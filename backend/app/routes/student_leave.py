"""
学生请假出校 - API路由

提供学生请假申请、审批、验证等功能
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from functools import wraps

from app import db
from app.models.user import User
from app.models.student_leave import StudentLeaveApplication
from app.services.electronic_card_service import ElectronicCardService

student_leave_bp = Blueprint('student_leave', __name__)


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


# ==================== 学生请假申请（家长端）====================

@student_leave_bp.route('/apply', methods=['POST'])
def apply_leave():
    """
    家长申请学生请假

    请求体:
    {
        "student_name": "张三",
        "student_id": "2021001",  # 学号，用于查找学生
        "parent_name": "张父",
        "parent_phone": "13800138000",
        "parent_id_card": "210102198001011234",  # 可选，用于验证
        "leave_reason": "生病需要去医院",
        "leave_type": "sick",  # sick/personal/other
        "expected_return_date": "2026-03-28",
        "expected_return_time": "08:00"
    }

    返回:
    {
        "success": true,
        "data": {
            "application_id": 123,
            "leave_code": "654321",
            "status": "pending",
            "message": "请假申请已提交，等待班主任审批"
        }
    }
    """
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['student_name', 'student_id', 'parent_name', 'parent_phone',
                          'leave_reason', 'leave_type', 'expected_return_date', 'expected_return_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        # 验证请假类型
        if data['leave_type'] not in ['sick', 'personal', 'other']:
            return jsonify({'error': '无效的请假类型'}), 400

        # 查找学生
        student = User.query.filter(
            User.student_id == data['student_id'],
            User.user_type.like('%student%')
        ).first()

        if not student:
            return jsonify({'error': '学生不存在'}), 404

        # 计算过期时间（当天23:59:59）
        expected_return = datetime.strptime(
            f"{data['expected_return_date']} {data['expected_return_time']}",
            '%Y-%m-%d %H:%M'
        )
        expires_at = expected_return.replace(hour=23, minute=59, second=59)

        # 生成请假码（6位数字）
        import random
        leave_code = f"{random.randint(0, 999999):06d}"

        # 创建请假申请
        application = StudentLeaveApplication(
            student_id=student.id,
            student_name=data['student_name'],
            class_name=student.class_name,
            grade=student.grade,
            parent_name=data['parent_name'],
            parent_phone=data['parent_phone'],
            parent_id_card=data.get('parent_id_card'),
            leave_reason=data['leave_reason'],
            leave_type=data['leave_type'],
            expected_return_time=expected_return,
            leave_code=leave_code,
            status='pending',
            expires_at=expires_at
        )

        db.session.add(application)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'application_id': application.id,
                'leave_code': leave_code,
                'status': 'pending',
                'message': '请假申请已提交，等待班主任审批',
                'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"请假申请失败: {str(e)}")
        return jsonify({'error': '请假申请失败', 'details': str(e)}), 500


@student_leave_bp.route('/status/<int:application_id>', methods=['GET'])
def get_leave_status(application_id):
    """
    查询请假申请状态

    返回:
    {
        "success": true,
        "data": {
            "status": "approved",
            "leave_code": "654321",
            "approved_at": "2026-03-27 10:00",
            "teacher_name": "王老师"
        }
    }
    """
    try:
        application = StudentLeaveApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '申请不存在'}), 404

        result = {
            'application_id': application.id,
            'status': application.status,
            'status_label': application.get_status_label()
        }

        if application.status == 'approved':
            result['leave_code'] = application.leave_code
            result['approved_at'] = application.approved_at.strftime('%Y-%m-%d %H:%M')
            result['teacher_name'] = application.teacher_name
            result['message'] = '请假已批准'
        elif application.status == 'rejected':
            result['message'] = '请假已被拒绝'
            if application.rejection_reason:
                result['rejection_reason'] = application.rejection_reason
        else:
            result['message'] = '等待班主任审批'

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        current_app.logger.error(f"查询请假状态失败: {str(e)}")
        return jsonify({'error': '查询请假状态失败', 'details': str(e)}), 500


# ==================== 教师审批 ====================

@student_leave_bp.route('/pending', methods=['GET'])
@token_required
def get_pending_leaves():
    """
    获取待审批的请假申请列表（教师使用）

    返回:
    {
        "success": true,
        "data": {
            "applications": [...]
        }
    }
    """
    try:
        # 获取当前用户信息
        current_user = User.query.get(request.current_user_id)

        applications = StudentLeaveApplication.query.filter_by(
            status='pending'
        ).order_by(StudentLeaveApplication.created_at.desc()).all()

        result = []
        for app in applications:
            result.append({
                'id': app.id,
                'student_name': app.student_name,
                'class_name': app.class_name,
                'grade': app.grade,
                'parent_name': app.parent_name,
                'parent_phone': app.parent_phone,
                'leave_reason': app.leave_reason,
                'leave_type': app.leave_type,
                'leave_type_label': app.get_leave_type_label(),
                'expected_return_time': app.expected_return_time.strftime('%Y-%m-%d %H:%M'),
                'created_at': app.created_at.strftime('%Y-%m-%d %H:%M')
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


@student_leave_bp.route('/approve/<int:application_id>', methods=['POST'])
@token_required
def approve_leave(application_id):
    """
    审批学生请假（教师使用）

    请求体:
    {
        "action": "approve",  # approve/reject
        "rejection_reason": "理由不充分"  # 拒绝时必填
    }

    返回:
    {
        "success": true,
        "data": {
            "leave_code": "654321",
            "message": "审批通过"
        }
    }
    """
    try:
        data = request.get_json()
        action = data.get('action', 'approve')

        application = StudentLeaveApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '申请不存在'}), 404

        if application.status != 'pending':
            return jsonify({'error': '申请已被处理'}), 400

        current_user = User.query.get(request.current_user_id)

        if action == 'approve':
            # 审批通过
            application.status = 'approved'
            application.teacher_id = current_user.id
            application.teacher_name = current_user.real_name
            application.approved_at = datetime.now()

            db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'leave_code': application.leave_code,
                    'approved_at': application.approved_at.strftime('%Y-%m-%d %H:%M'),
                    'expires_at': application.expires_at.strftime('%Y-%m-%d %H:%M'),
                    'message': '审批通过'
                }
            })

        elif action == 'reject':
            # 拒绝
            rejection_reason = data.get('rejection_reason')
            if not rejection_reason:
                return jsonify({'error': '拒绝时必须填写拒绝理由'}), 400

            application.status = 'rejected'
            application.teacher_id = current_user.id
            application.teacher_name = current_user.real_name
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
        current_app.logger.error(f"审批请假申请失败: {str(e)}")
        return jsonify({'error': '审批请假申请失败', 'details': str(e)}), 500


# ==================== 班主任紧急特批 ====================

@student_leave_bp.route('/emergency-approve', methods=['POST'])
@token_required
def emergency_approve():
    """
    班主任紧急特批（无需家长码）

    请求体:
    {
        "student_name": "赵六",
        "student_id": "2021006",
        "emergency_reason": "学生突发高烧，多次联系家长未果",
        "emergency_note": "已联系校医确认体温39度",
        "expected_return_date": "2026-03-28",
        "expected_return_time": "08:00"
    }

    返回:
    {
        "success": true,
        "data": {
            "leave_code": "999999",
            "message": "特批成功，请告知学生凭特批码出校"
        }
    }
    """
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['student_name', 'student_id', 'emergency_reason',
                          'expected_return_date', 'expected_return_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        # 查找学生
        student = User.query.filter(
            User.student_id == data['student_id'],
            User.user_type.like('%student%')
        ).first()

        if not student:
            return jsonify({'error': '学生不存在'}), 404

        # 计算过期时间
        expected_return = datetime.strptime(
            f"{data['expected_return_date']} {data['expected_return_time']}",
            '%Y-%m-%d %H:%M'
        )
        expires_at = expected_return.replace(hour=23, minute=59, second=59)

        # 生成特批码（6位数字）
        import random
        leave_code = f"{random.randint(0, 999999):06d}"

        # 获取当前用户（班主任）
        current_user = User.query.get(request.current_user_id)

        # 创建请假申请（直接标记为已批准+紧急特批）
        application = StudentLeaveApplication(
            student_id=student.id,
            student_name=data['student_name'],
            class_name=student.class_name,
            grade=student.grade,
            parent_name='紧急特批',
            parent_phone='N/A',
            leave_reason=data['emergency_reason'],
            leave_type='other',
            expected_return_time=expected_return,
            leave_code=leave_code,
            status='approved',
            teacher_id=current_user.id,
            teacher_name=current_user.real_name,
            approved_at=datetime.now(),
            is_emergency=True,
            emergency_approver_id=current_user.id,
            emergency_approver_name=current_user.real_name,
            emergency_reason=data['emergency_reason'],
            expires_at=expires_at
        )

        db.session.add(application)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'application_id': application.id,
                'leave_code': leave_code,
                'status': 'approved',
                'is_emergency': True,
                'message': '特批成功，请告知学生凭特批码出校',
                'warning': '⚠️ 此为班主任特批，全程留痕记录',
                'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"紧急特批失败: {str(e)}")
        return jsonify({'error': '紧急特批失败', 'details': str(e)}), 500


# ==================== 门卫验证 ====================

@student_leave_bp.route('/verify/<code>', methods=['POST'])
def verify_leave_code(code):
    """
    门卫验证请假码

    请求体:
    {
        "guard_name": "门卫01"
    }

    返回:
    {
        "success": true,
        "data": {
            "code_type": "student_leave",
            "valid": true,
            "is_emergency": false,
            "student_info": {...}
        }
    }
    """
    try:
        from app.models.verification_log import VerificationLog

        data = request.get_json()
        guard_name = data.get('guard_name', 'unknown')

        # 查找请假申请
        application = StudentLeaveApplication.query.filter_by(
            leave_code=code,
            status='approved'
        ).first()

        if not application:
            # 记录验证失败日志
            log = VerificationLog(
                code_type='student_leave',
                code=code,
                verification_result=False,
                verified_by=guard_name,
                user_name=None
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'student_leave',
                    'valid': False,
                    'message': '请假码无效或未批准'
                }
            })

        # 检查是否过期
        if datetime.utcnow() > application.expires_at:
            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'student_leave',
                    'valid': False,
                    'message': '请假码已过期'
                }
            })

        # 检查使用次数
        if application.used_count >= 2:
            return jsonify({
                'success': True,
                'data': {
                    'code_type': 'student_leave',
                    'valid': False,
                    'message': '请假码已使用完毕'
                }
            })

        # 更新使用次数
        application.used_count += 1
        db.session.commit()

        # 获取学生照片
        student = User.query.get(application.student_id)

        # 记录验证成功日志
        log = VerificationLog(
            code_type='student_leave',
            code=code,
            personnel_id=application.student_id,
            verification_result=True,
            verified_by=guard_name,
            user_name=application.student_name
        )
        db.session.add(log)
        db.session.commit()

        # 判断是出校还是入校
        direction = '出校' if application.used_count == 1 else '入校'

        return jsonify({
            'success': True,
            'data': {
                'code_type': 'student_leave',
                'valid': True,
                'is_emergency': application.is_emergency,
                'direction': direction,
                'remaining_uses': application.get_remaining_uses(),
                'message': f'验证成功 - {direction}',
                'student_info': {
                    'name': application.student_name,
                    'class_name': application.class_name,
                    'grade': application.grade,
                    'leave_reason': application.leave_reason,
                    'leave_type': application.get_leave_type_label(),
                    'expected_return_time': application.expected_return_time.strftime('%Y-%m-%d %H:%M'),
                    'teacher_name': application.teacher_name,
                    'approved_at': application.approved_at.strftime('%Y-%m-%d %H:%M') if application.approved_at else None,
                    'photo_url': getattr(student, 'photo_path', None)
                },
                'emergency_info': {
                    'is_emergency': application.is_emergency,
                    'emergency_approver': application.emergency_approver_name,
                    'emergency_reason': application.emergency_reason if application.is_emergency else None
                } if application.is_emergency else None
            }
        })

    except Exception as e:
        current_app.logger.error(f"验证请假码失败: {str(e)}")
        return jsonify({'error': '验证请假码失败', 'details': str(e)}), 500


# ==================== 管理后台查询 ====================

@student_leave_bp.route('/records', methods=['GET'])
@token_required
def get_leave_records():
    """
    获取请假记录列表（管理后台）

    查询参数:
    - status: 状态筛选（pending/approved/rejected）
    - is_emergency: 是否特批（true/false）
    - start_date: 开始日期
    - end_date: 结束日期

    返回:
    {
        "success": true,
        "data": {
            "records": [...],
            "total": 100
        }
    }
    """
    try:
        # 获取查询参数
        status = request.args.get('status')
        is_emergency = request.args.get('is_emergency')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 构建查询
        query = StudentLeaveApplication.query

        if status:
            query = query.filter_by(status=status)
        if is_emergency is not None:
            query = query.filter_by(is_emergency=(is_emergency.lower() == 'true'))
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(StudentLeaveApplication.created_at >= start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(StudentLeaveApplication.created_at <= end)

        # 排序：特批记录优先，然后按时间倒序
        query = query.order_by(StudentLeaveApplication.is_emergency.desc(),
                              StudentLeaveApplication.created_at.desc())

        records = query.all()

        result = [record.to_dict() for record in records]

        return jsonify({
            'success': True,
            'data': {
                'records': result,
                'total': len(result)
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取请假记录失败: {str(e)}")
        return jsonify({'error': '获取请假记录失败', 'details': str(e)}), 500


@student_leave_bp.route('/export', methods=['GET'])
@token_required
def export_leave_records():
    """
    导出请假记录（Excel格式）

    查询参数同 /records

    返回: Excel文件
    """
    try:
        import io
        import xlsxwriter
        from flask import send_file

        # 获取数据（复用逻辑）
        # ... (同 get_leave_records)

        # 创建Excel文件
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        worksheet = workbook.add_worksheet('请假记录')

        # 添加表头
        headers = ['申请ID', '学生姓名', '班级', '年级', '家长姓名', '家长电话',
                  '请假原因', '请假类型', '状态', '审批人', '审批时间',
                  '是否特批', '特批人', '特批原因', '创建时间', '过期时间']

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # 添加数据行
        # ... (填充数据)

        workbook.close()
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'leave_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )

    except Exception as e:
        current_app.logger.error(f"导出请假记录失败: {str(e)}")
        return jsonify({'error': '导出请假记录失败', 'details': str(e)}), 500
