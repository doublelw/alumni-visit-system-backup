"""
电子校友卡 - API路由

提供动态申请码、访客申请、审批等功能
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from functools import wraps
import base64

from app import db
from app.models.user import User
from app.services.electronic_card_service import ElectronicCardService

electronic_card_bp = Blueprint('electronic_card', __name__)


def token_required(f):
    """JWT token验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': '缺少认证令牌'}), 401

        token = token[7:]
        try:
            from app.routes.auth import verify_token
            payload = verify_token(token)
            if payload is None:
                return jsonify({'error': '无效的令牌'}), 401
            request.current_user_id = payload['user_id']
        except Exception as e:
            current_app.logger.error(f"Token验证失败: {str(e)}")
            return jsonify({'error': '令牌验证失败'}), 401

        return f(*args, **kwargs)
    return decorated_function


# ==================== 动态申请码（校内人员）====================

@electronic_card_bp.route('/application/generate', methods=['POST'])
def generate_application_code():
    """
    生成动态申请码（校内人员）

    请求体:
    {
        "student_id": "2021001",  # 学号或身份证号
        "pin_code": "88"  # 2位个人密码
    }

    返回:
    {
        "success": true,
        "data": {
            "code": "123456",
            "expires_at": "2026-03-27 12:05:00",
            "user_info": {
                "name": "张三",
                "student_no": "2021001",
                "class_name": "高一(3)班",
                "type": "student",
                "photo_url": "/static/photos/..."
            }
        }
    }
    """
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        pin_code = data.get('pin_code')

        # 验证参数
        if not student_id:
            return jsonify({'error': '学号不能为空'}), 400
        if not pin_code or len(pin_code) != 2:
            return jsonify({'error': '请输入2位数字密码'}), 400

        # 根据学号或身份证号查找用户
        # 先尝试在User表中查找student_id
        user = User.query.filter(User.student_id == student_id).first()

        # 如果找不到，尝试在AlumniProfile中查找id_card
        if not user:
            from app.models.alumni_profile import AlumniProfile
            profile = AlumniProfile.query.filter(AlumniProfile.id_card == student_id).first()
            if profile:
                user = User.query.get(profile.user_id)

        if not user:
            return jsonify({'error': '用户不存在，请检查学号或身份证号'}), 404

        # 检查用户状态
        if user.status != 'active':
            return jsonify({'error': '用户状态异常，无法生成申请码'}), 403

        # 确定用户类型
        user_type = 'student' if 'student' in user.user_type else 'alumni'

        # 生成动态申请码（2分钟有效）
        result = ElectronicCardService.generate_application_code(
            user_id=user.id,
            user_type=user_type,
            pin_code=pin_code,
            validity_minutes=2  # 2分钟有效期
        )

        return jsonify({
            'success': True,
            'data': {
                'code': result['code'],
                'expires_at': result['expires_at'],
                'validity_period': result['validity_period'],
                'user_info': {
                    'name': user.real_name,
                    'type': user_type,
                    'student_id': user.student_id,
                    'employee_id': user.employee_id,
                    'grade': user.grade,
                    'class_id': user.class_name,
                    'phone': user.phone
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"生成申请码失败: {str(e)}")
        return jsonify({'error': '生成申请码失败', 'details': str(e)}), 500


@electronic_card_bp.route('/application/verify', methods=['POST'])
def verify_application_code():
    """
    验证动态申请码（门卫使用）

    请求体:
    {
        "code": "123456",
        "student_id": "2021001",  # 学号或身份证号
        "pin_code": "88"  # 2位个人密码
    }

    返回:
    {
        "success": true,
        "data": {
            "valid": true,
            "message": "验证成功",
            "user_info": {...}
        }
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        student_id = data.get('student_id')
        pin_code = data.get('pin_code')

        # 验证参数
        if not code or len(code) != 6:
            return jsonify({'error': '申请码必须是6位数字'}), 400

        if not student_id or not pin_code:
            return jsonify({'error': '缺少学号或密码'}), 400

        # 根据学号或身份证号查找用户
        user = User.query.filter(User.student_id == student_id).first()

        # 如果找不到，尝试在AlumniProfile中查找id_card
        if not user:
            from app.models.alumni_profile import AlumniProfile
            profile = AlumniProfile.query.filter(AlumniProfile.id_card == student_id).first()
            if profile:
                user = User.query.get(profile.user_id)

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 确定用户类型
        user_type = 'student' if 'student' in user.user_type else 'alumni'

        # 验证申请码
        is_valid, message = ElectronicCardService.verify_application_code(
            code=code,
            user_id=user.id,
            user_type=user_type,
            pin_code=pin_code
        )

        # 记录验证日志
        from app.models.verification_log import VerificationLog
        log = VerificationLog(
            code_type='application',
            code=code,
            personnel_id=user.id,
            verification_result=is_valid,
            verified_by=data.get('guard_name', 'unknown'),
            user_name=user.real_name if is_valid else None
        )
        db.session.add(log)
        db.session.commit()

        if is_valid:
            return jsonify({
                'success': True,
                'data': {
                    'valid': True,
                    'message': message,
                    'user_info': {
                        'name': user.real_name,
                        'type': user_type,
                        'student_no': user.student_no,
                        'employee_no': user.employee_no,
                        'grade': user.grade,
                        'class_name': user.class_name,
                        'department': user.department,
                        'photo_url': user.photo_url
                    }
                }
            })
        else:
            return jsonify({
                'success': False,
                'data': {
                    'valid': False,
                    'message': message
                }
            })

    except Exception as e:
        current_app.logger.error(f"验证申请码失败: {str(e)}")
        return jsonify({'error': '验证申请码失败', 'details': str(e)}), 500


# ==================== 访客申请（校外人员）====================

@electronic_card_bp.route('/visitor/apply', methods=['POST'])
def visitor_apply():
    """
    访客申请

    请求体:
    {
        "visitor_name": "张三",
        "id_card": "110101199001011234",
        "phone": "13800138000",
        "visit_reason": "探望学生",
        "host_name": "李老师",
        "photo_data": "base64_encoded_photo"  # 可选
    }

    返回:
    {
        "success": true,
        "data": {
            "application_id": 456,
            "status": "pending",
            "message": "申请已提交，等待审核"
        }
    }
    """
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['visitor_name', 'id_card', 'phone', 'visit_reason', 'host_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        # 创建访客申请
        from app.models.visitor_application import VisitorApplication

        application = VisitorApplication(
            visitor_name=data['visitor_name'].strip(),
            id_card=data['id_card'].strip(),
            phone=data['phone'].strip(),
            visit_reason=data['visit_reason'].strip(),
            host_name=data['host_name'].strip(),
            photo_data=data.get('photo_data'),  # Base64照片
            status='pending'
        )

        # 如果指定了接待人ID，记录下来
        if data.get('host_id'):
            application.host_id = data['host_id']

        db.session.add(application)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'application_id': application.id,
                'status': 'pending',
                'message': '申请已提交，等待审核'
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"访客申请失败: {str(e)}")
        return jsonify({'error': '访客申请失败', 'details': str(e)}), 500


@electronic_card_bp.route('/visitor/status/<int:application_id>', methods=['GET'])
def get_visitor_status(application_id):
    """
    查询访客申请状态

    参数:
        application_id: 申请ID

    返回:
    {
        "success": true,
        "data": {
            "status": "approved",
            "access_code": "654321",
            "expires_at": "2026-03-27 23:59:59"
        }
    }
    """
    try:
        from app.models.visitor_application import VisitorApplication

        application = VisitorApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '申请不存在'}), 404

        result = {
            'application_id': application.id,
            'status': application.status
        }

        if application.status == 'approved':
            result['access_code'] = application.access_code
            result['expires_at'] = application.code_expires_at.strftime('%Y-%m-%d %H:%M:%S')
            result['message'] = '申请已通过'
        elif application.status == 'rejected':
            result['message'] = '申请已被拒绝'
            if application.rejection_reason:
                result['rejection_reason'] = application.rejection_reason
        else:
            result['message'] = '等待审核中'

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        current_app.logger.error(f"查询访客状态失败: {str(e)}")
        return jsonify({'error': '查询访客状态失败', 'details': str(e)}), 500


# ==================== 教师管理端（审批）====================

@electronic_card_bp.route('/admin/visitor/pending', methods=['GET'])
@token_required
def get_pending_applications():
    """
    获取待审批的访客申请列表（教师使用）

    返回:
    {
        "success": true,
        "data": {
            "applications": [...]
        }
    }
    """
    try:
        from app.models.visitor_application import VisitorApplication

        applications = VisitorApplication.query.filter_by(
            status='pending'
        ).order_by(VisitorApplication.created_at.desc()).all()

        result = []
        for app in applications:
            result.append({
                'id': app.id,
                'visitor_name': app.visitor_name,
                'id_card_last4': app.id_card[-4:] if app.id_card else None,
                'visit_reason': app.visit_reason,
                'host_name': app.host_name,
                'photo_url': app.get_photo_url(),
                'created_at': app.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify({
            'success': True,
            'data': {
                'applications': result
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取待审批列表失败: {str(e)}")
        return jsonify({'error': '获取待审批列表失败', 'details': str(e)}), 500


@electronic_card_bp.route('/admin/visitor/approve/<int:application_id>', methods=['POST'])
@token_required
def approve_visitor_application(application_id):
    """
    审批访客申请（教师使用）

    请求体:
    {
        "action": "approve",  # approve/reject
        "rejection_reason": "理由不充分"  # 拒绝时必填
    }

    返回:
    {
        "success": true,
        "data": {
            "access_code": "654321",  # 通过时返回
            "expires_at": "2026-03-27 23:59:59"
        }
    }
    """
    try:
        from app.models.visitor_application import VisitorApplication

        data = request.get_json()
        action = data.get('action', 'approve')

        application = VisitorApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '申请不存在'}), 404

        if application.status != 'pending':
            return jsonify({'error': '申请已被处理'}), 400

        if action == 'approve':
            # 审批通过
            # 生成访客码
            code_result = ElectronicCardService.generate_visitor_code(
                visitor_id=application.id,
                approval_time=datetime.now()
            )

            application.status = 'approved'
            application.access_code = code_result['code']
            application.approved_by = request.current_user_id
            application.approved_at = datetime.now()
            application.code_expires_at = datetime.strptime(
                code_result['expires_at'],
                '%Y-%m-%d %H:%M:%S'
            )

            db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'access_code': code_result['code'],
                    'expires_at': code_result['expires_at'],
                    'message': '审批通过'
                }
            })

        elif action == 'reject':
            # 拒绝
            rejection_reason = data.get('rejection_reason')
            if not rejection_reason:
                return jsonify({'error': '拒绝时必须填写拒绝理由'}), 400

            application.status = 'rejected'
            application.approved_by = request.current_user_id
            application.approved_at = datetime.now()
            application.rejection_reason = rejection_reason

            db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'message': '申请已拒绝',
                    'rejection_reason': rejection_reason
                }
            })

        else:
            return jsonify({'error': '无效的操作'}), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"审批访客申请失败: {str(e)}")
        return jsonify({'error': '审批访客申请失败', 'details': str(e)}), 500


# ==================== 照片上传 ====================

@electronic_card_bp.route('/photo/upload', methods=['POST'])
@token_required
def upload_photo():
    """
    上传照片

    请求:
        file: 照片文件（multipart/form-data）
        personnel_id: 人员ID（可选）

    返回:
    {
        "success": true,
        "data": {
            "photo_path": "/static/photos/123.jpg"
        }
    }
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400

        file = request.files['file']
        personnel_id = request.form.get('personnel_id')

        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        # 验证文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'error': '只支持图片文件（png, jpg, jpeg, gif）'}), 400

        # 保存文件
        import os
        import uuid
        from werkzeug.utils import secure_filename

        # 生成唯一文件名
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"

        # 确保上传目录存在
        upload_dir = os.path.join(current_app.root_path, 'static', 'photos')
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # 相对路径
        photo_path = f"/static/photos/{unique_filename}"

        # 如果指定了人员ID，更新数据库
        if personnel_id:
            user = User.query.get(personnel_id)
            if user:
                user.photo_path = photo_path
                db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'photo_path': photo_path
            }
        })

    except Exception as e:
        current_app.logger.error(f"上传照片失败: {str(e)}")
        return jsonify({'error': '上传照片失败', 'details': str(e)}), 500


@electronic_card_bp.route('/photo/upload-base64', methods=['POST'])
@token_required
def upload_photo_base64():
    """
    上传照片（Base64格式）

    请求体:
    {
        "photo_data": "base64_encoded_photo",
        "personnel_id": 123
    }

    返回:
    {
        "success": true,
        "data": {
            "photo_path": "/static/photos/123.jpg"
        }
    }
    """
    try:
        data = request.get_json()
        photo_data = data.get('photo_data')
        personnel_id = data.get('personnel_id')

        if not photo_data:
            return jsonify({'error': '照片数据不能为空'}), 400

        # 解码Base64
        try:
            # 去除可能的前缀
            if ',' in photo_data:
                photo_data = photo_data.split(',', 1)[1]

            photo_bytes = base64.b64decode(photo_data)
        except Exception:
            return jsonify({'error': '无效的Base64数据'}), 400

        # 保存文件
        import os
        import uuid
        from PIL import Image
        from io import BytesIO

        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}.jpg"

        # 确保上传目录存在
        upload_dir = os.path.join(current_app.root_path, 'static', 'photos')
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, unique_filename)

        # 压缩图片
        image = Image.open(BytesIO(photo_bytes))

        # 转换为RGB（如果需要）
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 调整大小（最大宽高）
        max_size = 800
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # 保存
        image.save(file_path, 'JPEG', quality=85)

        # 相对路径
        photo_path = f"/static/photos/{unique_filename}"

        # 如果指定了人员ID，更新数据库
        if personnel_id:
            user = User.query.get(personnel_id)
            if user:
                user.photo_path = photo_path
                db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'photo_path': photo_path
            }
        })

    except Exception as e:
        current_app.logger.error(f"上传照片失败: {str(e)}")
        return jsonify({'error': '上传照片失败', 'details': str(e)}), 500


# ==================== 门卫验证（统一接口）====================

@electronic_card_bp.route('/guard/verify', methods=['POST'])
def guard_verify():
    """
    门卫验证（统一接口，验证申请码和访客码）

    请求体:
    {
        "code": "123456",
        "guard_name": "门卫01"
    }

    返回:
    {
        "success": true,
        "data": {
            "code_type": "application",  # application/visitor
            "valid": true,
            "person_info": {...}
        }
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        guard_name = data.get('guard_name', 'unknown')

        if not code or len(code) != 6:
            return jsonify({'error': '访问码必须是6位数字'}), 400

        # 依次尝试验证

        # 1. 使用原始SQL查询访客码（避免ORM映射问题）
        visitor_query = db.text("""
            SELECT va.id, va.applicant_id, va.visit_date, va.visit_purpose, va.target_person,
                   va.application_status, va.approved_by, va.approval_time, va.qr_code,
                   u.username, u.real_name, u.user_type, u.phone, u.grade, u.class_id,
                   u.student_id, u.employee_id
            FROM visit_applications va
            LEFT JOIN users u ON va.applicant_id = u.id
            WHERE va.qr_code = :code
            AND va.application_status = 'approved'
            LIMIT 1
        """)

        visitor_result = db.session.execute(visitor_query, {'code': code}).fetchone()

        if visitor_result:
            (visitor_id, applicant_id, visit_date, visit_purpose, target_person,
             application_status, approved_by, approval_time, qr_code,
             username, real_name, user_type, phone, grade, class_id,
             student_id, employee_id) = visitor_result

            # 记录日志
            try:
                log_query = db.text("""
                    INSERT INTO verification_logs
                    (code_type, code, visitor_id, verification_result, verified_by, created_at)
                    VALUES (:code_type, :code, :visitor_id, :result, :verified_by, datetime('now'))
                """)
                db.session.execute(log_query, {
                    'code_type': 'visitor',
                    'code': code,
                    'visitor_id': visitor_id,
                    'result': True,
                    'verified_by': guard_name
                })
                db.session.commit()
            except Exception as log_error:
                current_app.logger.error(f"记录验证日志失败: {str(log_error)}")
                db.session.rollback()

            # 格式化审批时间
            try:
                if approval_time and hasattr(approval_time, 'strftime'):
                    approval_time_str = approval_time.strftime('%Y-%m-%d %H:%M')
                else:
                    approval_time_str = str(approval_time) if approval_time else None
            except:
                approval_time_str = None

            # 获取用户类型标签
            user_type_labels = {
                'student': '学生',
                'teacher': '教师',
                'parent': '家长',
                'alumni': '校友',
                'admin': '管理员'
            }
            user_type_label = user_type_labels.get(user_type, user_type)

            # 构建显示名称
            display_name = real_name or username or '访客'

            # 构建详细信息
            person_details = {
                'name': display_name,
                'user_type': user_type,
                'user_type_label': user_type_label,
                'phone': phone,
                'visit_reason': visit_purpose or '访问',
                'host_name': target_person or '接待人',
                'approved_by': approved_by,
                'approved_at': approval_time_str,
                'photo_url': None
            }

            # 如果是学生，添加班级信息
            if user_type == 'student':
                if grade and class_id:
                    person_details['class_name'] = f'{grade} {class_id}班'
                elif student_id:
                    person_details['student_id'] = student_id

            # 如果是家长，尝试获取关联的学生信息
            elif user_type == 'parent':
                parent_student_query = db.text("""
                    SELECT u.real_name, u.grade, u.class_id, u.student_id
                    FROM users u
                    WHERE u.id = (SELECT parent_student_id FROM users WHERE id = :applicant_id)
                    LIMIT 1
                """)
                student_result = db.session.execute(parent_student_query, {'applicant_id': applicant_id}).fetchone()

                if student_result:
                    student_name, student_grade, student_class, student_id_num = student_result
                    person_details['related_student'] = {
                        'name': student_name,
                        'grade': student_grade,
                        'class': student_class,
                        'student_id': student_id_num
                    }
                    # 显示孩子的班级
                    if student_grade and student_class:
                        person_details['child_class_name'] = f'{student_grade} {student_class}班'

            # 如果是校友，获取毕业年份
            elif user_type == 'alumni':
                alumni_query = db.text("""
                    SELECT graduation_year, class_name
                    FROM alumni_profiles
                    WHERE user_id = :applicant_id
                    LIMIT 1
                """)
                alumni_result = db.session.execute(alumni_query, {'applicant_id': applicant_id}).fetchone()

                if alumni_result:
                    graduation_year, class_name = alumni_result
                    person_details['graduation_year'] = graduation_year
                    person_details['class_name'] = f'{graduation_year}届 {class_name}'
                # 如果没有alumni_profile记录，尝试使用users表的grade字段
                elif grade:
                    person_details['graduation_year'] = grade
                    person_details['class_name'] = f'{grade}届'

            # 如果是教师，添加工号
            elif user_type == 'teacher' and employee_id:
                person_details['employee_id'] = employee_id

            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'visitor',
                    'valid': True,
                    'message': f'验证成功 - {user_type_label}',
                    'person_info': person_details
                }
            })

        # 2.5. 查询外部访客（applicant_id = 0的情况）
        external_visitor_query = db.text("""
            SELECT va.id, va.visit_date, va.visit_purpose, va.target_person,
                   va.approval_time, va.application_status, va.qr_code
            FROM visit_applications va
            WHERE va.qr_code = :code
            AND va.application_status = 'approved'
            AND va.applicant_id = 0
            ORDER BY va.created_at DESC
            LIMIT 1
        """)

        external_result = db.session.execute(external_visitor_query, {'code': code}).fetchone()

        if external_result:
            (ext_id, ext_visit_date, ext_visit_purpose, ext_target_person,
             ext_approval_time, ext_status, ext_qr_code) = external_result

            # 记录日志
            try:
                log_query = db.text("""
                    INSERT INTO verification_logs
                    (code_type, code, visitor_id, verification_result, verified_by, created_at)
                    VALUES (:code_type, :code, :visitor_id, :result, :verified_by, datetime('now'))
                """)
                db.session.execute(log_query, {
                    'code_type': 'external_visitor',
                    'code': code,
                    'visitor_id': ext_id,
                    'result': True,
                    'verified_by': guard_name
                })
                db.session.commit()
            except Exception as log_error:
                current_app.logger.error(f"记录验证日志失败: {str(log_error)}")
                db.session.rollback()

            # 格式化审批时间
            try:
                if ext_approval_time and hasattr(ext_approval_time, 'strftime'):
                    approval_time_str = ext_approval_time.strftime('%Y-%m-%d %H:%M')
                else:
                    approval_time_str = str(ext_approval_time) if ext_approval_time else None
            except:
                approval_time_str = None

            # 解析访问目的，提取公司信息
            purpose_parts = ext_visit_purpose.split(' - ', 1) if ext_visit_purpose else []
            visit_purpose = purpose_parts[0] if purpose_parts else ext_visit_purpose or '访问'
            visitor_company = purpose_parts[1] if len(purpose_parts) > 1 else ''

            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'external_visitor',
                    'valid': True,
                    'message': '验证成功 - 外部访客',
                    'person_info': {
                        'name': '外部访客',
                        'user_type': 'external_visitor',
                        'user_type_label': '外部访客',
                        'visit_purpose': visit_purpose,
                        'visitor_company': visitor_company,
                        'host_name': ext_target_person or '联系人',
                        'approved_at': approval_time_str
                    }
                }
            })

        # 3. 查询请假码
        from app.models.student_leave import StudentLeaveApplication

        leave_app = StudentLeaveApplication.query.filter_by(
            leave_code=code,
            status='approved'
        ).first()

        if leave_app:
            # 验证请假码
            if datetime.now() > leave_app.expires_at:
                return jsonify({
                    'success': True,
                    'data': {
                        'code_type': 'student_leave',
                        'valid': False,
                        'message': '请假码已过期'
                    }
                })

            # 检查使用次数
            if leave_app.used_count >= 2:
                return jsonify({
                    'success': True,
                    'data': {
                        'code_type': 'student_leave',
                        'valid': False,
                        'message': '请假码已使用完毕'
                    }
                })

            # 更新使用次数
            leave_app.used_count += 1
            db.session.commit()

            # 获取学生照片
            student = User.query.get(leave_app.student_id)

            # 判断是出校还是入校
            direction = '出校' if leave_app.used_count == 1 else '入校'

            # 记录日志
            from app.models.verification_log import VerificationLog
            log = VerificationLog(
                code_type='student_leave',
                code=code,
                personnel_id=leave_app.student_id,
                verification_result=True,
                verified_by=guard_name,
                user_name=leave_app.student_name
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'student_leave',
                    'valid': True,
                    'is_emergency': leave_app.is_emergency,
                    'direction': direction,
                    'remaining_uses': leave_app.get_remaining_uses(),
                    'message': f'验证成功 - {direction}' + (' (⚠️ 班主任特批)' if leave_app.is_emergency else ''),
                    'person_info': {
                        'name': leave_app.student_name,
                        'class_name': leave_app.class_name,
                        'grade': leave_app.grade,
                        'leave_reason': leave_app.leave_reason,
                        'leave_type': leave_app.get_leave_type_label(),
                        'expected_return_time': leave_app.expected_return_time.strftime('%Y-%m-%d %H:%M'),
                        'teacher_name': leave_app.teacher_name,
                        'approved_at': leave_app.approved_at.strftime('%Y-%m-%d %H:%M') if leave_app.approved_at else None,
                        'photo_url': getattr(student, 'photo_path', None),
                        'emergency_approver': leave_app.emergency_approver_name if leave_app.is_emergency else None,
                        'emergency_reason': leave_app.emergency_reason if leave_app.is_emergency else None
                    }
                }
            })

        # 4. 查询申请码（需要在请求中提供user_id）
        # 这里简化处理，实际使用中可以改进

        return jsonify({
            'success': True,
            'data': {
                'valid': False,
                'message': '访问码无效或已过期'
            }
        })

    except Exception as e:
        current_app.logger.error(f"验证访问码失败: {str(e)}")
        return jsonify({'error': '验证访问码失败', 'details': str(e)}), 500
