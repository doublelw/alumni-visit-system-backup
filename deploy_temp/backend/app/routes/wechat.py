"""
微信H5页面 - API路由

支持老师和家长通过微信公众号H5页面访问
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta, date, time
from functools import wraps
import jwt
import re
from app import db
from app.models.user import User
from app.models.visit_application import VisitApplication

wechat_bp = Blueprint('wechat', __name__)

# JWT密钥（应该从config中读取）
JWT_SECRET_KEY = 'your-secret-key-change-in-production'
JWT_EXPIRATION_DAYS = 30  # 30天有效期


def generate_token(user_id, user_type):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'user_type': user_type,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')


def verify_token(token):
    """验证JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def wechat_auth_required(f):
    """微信认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未登录或登录已过期'}), 401

        token = auth_header.split(' ')[1]
        payload = verify_token(token)

        if not payload:
            return jsonify({'error': '登录已过期，请重新登录'}), 401

        # 将用户信息添加到request上下文
        request.current_user_id = payload['user_id']
        request.current_user_type = payload['user_type']

        return f(*args, **kwargs)

    return decorated_function


# ==================== 老师接口 ====================

@wechat_bp.route('/teacher/login', methods=['POST'])
def teacher_login():
    """
    老师登录（微信H5）

    请求体:
    {
        "phone": "13800138000",
        "password": "1234"  # 2-6位数字密码
    }

    返回:
    {
        "success": true,
        "data": {
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "teacher": {
                "id": 1,
                "name": "王老师",
                "phone": "13800138000"
            }
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()

        # 验证输入
        if not phone or len(phone) != 11:
            return jsonify({'error': '请输入正确的11位手机号'}), 400

        if not password or len(password) < 2 or len(password) > 6:
            return jsonify({'error': '请输入2-6位数字密码'}), 400

        # 查找老师用户
        teacher = User.query.filter(
            User.phone == phone,
            User.user_type.like('%teacher%')
        ).first()

        if not teacher:
            return jsonify({'error': '未找到该教师账号，请联系学校'}), 404

        # 验证密码
        if teacher.wechat_password != password:
            return jsonify({'error': '密码错误'}), 401

        # 生成token
        token = generate_token(teacher.id, 'teacher')

        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'teacher': {
                    'id': teacher.id,
                    'name': teacher.real_name,
                    'phone': teacher.phone
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"老师登录失败: {str(e)}")
        return jsonify({'error': '登录失败', 'details': str(e)}), 500


@wechat_bp.route('/teacher/check-code', methods=['POST'])
@wechat_auth_required
def teacher_check_code():
    """
    老师查询6位码（HMAC验证）

    请求体:
    {
        "code": "123456"
    }

    返回:
    {
        "success": true,
        "data": {
            "found": true,
            "type": "parent-visit",  # parent-visit 或 student-leave
            "application": {
                "phone": "13800138000",
                "parent_name": "张父",
                "student_name": "张小明",
                "class_name": "高一 1班"
            }
        }
    }
    """
    try:
        from app.utils.hmac_utils import verify_hmac_code, get_timestamp_info
        from app.models.user import User

        data = request.get_json()
        code = data.get('code', '').strip()

        current_app.logger.info(f"🔍 老师验证码: {code}")

        if not code or len(code) != 6:
            return jsonify({'error': '请输入6位审批码'}), 400

        # 验证HMAC码（24小时窗口）
        time_window_minutes = current_app.config['HMAC_TIME_WINDOW_TEACHER']

        # 检查所有用户，根据phone判断类型
        all_users = User.query.filter(
            User.user_type.in_(['parent', 'student', 'alumni']),
            User.status == 'active'
        ).all()

        current_app.logger.info(f"📊 找到 {len(all_users)} 个有效用户")

        matched_user = None
        matched_timestamp = None
        code_type = None

        for user in all_users:
            if not user.phone or not user.wechat_password:
                continue

            # 尝试纯phone（家长入校/校友入校）
            verification_parent = verify_hmac_code(
                code, user.phone, user.wechat_password, time_window_minutes
            )

            current_app.logger.info(f"  ✗ {user.phone} ({user.user_type}): {verification_parent['message']}")

            if verification_parent['valid']:
                matched_user = user
                matched_timestamp = verification_parent['timestamp']
                code_type = 'parent' if user.user_type in ['parent', 'alumni'] else 'student'
                current_app.logger.info(f"✅ 匹配成功: {user.phone} ({user.user_type}), 类型: {code_type}")
                break

            # 尝试phone+'STU'（学生请假）
            phone_stu = user.phone + 'STU'
            verification_student = verify_hmac_code(
                code, phone_stu, user.wechat_password, time_window_minutes
            )

            if verification_student['valid']:
                matched_user = user
                matched_timestamp = verification_student['timestamp']
                code_type = 'student-leave'
                current_app.logger.info(f"✅ 匹配成功: {phone_stu} (学生请假), 类型: {code_type}")
                break

        # 如果没有匹配到用户
        if not matched_user:
            current_app.logger.warning(f"❌ 未找到匹配的码: {code}")
            return jsonify({
                'success': True,
                'data': {
                    'found': False
                }
            })
            return jsonify({
                'success': True,
                'data': {
                    'found': False
                }
            })

        # 根据类型返回信息
        timestamp_info = get_timestamp_info(matched_timestamp)

        if code_type == 'parent':
            # 家长入校/校友入校
            if matched_user.user_type == 'alumni':
                # 校友入校 - 从alumni_profile获取毕业年份
                graduation_year = ''
                if matched_user.alumni_profile:
                    graduation_year = str(matched_user.alumni_profile.graduation_year)

                response_data = {
                    'success': True,
                    'data': {
                        'found': True,
                        'type': 'alumni-visit',
                        'application': {
                            'phone': matched_user.phone,
                            'alumni_name': matched_user.real_name,
                            'graduation_year': graduation_year,
                            'created_at': timestamp_info['formatted'],
                            'code_timestamp': matched_timestamp
                        }
                    }
                }
            else:
                # 家长入校
                student = User.query.get(matched_user.parent_student_id) if matched_user.parent_student_id else None

                response_data = {
                    'success': True,
                    'data': {
                        'found': True,
                        'type': 'parent-visit',
                        'application': {
                            'phone': matched_user.phone,
                            'parent_name': matched_user.real_name,
                            'created_at': timestamp_info['formatted'],
                            'code_timestamp': matched_timestamp
                        }
                    }
                }

                if student:
                    response_data['data']['application']['student_name'] = student.real_name
                    response_data['data']['application']['class_name'] = f"{student.grade}{student.class_id}" if student.grade and student.class_id else ''

            return jsonify(response_data)

        elif code_type == 'student-leave':
            # 学生请假
            student = matched_user
            parent = User.query.get(student.student_parent_id) if student.student_parent_id else None

            response_data = {
                'success': True,
                'data': {
                    'found': True,
                    'type': 'student-leave',
                    'application': {
                        'phone': student.phone,
                        'student_name': student.real_name,
                        'created_at': timestamp_info['formatted'],
                        'code_timestamp': matched_timestamp
                    }
                }
            }

            if parent:
                response_data['data']['application']['parent_name'] = parent.real_name
                response_data['data']['application']['parent_phone'] = parent.phone

            response_data['data']['application']['class_name'] = f"{student.grade}{student.class_id}" if student.grade and student.class_id else ''

            return jsonify(response_data)

        else:
            # 不应该到这里
            return jsonify({
                'success': True,
                'data': {
                    'found': False
                }
            })

    except Exception as e:
        current_app.logger.error(f"查询审批码失败: {str(e)}")
        return jsonify({'error': '查询失败', 'details': str(e)}), 500


@wechat_bp.route('/teacher/approve', methods=['POST'])
@wechat_auth_required
def teacher_approve():
    """
    老师审批6位码（HMAC验证 + 创建审批记录）

    简化流程：验证通过直接添加，不需要二次确认

    请求体:
    {
        "code": "123456",
        "action": "approve",
        "type": "parent-visit",  # parent-visit / student-leave / alumni-visit
        "phone": "13900002002",
        "approval_date": "2026-03-28"  # 可选
    }

    返回:
    {
        "success": true,
        "data": {
            "message": "审批成功"
        }
    }
    """
    try:
        from app.utils.hmac_utils import verify_hmac_code, get_timestamp_info
        from app.models.user import User
        from app import db

        data = request.get_json()
        code = data.get('code', '').strip()
        action = data.get('action', 'approve')
        approval_type = data.get('type', 'parent-visit')
        phone = data.get('phone', '').strip()
        approval_date_str = data.get('approval_date')

        current_app.logger.info(f"📝 审批请求: code={code}, type={approval_type}, phone={phone}")

        if not code:
            return jsonify({'error': '缺少审批码'}), 400

        if not phone:
            return jsonify({'error': '请输入手机号'}), 400

        # 获取老师ID（如果已认证，使用认证的用户ID；否则使用固定ID用于测试）
        teacher_id = getattr(request, 'current_user_id', 1)
        time_window_minutes = current_app.config['HMAC_TIME_WINDOW_TEACHER']

        # 根据类型查找用户并验证
        if approval_type == 'parent-visit':
            # 家长入校：查找家长或校友
            applicant = User.query.filter(
                User.phone == phone,
                User.user_type.in_(['parent', 'alumni']),
                User.status == 'active'
            ).first()

            if not applicant:
                current_app.logger.warning(f"❌ 未找到用户: {phone}")
                return jsonify({'error': '未找到该账号'}), 404

            # 验证HMAC码
            verification = verify_hmac_code(
                code, applicant.phone, applicant.wechat_password, time_window_minutes
            )

            if not verification['valid']:
                current_app.logger.warning(f"❌ HMAC验证失败: {verification['message']}")
                return jsonify({'error': verification['message']}), 400

            visit_purpose = '家长进校' if applicant.user_type == 'parent' else '校友进校'

        elif approval_type == 'alumni-visit':
            # 校友入校（新类型）
            applicant = User.query.filter_by(
                phone=phone,
                user_type='alumni',
                status='active'
            ).first()

            if not applicant:
                current_app.logger.warning(f"❌ 未找到校友: {phone}")
                return jsonify({'error': '未找到该校友账号'}), 404

            verification = verify_hmac_code(
                code, applicant.phone, applicant.wechat_password, time_window_minutes
            )

            if not verification['valid']:
                current_app.logger.warning(f"❌ HMAC验证失败: {verification['message']}")
                return jsonify({'error': verification['message']}), 400

            visit_purpose = '校友进校'

        elif approval_type == 'student-leave':
            # 学生请假：直接验证HMAC码（phone+STU）
            # 不依赖家长-学生关联关系
            phone_stu = phone + 'STU'

            # 查询所有用户，找到HMAC密码匹配的
            from app.models.user import User
            users = User.query.filter(
                User.phone.like(phone + '%'),
                User.status == 'active'
            ).all()

            matched_user = None
            for user in users:
                # 尝试用每个用户的密码验证HMAC
                verification = verify_hmac_code(
                    code, phone_stu, user.wechat_password, time_window_minutes
                )
                if verification['valid']:
                    matched_user = user
                    break

            if not matched_user:
                current_app.logger.warning(f"❌ 未找到用户或HMAC验证失败: {phone}")
                return jsonify({'error': '未找到该账号或验证码无效'}), 404

            current_app.logger.info(f"✅ 找到用户: {matched_user.real_name} ({matched_user.user_type})")

            # 使用找到的用户作为申请人
            applicant = matched_user
            visit_purpose = '学生出校'

        else:
            return jsonify({'error': '无效的申请类型'}), 400

        if action == 'approve':
            # 创建审批记录
            from datetime import datetime, date as dt_date, time
            from app.utils.hmac_utils import generate_hmac_code
            import random

            today = dt_date.today()

            # 处理审批日期
            if approval_date_str:
                visit_date = datetime.strptime(approval_date_str, '%Y-%m-%d').date()
            else:
                visit_date = today

            application = VisitApplication(
                applicant_id=applicant.id,
                visit_date=visit_date,  # 确保是date对象
                visit_time_start=time(8, 0),
                visit_time_end=time(20, 0),
                visit_purpose=visit_purpose,
                target_person=applicant.real_name,
                qr_code=code,
                application_status='approved',
                approved_by=teacher_id,
                approval_time=datetime.now(),
                approval_note=f"审批日期: {visit_date}"
            )

            db.session.add(application)
            db.session.commit()

            current_app.logger.info(f"✅ 审批成功: {applicant.real_name}, 目的: {visit_purpose}, 日期: {visit_date}")

            # 如果是学生请假，生成当天有效的出校验证码（基于学号+日期）
            exit_code = None
            if approval_type == 'student-leave':
                # 学生请假：找到家长关联的学生，用学生学号生成HMAC出校码
                # applicant是家长，需要找到关联的学生
                student = applicant.parent_students  # 这是一对一关系，返回单个User对象

                if not student:
                    current_app.logger.error(f"❌ 家长没有关联学生: {applicant.real_name}")
                    return jsonify({'error': '该家长没有关联学生，无法生成出校码'}), 400

                student_id = student.student_id

                if not student_id:
                    current_app.logger.error(f"❌ 学生没有学号: {student.real_name}")
                    return jsonify({'error': f'学生 {student.real_name} 没有学号，无法生成出校码'}), 400

                # 使用日期作为时间戳，生成当天唯一的6位HMAC码
                # timestamp: 日期的Unix时间戳（当天0点）
                from datetime import datetime
                visit_date_datetime = datetime.combine(visit_date, datetime.min.time())
                date_timestamp = int(visit_date_datetime.timestamp())

                # 生成HMAC码：学号 + 固定密钥 + 日期戳
                # 这样同一天内，同一个学号会生成相同的6位码
                exit_code = generate_hmac_code(student_id, 'STUDENT_EXIT', date_timestamp)

                current_app.logger.info(f"🎫 生成学生出校码: {exit_code} (学号: {student_id}, 学生: {student.real_name}, 日期戳: {date_timestamp})")

                # 将出校码保存到审批记录中
                application.access_code = exit_code
                db.session.commit()

                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'审批成功，允许在{visit_date}出校',
                        'exit_code': exit_code,  # 学生出校码
                        'exit_code_valid_date': visit_date.strftime('%Y-%m-%d'),
                        'applicant_name': applicant.real_name,
                        'student_name': student.real_name,  # 学生姓名
                        'student_id': student_id  # 学生学号
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'审批成功，允许在{visit_date}入校'
                    }
                })

        else:
            return jsonify({'error': '无效的操作'}), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"审批失败: {str(e)}")
        import traceback
        current_app.logger.error(f"详细错误: {traceback.format_exc()}")
        return jsonify({'error': '审批失败', 'details': str(e)}), 500


@wechat_bp.route('/teacher/special-approve', methods=['POST'])
@wechat_auth_required
def teacher_special_approve():
    """
    老师特批出校（紧急情况，联系不上家长时）

    请求体:
    {
        "student_name": "张三",
        "class_name": "高一1班",  # 或分开 grade/class_id
        "reason": "紧急情况，家长无法联系"
    }

    返回:
    {
        "success": true,
        "data": {
            "code": "123456",
            "message": "特批码已生成，请告知学生"
        }
    }
    """
    try:
        from app.utils.hmac_utils import generate_hmac_code

        data = request.get_json()
        student_name = data.get('student_name', '').strip()
        class_name = data.get('class_name', '').strip()
        grade = data.get('grade', '').strip()
        class_id = data.get('class_id', '').strip()
        reason = data.get('reason', '').strip()

        if not student_name:
            return jsonify({'error': '请输入学生姓名'}), 400

        if not (grade or class_name):
            return jsonify({'error': '请输入学生班级'}), 400

        if not reason:
            return jsonify({'error': '请填写特批原因'}), 400

        # 组合班级信息
        if not class_name:
            class_name = f"{grade}{class_id}"

        # 查找学生
        student = User.query.filter(
            User.real_name == student_name,
            User.user_type == 'student',
            User.status == 'active'
        ).first()

        if not student:
            return jsonify({'error': f'未找到学生：{student_name}'}), 404

        # 验证班级匹配（如果提供了具体的年级和班级）
        if grade and student.grade != grade:
            return jsonify({'error': f'学生年级不匹配，数据库中为：{student.grade}'}), 400

        if class_id and student.class_id != class_id:
            return jsonify({'error': f'学生班级不匹配，数据库中为：{student.class_id}'}), 400

        # 获取老师ID（从认证token中获取）
        teacher_id = request.current_user_id

        # 使用学生的phone和password生成HMAC码
        # 注意：特批码使用学生凭证生成，与家长码算法一致
        if not student.phone or not student.wechat_password:
            return jsonify({'error': '该学生账号信息不完整，无法生成特批码'}), 400

        code = generate_hmac_code(student.phone, student.wechat_password)

        # 创建特批审批记录（高亮标记）
        today = datetime.now().date()
        application = VisitApplication(
            applicant_id=student.id,  # 申请人是学生
            visit_date=today,
            visit_time_start=time(8, 0),
            visit_time_end=time(20, 0),
            visit_purpose='学生出校（特批）',
            target_person=student.real_name,
            qr_code=code,
            application_status='approved',
            approved_by=teacher_id,
            approval_time=datetime.now(),
            approval_note=f"班主任特批・无家长确认\n原因：{reason}",
            is_special_approval=True,  # 特批标记
            special_approval_reason=reason  # 特批原因
        )

        db.session.add(application)
        db.session.commit()

        current_app.logger.warning(
            f"老师{teacher_id}发起特批：学生{student_name}（{class_name}），原因：{reason}"
        )

        return jsonify({
            'success': True,
            'data': {
                'code': code,
                'message': f'特批码已生成：{code}，请告知学生。此码已高亮标记为「班主任特批」'
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"特批失败: {str(e)}")
        return jsonify({'error': '特批失败', 'details': str(e)}), 500


@wechat_bp.route('/teacher/statistics', methods=['GET'])
@wechat_auth_required
def teacher_statistics():
    """
    老师获取今日统计

    返回:
    {
        "success": true,
        "data": {
            "pending": 5,
            "approved_today": 10
        }
    }
    """
    try:
        from datetime import datetime as dt, timedelta
        from sqlalchemy import func

        today = dt.now().date()
        today_start = dt.combine(today, dt.min.time())

        # 待审批数量
        pending_count = VisitApplication.query.filter_by(application_status='pending').count()

        # 今日已批准数量
        approved_today = VisitApplication.query.filter(
            VisitApplication.application_status == 'approved',
            VisitApplication.approval_time >= today_start
        ).count()

        return jsonify({
            'success': True,
            'data': {
                'pending': pending_count,
                'approved_today': approved_today
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取统计失败: {str(e)}")
        import traceback
        current_app.logger.error(f"详细错误: {traceback.format_exc()}")
        return jsonify({'error': '获取统计失败', 'details': str(e)}), 500


# ==================== 家长接口 ====================

@wechat_bp.route('/parent/login', methods=['POST'])
def parent_login():
    """
    家长登录（微信H5）

    请求体:
    {
        "phone": "13800138000",
        "password": "88"  # 2-6位数字密码
    }

    返回:
    {
        "success": true,
        "data": {
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "parent": {
                "id": 1,
                "name": "张父",
                "phone": "13800138000"
            }
        }
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()

        # 验证输入
        if not phone or len(phone) != 11:
            return jsonify({'error': '请输入正确的11位手机号'}), 400

        if not password or len(password) < 2 or len(password) > 6:
            return jsonify({'error': '请输入2-6位数字密码'}), 400

        # 查找家长用户
        parent = User.query.filter(
            User.phone == phone,
            User.user_type.like('%parent%')
        ).first()

        if not parent:
            return jsonify({'error': '未找到该家长账号，请联系学校'}), 404

        # 验证密码
        if parent.wechat_password != password:
            return jsonify({'error': '密码错误'}), 401

        # 生成token
        token = generate_token(parent.id, 'parent')

        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'parent': {
                    'id': parent.id,
                    'name': parent.real_name,
                    'phone': parent.phone
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"家长登录失败: {str(e)}")
        return jsonify({'error': '登录失败', 'details': str(e)}), 500


@wechat_bp.route('/parent/get-children', methods=['GET'])
@wechat_auth_required
def parent_get_children():
    """
    获取家长关联的学生信息

    返回:
    {
        "success": true,
        "data": {
            "children": [
                {
                    "id": 1,
                    "name": "张小明",
                    "student_id": "2021001",
                    "class_name": "高一1班",
                    "grade": "高一"
                }
            ]
        }
    }
    """
    try:
        parent_id = request.current_user_id

        # 查找关联的学生（通过student_parent_id字段）
        students = User.query.filter(
            User.student_parent_id == parent_id
        ).all()

        children_list = []
        for student in students:
            children_list.append({
                'id': student.id,
                'name': student.real_name,
                'student_id': student.student_id or '',
                'class_name': f"{student.grade} {student.class_id}" if student.grade and student.class_id else '',
                'grade': student.grade or ''
            })

        return jsonify({
            'success': True,
            'data': {
                'children': children_list
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取学生信息失败: {str(e)}")
        return jsonify({'error': '获取学生信息失败', 'details': str(e)}), 500


@wechat_bp.route('/parent/generate-visit-code', methods=['POST'])
@wechat_auth_required
def parent_generate_visit_code():
    """
    家长生成进校6位码

    请求体:
    {
        "student_id": 1,
        "visit_date": "2025-03-27",
        "visit_purpose": "家长进校",
        "companion_count": 0,
        "companions": []
    }

    返回:
    {
        "success": true,
        "data": {
            "code": "123456"
        }
    }
    """
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        visit_date = data.get('visit_date')
        visit_purpose = data.get('visit_purpose', '家长进校')
        companion_count = data.get('companion_count', 0)
        companions = data.get('companions', [])

        # 验证输入
        if not student_id:
            return jsonify({'error': '请选择学生'}), 400

        if not visit_date:
            return jsonify({'error': '请选择访问日期'}), 400

        # 转换日期字符串为date对象
        try:
            from datetime import datetime
            visit_date_obj = datetime.strptime(visit_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '日期格式错误'}), 400

        parent_id = request.current_user_id
        parent = User.query.get(parent_id)

        if not parent:
            return jsonify({'error': '未找到家长信息'}), 404

        # 验证学生是否属于该家长
        student = User.query.get(student_id)
        if not student or student.student_parent_id != parent_id:
            return jsonify({'error': '未找到该学生或学生不属于您'}), 404

        # 生成6位码
        import random
        code = str(random.randint(100000, 999999))

        # 检查码是否已存在
        existing = VisitApplication.query.filter_by(qr_code=code).first()
        if existing:
            # 重新生成
            code = str(random.randint(100000, 999999))

        # 创建访问申请
        application = VisitApplication(
            applicant_id=parent_id,
            visit_date=visit_date_obj,
            visit_time_start=time(8, 0),
            visit_time_end=time(20, 0),
            visit_purpose=visit_purpose,
            target_person=f"{student.real_name}家长",
            qr_code=code,
            application_status='pending'
        )

        db.session.add(application)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'code': code
            }
        })

    except Exception as e:
        current_app.logger.error(f"家长生成6位码失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '生成失败', 'details': str(e)}), 500


@wechat_bp.route('/teacher/create-student-code', methods=['POST'])
@wechat_auth_required
def teacher_create_student_code():
    """
    老师代学生申请入校，生成6位码

    请求体:
    {
        "student_name": "张小明",
        "student_id": "2021001",
        "visit_purpose": "return",
        "note": "放学后返校取练习册"
    }

    返回:
    {
        "success": true,
        "data": {
            "code": "123456"
        }
    }
    """
    try:
        data = request.get_json()
        student_name = data.get('student_name', '').strip()
        student_id = data.get('student_id', '').strip()
        visit_purpose = data.get('visit_purpose', 'return')
        note = data.get('note', '').strip()

        # 验证输入
        if not student_name:
            return jsonify({'error': '请输入学生姓名'}), 400

        # 获取老师信息（从认证token中获取）
        teacher_id = request.current_user_id
        teacher = User.query.get(teacher_id)

        if not teacher:
            return jsonify({'error': '未找到老师信息'}), 404

        # 访问目的映射
        purpose_map = {
            'return': '返校取物',
            'parent-visit': '家长来校接学生',
            'emergency': '紧急事务',
            'other': '其他'
        }

        # 生成6位码
        from datetime import datetime as dt_datetime
        from app.utils.hmac_utils import generate_hmac_code

        today = datetime.now().date()

        # 如果提供了学号，使用HMAC生成（基于学号+日期）
        if student_id:
            # 使用日期作为时间戳
            today_datetime = dt_datetime.combine(today, dt_datetime.min.time())
            date_timestamp = int(today_datetime.timestamp())

            # 生成HMAC码：学号 + 固定密钥 + 日期戳
            # 这样同一天内，同一个学号会生成相同的6位码
            code = generate_hmac_code(student_id, 'STUDENT_EXIT', date_timestamp)

            current_app.logger.info(f"🎫 老师代申请：使用学号生成HMAC码: {code} (学号: {student_id}, 日期戳: {date_timestamp})")
        else:
            # 没有学号，使用随机码（原有逻辑）
            import random
            code = str(random.randint(100000, 999999))

            # 检查码是否已存在
            existing = VisitApplication.query.filter_by(qr_code=code).first()
            if existing:
                # 重新生成
                code = str(random.randint(100000, 999999))

            current_app.logger.info(f"🎫 老师代申请：使用随机码: {code}")

        # 创建访问申请
        application = VisitApplication(
            applicant_id=teacher_id,  # 老师作为申请人
            visit_date=today,
            visit_time_start=time(8, 0),
            visit_time_end=time(20, 0),
            visit_purpose=purpose_map.get(visit_purpose, '其他'),
            target_person=f"{student_name} (老师代申请)",
            qr_code=code,
            application_status='approved',  # 直接批准
            approved_by=teacher_id,
            approval_time=datetime.now(),
            access_code=code  # 保存到access_code字段（用于验证）
        )

        db.session.add(application)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'code': code,
                'code_type': 'hmac' if student_id else 'random'
            }
        })

    except Exception as e:
        current_app.logger.error(f"老师代学生申请失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '生成失败', 'details': str(e)}), 500


@wechat_bp.route('/teacher/add-visitor', methods=['POST'])
@wechat_auth_required
def teacher_add_visitor():
    """
    老师添加访客（从访客发送的信息中创建访客账号和访问记录）

    请求体:
    {
        "name": "张三",
        "phone": "13800138000",
        "id_card": "110101199001011234",
        "visit_purpose": "meeting",
        "visit_reason": "商务洽谈",
        "access_code": "123456"
    }

    返回:
    {
        "success": true,
        "data": {
            "visitor": {
                "name": "张三",
                "phone": "13800138000"
            },
            "access_code": "123456"
        }
    }
    """
    try:
        from app.models.user import User
        from app.models.visit_application import VisitApplication

        data = request.get_json()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        id_card = data.get('id_card', '').strip()
        visit_purpose = data.get('visit_purpose', 'other')
        visit_reason = data.get('visit_reason', '').strip()
        access_code = data.get('access_code', '').strip()
        access_password = data.get('access_password', '').strip()

        current_app.logger.info(f"📝 老师添加访客: {name} ({phone})")

        # 验证输入
        if not name:
            return jsonify({'error': '请输入访客姓名'}), 400

        if not phone:
            return jsonify({'error': '请输入访客手机号'}), 400

        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'error': '手机号格式不正确'}), 400

        if not access_code:
            return jsonify({'error': '缺少访客码'}), 400

        if not re.match(r'^\d{6}$', access_code):
            return jsonify({'error': '访客码格式不正确，必须是6位数字'}), 400

        # 检查访客是否已存在
        existing_visitor = User.query.filter_by(phone=phone).first()
        if existing_visitor:
            current_app.logger.info(f"  ℹ️ 访客已存在: {existing_visitor.real_name}")

            # 创建访问记录（使用已存在的访客）
            application = VisitApplication(
                applicant_id=existing_visitor.id,
                visit_date=datetime.now().date(),
                visit_time_start=time(8, 0),
                visit_time_end=time(20, 0),
                visit_purpose=visit_purpose,
                target_person=name,
                qr_code=access_code,
                application_status='approved',
                approved_by=request.current_user_id,
                approval_time=datetime.now(),
                access_code=access_code,
                approval_note=visit_reason
            )

            db.session.add(application)
            db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'visitor': {
                        'name': existing_visitor.real_name,
                        'phone': existing_visitor.phone
                    },
                    'access_code': access_code,
                    'message': '访客已存在，已创建访问记录'
                }
            })

        # 访客不存在，创建新访客账号
        # 查找最大用户ID
        max_user = User.query.order_by(User.id.desc()).first()
        new_id = (max_user.id + 1) if max_user else 1

        # 生成默认密码（手机号后6位）
        default_password = phone[-6:] if len(phone) >= 6 else phone

        # 创建访客账号
        visitor = User(
            id=new_id,
            real_name=name,
            phone=phone,
            id_card=id_card if id_card else None,
            user_type='visitor',
            status='active',
            wechat_password=default_password,
            organization_id=1  # 默认组织
        )

        db.session.add(visitor)
        db.session.flush()  # 获取visitor.id

        current_app.logger.info(f"  ✅ 创建访客账号: ID={visitor.id}, 姓名={name}")

        # 创建访问申请记录
        application = VisitApplication(
            applicant_id=visitor.id,
            visit_date=datetime.now().date(),
            visit_time_start=time(8, 0),
            visit_time_end=time(20, 0),
            visit_purpose=visit_purpose,
            target_person=name,
            qr_code=access_code,
            application_status='approved',
            approved_by=request.current_user_id,
            approval_time=datetime.now(),
            access_code=access_code,
            approval_note=visit_reason
        )

        db.session.add(application)
        db.session.flush()  # 获取application.id

        # 创建访客档案并保存访问密码
        from app.models.visitor_profile import VisitorProfile
        visitor_profile = VisitorProfile(
            user_id=visitor.id,
            real_name=name,
            id_card=id_card if id_card else '',
            phone=phone,
            visitor_type='individual',
            visit_purpose=visit_purpose,
            access_code=access_code,
            access_password=access_password,
            application_status='approved',
            approved_by=request.current_user_id,
            approved_at=datetime.now()
        )

        db.session.add(visitor_profile)
        db.session.commit()

        current_app.logger.info(f"  ✅ 访客添加成功: 访客码={access_code}")

        return jsonify({
            'success': True,
            'data': {
                'visitor': {
                    'name': visitor.real_name,
                    'phone': visitor.phone
                },
                'access_code': access_code,
                'message': '访客添加成功'
            }
        })

    except Exception as e:
        current_app.logger.error(f"添加访客失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '添加失败', 'details': str(e)}), 500


@wechat_bp.route('/visitor/verify', methods=['POST'])
def visitor_verify():
    """
    访客验证API

    访客输入手机号和密码，系统验证并返回访客信息和访问码

    请求体:
    {
        "phone": "13800138000",
        "password": "12",
        "access_code": "123456"  # 基于手机号和密码生成的访问码
    }

    返回:
    {
        "success": true,
        "data": {
            "name": "张三",
            "visit_purpose": "商务会议",
            "status": "有效"
        }
    }
    """
    try:
        from app.models.visitor_profile import VisitorProfile
        from app.models.user import User

        data = request.get_json()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()
        access_code = data.get('access_code', '').strip()

        current_app.logger.info(f"🔍 访客验证: {phone}")

        # 验证输入
        if not phone:
            return jsonify({'error': '请输入手机号'}), 400

        if not password:
            return jsonify({'error': '请输入访问密码'}), 400

        if not access_code:
            return jsonify({'error': '请提供访问码'}), 400

        # 查找访客档案
        visitor_profile = VisitorProfile.query.filter_by(
            phone=phone,
            access_password=password
        ).first()

        if not visitor_profile:
            current_app.logger.warning(f"  ❌ 访客不存在或密码错误: {phone}")
            return jsonify({'error': '手机号或密码错误'}), 404

        # 检查访问是否有效
        is_valid, message = visitor_profile.is_valid_visit()
        if not is_valid:
            current_app.logger.warning(f"  ❌ 访问无效: {visitor_profile.real_name} - {message}")
            return jsonify({'error': message}), 403

        # 更新访客档案的访问码（使用新生成的）
        visitor_profile.access_code = access_code
        db.session.commit()

        current_app.logger.info(f"  ✅ 访客验证成功: {visitor_profile.real_name}")

        return jsonify({
            'success': True,
            'data': {
                'name': visitor_profile.real_name,
                'visit_purpose': visitor_profile.visit_purpose,
                'status': visitor_profile.get_status_label(),
                'access_code': access_code
            }
        })

    except Exception as e:
        current_app.logger.error(f"访客验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': '验证失败'}), 500


# ============================================================
# 外网/内网分离架构 - 访客管理（新架构）
# ============================================================

@wechat_bp.route('/teacher/add-visitor-v2', methods=['POST'])
@wechat_auth_required
def teacher_add_visitor_v2():
    """
    老师添加访客（外网/内网分离架构 V2）

    新架构：外网/内网分离
    - 外网：只存储访客码+手机号（模拟腾讯云托管）
    - 内网：存储完整的访客信息和访问记录

    流程：
    1. 老师输入访客码
    2. 从外网获取访客基本信息（手机号）
    3. 老师补充详细信息（姓名、身份证等）
    4. 在内网创建完整的访客账号
    5. 标记外网码已使用

    请求体:
    {
        "access_code": "123456",  # 访客码（必填）
        "name": "张三",            # 姓名（必填）
        "id_card": "110101...",    # 身份证（可选）
        "visit_purpose": "meeting", # 访问目的（可选）
        "visit_reason": "商务洽谈"  # 访问说明（可选）
    }

    返回:
    {
        "success": true,
        "data": {
            "visitor": {
                "name": "张三",
                "phone": "13800138000"
            },
            "access_code": "123456",
            "message": "访客添加成功"
        }
    }
    """
    try:
        from app.models.user import User
        from app.models.visit_application import VisitApplication
        import requests

        data = request.get_json()
        access_code = data.get('access_code', '').strip()
        name = data.get('name', '').strip()
        id_card = data.get('id_card', '').strip()
        visit_purpose = data.get('visit_purpose', 'other')
        visit_reason = data.get('visit_reason', '').strip()

        current_app.logger.info(f"📝 老师验证访客码: {access_code}")

        # 验证访问码格式
        if not access_code:
            return jsonify({'error': '缺少访客码'}), 400

        if not re.match(r'^\d{6}$', access_code):
            return jsonify({'error': '访客码格式不正确，必须是6位数字'}), 400

        # 从外网获取访客基本信息
        try:
            external_url = f"http://localhost:5000/external/visitor/info/{access_code}"
            current_app.logger.info(f"  🔍 从外网查询访客信息: {external_url}")

            response = requests.get(external_url, timeout=5)
            external_data = response.json()

            if not external_data.get('exists'):
                current_app.logger.warning(f"  ❌ 外网中不存在此访客码: {access_code}")
                return jsonify({
                    'error': '访客码无效或已过期',
                    'details': '请确认访客已在系统中登记，且访客码在24小时有效期内'
                }), 404

            visitor_basic_info = external_data.get('visitor_info', {})
            phone = visitor_basic_info.get('phone', '')

            if not phone:
                current_app.logger.error(f"  ❌ 外网数据异常：缺少手机号")
                return jsonify({'error': '外网数据异常：缺少手机号'}), 500

            current_app.logger.info(f"  ✅ 从外网获取到手机号: {phone}")

        except requests.RequestException as e:
            current_app.logger.error(f"  ❌ 外网请求失败: {e}")
            return jsonify({
                'error': '无法连接到外网服务',
                'details': '请检查网络连接或稍后重试'
            }), 503
        except Exception as e:
            current_app.logger.error(f"  ❌ 外网查询异常: {e}")
            return jsonify({
                'error': '外网查询失败',
                'details': str(e)
            }), 500

        # 验证老师输入的详细信息
        if not name:
            return jsonify({'error': '请输入访客姓名'}), 400

        # 手机号格式验证（外网已验证，这里再次确认）
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'error': f'手机号格式不正确: {phone}'}), 400

        # 检查内网是否已有此访客
        existing_visitor = User.query.filter_by(phone=phone).first()
        if existing_visitor:
            current_app.logger.info(f"  ℹ️ 内网中访客已存在: {existing_visitor.real_name}")

            # 创建新的访问记录
            application = VisitApplication(
                applicant_id=existing_visitor.id,
                visit_date=datetime.now().date(),
                visit_time_start=time(8, 0),
                visit_time_end=time(20, 0),
                visit_purpose=visit_purpose,
                target_person=name,
                qr_code=access_code,
                application_status='approved',
                approved_by=request.current_user_id,
                approval_time=datetime.now(),
                access_code=access_code,
                approval_note=visit_reason
            )

            db.session.add(application)
            db.session.commit()

            # 标记外网码已使用
            try:
                requests.post(f"http://localhost:5000/external/visitor/mark-used",
                            json={'code': access_code}, timeout=5)
                current_app.logger.info(f"  ✅ 已标记外网码使用")
            except:
                pass  # 标记失败不影响主流程

            return jsonify({
                'success': True,
                'data': {
                    'visitor': {
                        'name': existing_visitor.real_name,
                        'phone': existing_visitor.phone
                    },
                    'access_code': access_code,
                    'message': '访客已存在，已创建新的访问记录'
                }
            })

        # 在内网创建新访客账号
        max_user = User.query.order_by(User.id.desc()).first()
        new_id = (max_user.id + 1) if max_user else 1

        # 生成默认密码（手机号后6位）
        default_password = phone[-6:] if len(phone) >= 6 else phone

        # 生成用户名（使用手机号）
        username = f"visitor_{phone}"

        # 生成密码哈希（使用默认密码）
        import bcrypt
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(default_password.encode('utf-8'), salt).decode('utf-8')

        # 创建访客账号（内网存储完整信息）
        # 注意：User模型没有id_card字段，身份证信息存储在notes中
        visitor = User(
            id=new_id,
            username=username,
            password_hash=password_hash,
            real_name=name,
            phone=phone,
            user_type='visitor',
            status='active',
            wechat_password=default_password,
            organization_id=1  # 默认组织
        )

        db.session.add(visitor)
        db.session.flush()

        current_app.logger.info(f"  ✅ 创建内网访客账号: ID={visitor.id}, 姓名={name}, 手机={phone}")

        # 创建访问申请记录
        application = VisitApplication(
            applicant_id=visitor.id,
            visit_date=datetime.now().date(),
            visit_time_start=time(8, 0),
            visit_time_end=time(20, 0),
            visit_purpose=visit_purpose,
            target_person=name,
            qr_code=access_code,
            application_status='approved',
            approved_by=request.current_user_id,
            approval_time=datetime.now(),
            access_code=access_code,
            approval_note=visit_reason  # 使用approval_note存储访问说明
        )

        db.session.add(application)
        db.session.commit()

        current_app.logger.info(f"  ✅ 内网访客添加成功: 访客码={access_code}")

        # 标记外网码已使用
        try:
            requests.post(f"http://localhost:5000/external/visitor/mark-used",
                        json={'code': access_code}, timeout=5)
            current_app.logger.info(f"  ✅ 已标记外网码使用，访客信息已从外网迁移到内网")
        except Exception as e:
            current_app.logger.warning(f"  ⚠️ 标记外网码使用失败: {e}（不影响主流程）")

        return jsonify({
            'success': True,
            'data': {
                'visitor': {
                    'name': visitor.real_name,
                    'phone': visitor.phone
                },
                'access_code': access_code,
                'message': f'访客添加成功（从外网迁移到内网）'
            }
        })

    except Exception as e:
        current_app.logger.error(f"添加访客失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': '添加失败',
            'details': str(e)
        }), 500


# ============================================================
# 家长端API（无需登录）
# ============================================================

# =====================================================================
# ⚠️ 已废弃：/parent/generate-code 路由（2026-03-28）
# =====================================================================
# 原因：根据新架构，parent-simple.html 应该是纯离线的，所有HMAC码都在前端生成
#      不需要调用后台API，也不需要查询数据库验证用户
#
# 新流程：
# 1. parent-simple.html 纯前端生成HMAC码（使用Web Crypto API）
# 2. 用户将生成的6位码发给老师审批（微信/钉钉等）
# 3. 老师审批后，系统生成新的入校码给用户
# 4. 用户到校门时，门卫验证入校码（查询VisitApplication表）
#
# 校友特殊流程：
# - 校友不需要老师审批，直接用前端生成的码到校门验证
# - 门卫验证时查询User表（user_type='alumni'）
#
# 旧代码保留作为参考，但路由已禁用
# =====================================================================

# @wechat_bp.route('/parent/generate-code', methods=['POST'])
# def parent_generate_code():
#     """
#     家长生成HMAC码（支持家长入校和学生请假）
#
#     请求体:
#     {
#         "phone": "13900002002" 或 "13900002002STU",
#         "password": "88"
#     }
#
#     说明:
#     - phone纯数字: 家长入校
#     - phone+STU后缀: 学生请假
#     """
#     from app.utils.hmac_utils import generate_hmac_code
#
#     try:
#         data = request.get_json()
#         phone = data.get('phone', '').strip()
#         password = data.get('password', '').strip()
#
#         current_app.logger.info(f"📱 生成码请求: phone={phone}, password={password}")
#
#         # 验证输入
#         if not phone:
#             return jsonify({'error': '请输入手机号'}), 400
#
#         if not password or len(password) < 2 or len(password) > 6:
#             return jsonify({'error': '请输入2-6位密码'}), 400
#
#         # 检查是否为学生请假（带STU后缀）
#         is_student_leave = phone.endswith('STU')
#
#         if is_student_leave:
#             # 学生请假：去掉STU后缀，查找家长
#             parent_phone = phone[:-3]  # 去掉STU
#             current_app.logger.info(f"🎓 学生请假模式: parent_phone={parent_phone}")
#
#             parent = User.query.filter_by(
#                 phone=parent_phone,
#                 user_type='parent',
#                 status='active'
#             ).first()
#
#             if not parent:
#                 current_app.logger.warning(f"❌ 未找到家长: {parent_phone}")
#                 return jsonify({'error': '未找到该家长账号'}), 404
#
#             # 验证密码
#             if parent.wechat_password != password:
#                 current_app.logger.warning(f"❌ 密码错误: {password} != {parent.wechat_password}")
#                 return jsonify({'error': '密码错误'}), 401
#
#             # 用家长phone+STU生成码
#             code = generate_hmac_code(phone, password)
#             current_app.logger.info(f"✅ 学生请假码生成成功: {code}")
#
#         else:
#             # 入校申请：查找家长或校友
#             current_app.logger.info(f"🏫 入校申请模式: phone={phone}")
#
#             user = User.query.filter(
#                 User.phone == phone,
#                 User.user_type.in_(['parent', 'alumni']),
#                 User.status == 'active'
#             ).first()
#
#             if not user:
#                 current_app.logger.warning(f"❌ 未找到账号: {phone}")
#                 return jsonify({'error': '未找到该账号'}), 404
#
#             current_app.logger.info(f"✅ 找到用户: {user.real_name} ({user.user_type})")
#
#             # 验证密码
#             if user.wechat_password != password:
#                 current_app.logger.warning(f"❌ 密码错误: {password} != {user.wechat_password}")
#                 return jsonify({'error': '密码错误'}), 401
#
#             # 用纯phone生成码
#             code = generate_hmac_code(phone, password)
#             current_app.logger.info(f"✅ 入校申请码生成成功: {code} (用户: {user.real_name}, 类型: {user.user_type})")
#
#         return jsonify({
#             'success': True,
#             'data': {
#                 'code': code
#             }
#         })
#
#     except Exception as e:
#         current_app.logger.error(f"生成码失败: {str(e)}")
#         return jsonify({'error': '生成失败', 'details': str(e)}), 500


@wechat_bp.route('/parent/get-student-info', methods=['POST'])
def parent_get_student_info():
    """
    获取家长关联的学生信息
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()

        # 验证输入
        if not phone or len(phone) != 11:
            return jsonify({'error': '请输入正确的11位手机号'}), 400

        if not password:
            return jsonify({'error': '请输入密码'}), 400

        # 查找家长用户
        parent = User.query.filter_by(
            phone=phone,
            user_type='parent',
            status='active'
        ).first()

        if not parent:
            return jsonify({'error': '未找到该家长账号'}), 404

        # 验证密码
        if parent.wechat_password != password:
            return jsonify({'error': '密码错误'}), 401

        # 获取关联的学生信息
        student = None
        if parent.parent_student_id:
            student = User.query.get(parent.parent_student_id)

        return jsonify({
            'success': True,
            'data': {
                'parent': {
                    'name': parent.real_name,
                    'phone': parent.phone
                },
                'student': {
                    'name': student.real_name if student else None,
                    'grade': student.grade if student else None,
                    'class_id': student.class_id if student else None
                } if student else None
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取学生信息失败: {str(e)}")
        return jsonify({'error': '获取失败', 'details': str(e)}), 500
