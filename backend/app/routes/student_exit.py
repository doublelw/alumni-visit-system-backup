"""
学生出校申请相关路由
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, time
from app import db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
import json

student_exit_bp = Blueprint('student_exit', __name__, url_prefix='/api/student-exit')

@student_exit_bp.route('/students', methods=['GET'])
@jwt_required()
def get_available_students():
    """根据用户身份获取可选的学生列表"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        students = []

        if current_user.user_type == 'student':
            # 学生只能选择自己
            students = [{
                'id': current_user.id,
                'student_id': current_user.student_id,
                'real_name': current_user.real_name,
                'class_name': getattr(current_user, 'class_id', ''),
                'department': getattr(current_user, 'department', '')
            }]
        elif current_user.user_type == 'parent':
            # 家长可以选择自己的孩子
            children = User.query.filter_by(
                user_type='student',
                student_parent_id=current_user.id
            ).all()

            students = [{
                'id': child.id,
                'student_id': child.student_id,
                'real_name': child.real_name,
                'class_name': getattr(child, 'class_id', ''),
                'department': getattr(child, 'department', '')
            } for child in children]
        elif current_user.user_type == 'teacher':
            # 班主任可以选择本班学生
            if hasattr(current_user, 'class_id') and current_user.class_id:
                class_students = User.query.filter_by(
                    user_type='student',
                    class_id=current_user.class_id
                ).all()

                students = [{
                    'id': student.id,
                    'student_id': student.student_id,
                    'real_name': student.real_name,
                    'class_name': getattr(student, 'class_id', ''),
                    'department': getattr(student, 'department', '')
                } for student in class_students]

        return jsonify({
            'success': True,
            'students': students
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取学生列表失败: {str(e)}")
        return jsonify({'error': '获取学生列表失败', 'details': str(e)}), 500

@student_exit_bp.route('/student/<int:student_id>/info', methods=['GET'])
@jwt_required()
def get_student_info(student_id):
    """获取学生详细信息，包括紧急联系人"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        # 验证学生存在
        student = User.query.get(student_id)
        if not student or student.user_type != 'student':
            return jsonify({'error': '学生不存在'}), 404

        # 验证权限
        if current_user.user_type == 'student' and student_id != current_user.id:
            return jsonify({'error': '您只能查看自己的信息'}), 403
        elif current_user.user_type == 'parent' and student.student_parent_id != current_user.id:
            return jsonify({'error': '您没有权限查看该学生信息'}), 403
        elif current_user.user_type == 'teacher':
            if hasattr(current_user, 'class_name') and student.class_name != current_user.class_name:
                return jsonify({'error': '您只能查看本班学生信息'}), 403

        # 获取紧急联系人信息
        emergency_contact = ''
        emergency_phone = ''
        if student.student_parent_id:
            parent = User.query.get(student.student_parent_id)
            if parent:
                emergency_contact = parent.real_name
                emergency_phone = parent.phone or ''

        return jsonify({
            'success': True,
            'student': {
                'id': student.id,
                'student_id': student.student_id,
                'real_name': student.real_name,
                'class_name': getattr(student, 'class_id', ''),
                'department': getattr(student, 'department', ''),
                'emergency_contact': emergency_contact,
                'emergency_phone': emergency_phone
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取学生信息失败: {str(e)}")
        return jsonify({'error': '获取学生信息失败', 'details': str(e)}), 500

@student_exit_bp.route('/applications', methods=['POST'])
@jwt_required()
def create_application():
    """创建学生出校申请"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        data = request.get_json()

        # 获取学生ID
        student_id = data.get('student_id')
        if not student_id:
            return jsonify({'error': '请选择学生'}), 400

        # 验证学生存在
        student = User.query.get(student_id)
        if not student or student.user_type != 'student':
            return jsonify({'error': '学生不存在'}), 404

        # 验证申请人身份和权限
        if current_user.user_type == 'student':
            # 学生只能为自己申请
            if student_id != current_user.id:
                return jsonify({'error': '您只能为自己申请出校'}), 403
            applicant_id = current_user.id
        elif current_user.user_type == 'parent':
            # 家长为孩子申请
            if student.student_parent_id != current_user.id:
                return jsonify({'error': '您没有权限为该学生申请'}), 403
            applicant_id = current_user.id
        elif current_user.user_type == 'teacher':
            # 班主任为学生申请（需要学生家长授权或特殊权限）
            if hasattr(current_user, 'class_id') and getattr(student, 'class_id', '') != current_user.class_id:
                return jsonify({'error': '您只能为本班学生申请出校'}), 403
            applicant_id = current_user.id
        else:
            return jsonify({'error': '只有学生、家长和教师可以申请出校'}), 403

        # 自动带出紧急联系人信息（如果没有提供则使用家长信息）
        emergency_contact = data.get('emergency_contact', '')
        emergency_phone = data.get('emergency_phone', '')

        if not emergency_contact or not emergency_phone:
            # 如果没有提供紧急联系人，尝试使用家长信息
            if student.student_parent_id:
                parent = User.query.get(student.student_parent_id)
                if parent:
                    emergency_contact = emergency_contact or parent.real_name
                    emergency_phone = emergency_phone or (parent.phone or '')

        # 创建申请记录
        application = StudentExitApplication(
            student_id=student_id,
            applicant_id=applicant_id,
            exit_date=datetime.strptime(data['exit_date'], '%Y-%m-%d').date(),
            exit_time_start=datetime.strptime(data['exit_time_start'], '%H:%M').time(),
            exit_time_end=datetime.strptime(data['exit_time_end'], '%H:%M').time(),
            exit_reason=data['exit_reason'],
            destination=data.get('destination', ''),
            transport_method=data.get('transport_method', ''),
            emergency_contact=emergency_contact,
            emergency_phone=emergency_phone
        )

        db.session.add(application)
        db.session.commit()

        return jsonify({
            'message': '申请提交成功',
            'application': application.to_dict()
        }), 201

    except Exception as e:
        current_app.logger.error(f"创建学生出校申请失败: {str(e)}")
        current_app.logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
        import traceback
        current_app.logger.error(f"错误追踪: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'error': f'申请提交失败: {str(e)}'}), 500

@student_exit_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_applications():
    """获取出校申请列表"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')

        query = StudentExitApplication.query

        # 根据用户类型过滤
        if current_user.user_type == 'student':
            query = query.filter_by(student_id=current_user.id)
        elif current_user.user_type == 'parent':
            # 获取该家长关联的所有学生的申请
            related_students = User.query.filter_by(student_parent_id=current_user.id).all()
            student_ids = [s.id for s in related_students]
            query = query.filter(StudentExitApplication.student_id.in_(student_ids))
        elif current_user.user_type == 'teacher' and current_user.is_class_teacher:
            # 班主任查看本班学生的申请
            # 这里可以根据班级字段过滤，暂时获取所有申请
            pass

        # 按状态过滤
        if status:
            query = query.filter_by(application_status=status)

        # 按创建时间倒序排列
        query = query.order_by(StudentExitApplication.created_at.desc())

        applications = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'applications': [app.to_dict() for app in applications.items],
            'total': applications.total,
            'pages': applications.pages,
            'current_page': page
        })

    except Exception as e:
        current_app.logger.error(f"获取学生出校申请列表失败: {str(e)}")
        return jsonify({'error': '获取申请列表失败'}), 500

@student_exit_bp.route('/applications/<int:application_id>', methods=['GET'])
@jwt_required()
def get_application(application_id):
    """获取单个申请详情"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        application = StudentExitApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '申请不存在'}), 404

        # 权限检查
        if not can_view_application(current_user, application):
            return jsonify({'error': '没有权限查看此申请'}), 403

        return jsonify({
            'application': application.to_dict()
        })

    except Exception as e:
        current_app.logger.error(f"获取学生出校申请详情失败: {str(e)}")
        return jsonify({'error': '获取申请详情失败'}), 500

@student_exit_bp.route('/applications/<int:application_id>/acknowledge', methods=['POST'])
@jwt_required()
def acknowledge_application(application_id):
    """家长知晓申请"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        application = StudentExitApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '申请不存在'}), 404

        # 获取提交的数据
        data = request.get_json() or {}
        note = data.get('note', '')

        # 验证权限：只有家长可以知晓，且必须是申请学生的家长
        student = User.query.get(application.student_id)
        if not student:
            return jsonify({'error': '学生不存在'}), 404

        if current_user.user_type != 'parent':
            return jsonify({'error': '只有家长可以知晓申请'}), 403

        if student.student_parent_id != current_user.id:
            return jsonify({'error': '您只能知晓自己孩子的申请'}), 403

        # 检查申请状态
        if application.parent_approval_status != 'pending':
            return jsonify({'error': '申请已经被处理过了'}), 400

        # 更新家长知晓状态
        application.parent_approval_status = 'approved'
        application.parent_approval_time = datetime.utcnow()
        application.parent_approval_note = note
        application.parent_approved_by = current_user.id

        # 更新整体申请状态
        application.update_approval_status()

        db.session.commit()

        return jsonify({
            'message': '已知晓此申请',
            'application': application.to_dict()
        })

    except Exception as e:
        current_app.logger.error(f"家长知晓申请失败: {str(e)}")
        current_app.logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
        import traceback
        current_app.logger.error(f"错误追踪: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'error': '知晓申请失败，请重试'}), 500

@student_exit_bp.route('/applications/<int:application_id>/approve', methods=['POST'])
@jwt_required()
def approve_application(application_id):
    """审批申请"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        application = StudentExitApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '申请不存在'}), 404

        data = request.get_json()
        approval_action = data.get('action')  # 'approve' or 'reject'
        approval_note = data.get('note', '')

        if approval_action not in ['approve', 'reject']:
            return jsonify({'error': '无效的审批操作'}), 400

        # 权限检查和审批逻辑
        if current_user.user_type == 'parent':
            # 家长审批
            if not application.can_approve(current_user.id, 'parent'):
                return jsonify({'error': '您没有权限审批此申请'}), 403

            application.parent_approval_status = 'approved' if approval_action == 'approve' else 'rejected'
            application.parent_approval_time = datetime.utcnow()
            application.parent_approval_note = approval_note
            application.parent_approved_by = current_user.id

        elif current_user.user_type == 'teacher' and current_user.is_class_teacher:
            # 班主任审批 - 必须先有家长知晓
            if not application.can_approve(current_user.id, 'teacher'):
                return jsonify({'error': '您没有权限审批此申请'}), 403

            # 检查家长是否已经知晓
            if application.parent_approval_status != 'approved':
                return jsonify({'error': '请等待家长知晓后才能审批'}), 400

            application.teacher_approval_status = 'approved' if approval_action == 'approve' else 'rejected'
            application.teacher_approval_time = datetime.utcnow()
            application.teacher_approval_note = approval_note
            application.teacher_approved_by = current_user.id

        else:
            return jsonify({'error': '您没有审批权限'}), 403

        # 更新总体审批状态
        application.update_approval_status()

        return jsonify({
            'message': '审批成功',
            'application': application.to_dict()
        })

    except Exception as e:
        current_app.logger.error(f"审批学生出校申请失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '审批失败，请重试'}), 500

@student_exit_bp.route('/applications/<int:application_id>/qr-code', methods=['GET'])
@jwt_required()
def get_qr_code(application_id):
    """获取申请的二维码"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        application = StudentExitApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '申请不存在'}), 404

        # 权限检查
        if not can_view_application(current_user, application):
            return jsonify({'error': '没有权限查看此申请'}), 403

        # 检查二维码是否有效
        if not application.is_qr_code_valid():
            return jsonify({'error': '二维码无效或已过期'}), 400

        return jsonify({
            'qr_code': application.qr_code,
            'expires_at': application.qr_code_expires_at.isoformat() if application.qr_code_expires_at else None
        })

    except Exception as e:
        current_app.logger.error(f"获取学生出校二维码失败: {str(e)}")
        return jsonify({'error': '获取二维码失败'}), 500

@student_exit_bp.route('/applications/verify-code', methods=['POST'])
def verify_application_code():
    """通过6位验证码验证学生出校申请"""
    try:
        # 检查请求是否来自保安端
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '需要保安端授权'}), 401

        token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': '授权令牌无效'}), 401

        # 验证保安端token
        security_user = User.query.filter_by(user_type='security', token=token).first()
        if not security_user:
            return jsonify({'error': '授权失败，保安端用户不存在'}), 401

        data = request.get_json()
        if not data or 'verification_code' not in data:
            return jsonify({'error': '请提供6位验证码'}), 400

        verification_code = data['verification_code']

        if not verification_code or len(verification_code) != 6 or not verification_code.isdigit():
            return jsonify({'error': '验证码格式不正确，应为6位数字'}), 400

        # 查找匹配的申请
        application = StudentExitApplication.query.filter_by(
            verification_code=verification_code
        ).first()

        if not application:
            return jsonify({'error': '验证码无效或申请不存在'}), 404

        # 检查二维码/验证码是否有效
        if not application.is_qr_code_valid():
            return jsonify({'error': '验证码已过期或申请状态无效'}), 400

        return jsonify({
            'success': True,
            'message': '验证成功',
            'student': {
                'id': application.student.id,
                'real_name': application.student.real_name,
                'student_id': application.student.student_id,
                'class_id': application.student.class_id,
                'grade': application.student.grade
            },
            'application': {
                'id': application.id,
                'exit_date': application.exit_date.isoformat() if application.exit_date else None,
                'exit_time_start': application.exit_time_start.isoformat() if application.exit_time_start else None,
                'exit_time_end': application.exit_time_end.isoformat() if application.exit_time_end else None,
                'exit_reason': application.exit_reason,
                'destination': application.destination,
                'application_status': application.application_status,
                'exit_status': application.exit_status,
                'verification_code': application.verification_code
            }
        })

    except Exception as e:
        current_app.logger.error(f"验证学生出校申请码失败: {str(e)}")
        return jsonify({'error': '验证失败，请重试'}), 500

@student_exit_bp.route('/applications/by-face', methods=['POST'])
def get_application_by_face():
    """通过人脸识别获取申请信息"""
    try:
        # 检查请求是否来自保安端
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '需要保安端授权'}), 401

        token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': '授权令牌无效'}), 401

        # 验证保安端token
        security_user = User.query.filter_by(user_type='security', token=token).first()
        if not security_user:
            return jsonify({'error': '授权失败，保安端用户不存在'}), 401

        # 获取人脸数据
        face_data = request.get_json()
        if not face_data or 'face_image' not in face_data:
            return jsonify({'error': '请提供人脸数据'}), 400

        face_image = face_data['face_image']

        # 这里应该调用人脸识别服务来识别学生
        # 暂时使用模拟的方式，通过学生ID或学号查找
        student_info = None

        # 如果提供了学生ID，直接查找
        if 'student_id' in face_data:
            student = User.query.filter_by(
                user_type='student',
                student_id=face_data['student_id']
            ).first()
            if student:
                student_info = student
        # 如果提供了姓名，查找匹配的学生
        elif 'student_name' in face_data:
            students = User.query.filter_by(
                user_type='student',
                real_name=face_data['student_name']
            ).all()
            if students:
                student_info = students[0]

        if not student_info:
            return jsonify({'error': '未找到匹配的学生信息'}), 404

        # 查询该学生的最近申请
        applications = StudentExitApplication.query.filter_by(
            student_id=student_info.id
        ).order_by(StudentExitApplication.created_at.desc()).limit(3).all()

        if not applications:
            return jsonify({
                'student': {
                    'id': student_info.id,
                    'real_name': student_info.real_name,
                    'student_id': student_info.student_id,
                    'class_id': student_info.class_id,
                    'grade': student_info.grade
                },
                'applications': [],
                'message': '该学生暂无出校申请记录'
            }), 200

        return jsonify({
            'student': {
                'id': student_info.id,
                'real_name': student_info.real_name,
                'student_id': student_info.student_id,
                'class_id': student_info.class_id,
                'grade': student_info.grade
            },
            'applications': [{
                'id': app.id,
                'exit_date': app.exit_date.isoformat() if app.exit_date else None,
                'exit_time_start': app.exit_time_start.isoformat() if app.exit_time_start else None,
                'exit_time_end': app.exit_time_end.isoformat() if app.exit_time_end else None,
                'exit_reason': app.exit_reason,
                'destination': app.destination,
                'application_status': app.application_status,
                'parent_approval_status': app.parent_approval_status,
                'teacher_approval_status': app.teacher_approval_status,
                'parent_approval_time': app.parent_approval_time.isoformat() if app.parent_approval_time else None,
                'teacher_approval_time': app.teacher_approval_time.isoformat() if app.teacher_approval_time else None,
                'created_at': app.created_at.isoformat() if app.created_at else None,
                'has_qr_code': bool(app.qr_code and app.is_qr_code_valid()),
                'exit_status': app.exit_status
            } for app in applications]
        })

    except Exception as e:
        current_app.logger.error(f"通过人脸识别获取申请失败: {str(e)}")
        return jsonify({'error': '查询失败，请重试'}), 500

@student_exit_bp.route('/applications/pending-approval', methods=['GET'])
@jwt_required()
def get_pending_approval_applications():
    """获取待审批的申请列表"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        # 根据用户类型获取待审批申请
        if current_user.user_type == 'parent':
            # 获取该家长需要审批的申请（自己孩子的申请）
            related_students = User.query.filter_by(student_parent_id=current_user.id, user_type='student').all()
            student_ids = [s.id for s in related_students]

            applications = StudentExitApplication.query.filter(
                StudentExitApplication.student_id.in_(student_ids),
                StudentExitApplication.parent_approval_status == 'pending',
                StudentExitApplication.application_status.in_(['pending', 'teacher_approved'])
            ).order_by(StudentExitApplication.created_at.desc()).limit(10).all()

        elif current_user.user_type == 'teacher' and current_user.is_class_teacher:
            # 获取班主任需要审批的申请
            applications = StudentExitApplication.query.filter(
                StudentExitApplication.teacher_approval_status == 'pending',
                StudentExitApplication.application_status.in_(['pending', 'parent_approved'])
            ).order_by(StudentExitApplication.created_at.desc()).limit(10).all()

        else:
            return jsonify({'error': '您没有审批权限'}), 403

        return jsonify({
            'applications': [{
                'id': app.id,
                'student_name': app.student.real_name if app.student else '未知',
                'student_class': app.student.class_id if app.student else '',
                'exit_date': app.exit_date.isoformat() if app.exit_date else None,
                'exit_time_start': app.exit_time_start.isoformat() if app.exit_time_start else None,
                'exit_time_end': app.exit_time_end.isoformat() if app.exit_time_end else None,
                'exit_reason': app.exit_reason,
                'destination': app.destination,
                'application_status': app.application_status,
                'parent_approval_status': app.parent_approval_status,
                'teacher_approval_status': app.teacher_approval_status,
                'created_at': app.created_at.isoformat() if app.created_at else None,
                'can_approve': app.can_approve(current_user.id, current_user.user_type)
            } for app in applications]
        })

    except Exception as e:
        current_app.logger.error(f"获取待审批申请失败: {str(e)}")
        return jsonify({'error': '获取待审批申请失败'}), 500

@student_exit_bp.route('/applications/recent', methods=['GET'])
@jwt_required()
def get_recent_applications():
    """获取最近的申请列表"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        # 根据用户类型获取相关申请
        if current_user.user_type == 'student':
            # 学生查看自己的申请
            applications = StudentExitApplication.query.filter_by(
                student_id=current_user.id
            ).order_by(StudentExitApplication.created_at.desc()).limit(5).all()

        elif current_user.user_type == 'parent':
            # 家长查看自己孩子的申请
            related_students = User.query.filter_by(student_parent_id=current_user.id, user_type='student').all()
            student_ids = [s.id for s in related_students]

            applications = StudentExitApplication.query.filter(
                StudentExitApplication.student_id.in_(student_ids)
            ).order_by(StudentExitApplication.created_at.desc()).limit(5).all()

        elif current_user.user_type == 'teacher' and current_user.is_class_teacher:
            # 班主任查看本班学生的申请
            applications = StudentExitApplication.query.filter(
                StudentExitApplication.application_status.in_(['pending', 'parent_approved', 'teacher_approved', 'approved', 'rejected'])
            ).order_by(StudentExitApplication.created_at.desc()).limit(5).all()

        else:
            applications = []

        return jsonify({
            'success': True,
            'applications': [{
                'id': app.id,
                'applicant_name': app.student.real_name if app.student else '未知',
                'student_name': app.student.real_name if app.student else '未知',
                'reason': app.exit_reason,
                'exit_date': app.exit_date.isoformat() if app.exit_date else None,
                'exit_time': app.exit_time_start.strftime('%H:%M') if app.exit_time_start else None,
                'status': app.application_status,
                'application_status': app.application_status,
                'created_at': app.created_at.isoformat() if app.created_at else None,
                'application_date': app.created_at.isoformat() if app.created_at else None,
                'can_approve': app.can_approve(current_user.id, current_user.user_type)
            } for app in applications]
        })

    except Exception as e:
        current_app.logger.error(f"获取最近申请失败: {str(e)}")
        return jsonify({'error': '获取最近申请失败'}), 500

@student_exit_bp.route('/parents/students', methods=['GET'])
@jwt_required()
def get_parent_students():
    """获取家长关联的学生列表"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user or current_user.user_type != 'parent':
            return jsonify({'error': '只有家长可以查看关联的学生'}), 403

        students = User.query.filter_by(student_parent_id=current_user.id, user_type='student').all()

        return jsonify({
            'students': [{
                'id': student.id,
                'real_name': student.real_name,
                'student_id': student.student_id,
                'class_id': student.class_id,
                'grade': student.grade
            } for student in students]
        })

    except Exception as e:
        current_app.logger.error(f"获取家长关联学生失败: {str(e)}")
        return jsonify({'error': '获取学生列表失败'}), 500

def can_view_application(user, application):
    """检查用户是否可以查看申请"""
    if user.user_type == 'student':
        return application.student_id == user.id
    elif user.user_type == 'parent':
        # 检查是否是学生的家长
        student = User.query.get(application.student_id)
        return student and student.student_parent_id == user.id
    elif user.user_type == 'teacher' and user.is_class_teacher:
        # 班主任可以查看本班学生的申请
        return True
    elif user.user_type in ['admin', 'security']:
        return True

@student_exit_bp.route('/applications/pending-acknowledgment', methods=['GET'])
@jwt_required()
def get_pending_acknowledgment_applications():
    """获取家长需要知晓的申请（代办事项）"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        # 只有家长有代办事项
        if current_user.user_type != 'parent':
            return jsonify({'applications': [], 'total': 0})

        # 获取该家长所有孩子的申请，其中家长还未知晓的
        applications = StudentExitApplication.query.join(User, StudentExitApplication.student_id == User.id)\
            .filter(User.student_parent_id == current_user.id)\
            .filter(StudentExitApplication.parent_approval_status == 'pending')\
            .order_by(StudentExitApplication.created_at.desc())\
            .all()

        return jsonify({
            'applications': [app.to_dict() for app in applications],
            'total': len(applications)
        })

    except Exception as e:
        current_app.logger.error(f"获取家长代办事项失败: {str(e)}")
        return jsonify({'error': '获取代办事项失败'}), 500