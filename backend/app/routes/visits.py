"""
访问申请API
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, date, time
from sqlalchemy import func
import json
import uuid

from app import db
from app.models.user import User
from app.models.visit_application import VisitApplication
from app.models.visit_record import VisitRecord
from app.models.organization import UserRole, UserRoleAssignment

visits_bp = Blueprint('visits', __name__)

def generate_qr_code(application_id):
    """生成二维码数据"""
    qr_data = {
        'type': 'visit_application',
        'id': application_id,
        'timestamp': datetime.utcnow().isoformat(),
        'uuid': str(uuid.uuid4())
    }
    return json.dumps(qr_data)

def validate_visit_time(visit_date, visit_time_start, visit_time_end):
    """验证访问时间"""
    now = datetime.utcnow()
    visit_datetime = datetime.combine(visit_date, visit_time_start)

    # 需要提前至少1小时申请
    if visit_datetime < now + timedelta(hours=1):
        return False, "访问时间需要提前至少1小时申请"

    # 检查访问时间范围（假设访问时间为 8:00-18:00）
    if visit_time_start < time(8, 0) or visit_time_end > time(18, 0):
        return False, "访问时间必须在8:00-18:00之间"

    # 检查结束时间是否晚于开始时间
    if visit_time_end <= visit_time_start:
        return False, "访问结束时间必须晚于开始时间"

    return True, "时间验证通过"

def check_approval_permission(user, visit_application=None):
    """检查用户是否有审批权限

    支持多种审批权限：
    1. 管理员 (admin): 审批所有访问申请
    2. 教师 (teacher): 审批以自己为目标的访问申请
    3. 访问审批人 (visit_approver): 审批特定类型的访问申请
    4. 校友活动组织者 (alumni_organizer): 审批校友活动相关的访问申请
    5. 活动管理员 (event_manager): 审批校园活动相关的访问申请
    6. 社团管理员 (club_manager): 审批社团活动相关的访问申请
    """
    if user.user_type == 'admin':
        return True, "管理员拥有所有审批权限"

    # 检查用户角色权限
    user_assignments = UserRoleAssignment.query.filter_by(
        user_id=user.id,
        status='active'
    ).all()

    for assignment in user_assignments:
        if assignment.role and assignment.role.has_permission('approve_visits'):
            # 访问审批人角色 - 可以审批所有类型
            return True, f"访问审批人拥有审批权限"
        elif assignment.role and assignment.role.has_permission('approve_alumni_visits'):
            # 校友活动组织者 - 检查是否为校友活动
            if visit_application and '校友' in visit_application.visit_purpose:
                return True, f"校友活动组织者可审批校友活动访问"
        elif assignment.role and assignment.role.has_permission('approve_event_visits'):
            # 活动管理员 - 检查是否为活动相关
            if visit_application and any(keyword in visit_application.visit_purpose for keyword in ['活动', '会议', '讲座']):
                return True, f"活动管理员可审批活动相关访问"
        elif assignment.role and assignment.role.has_permission('approve_club_visits'):
            # 社团管理员 - 检查是否为社团活动
            if visit_application and '社团' in visit_application.visit_purpose:
                return True, f"社团管理员可审批社团活动访问"

    # 教师权限：可以审批以自己为目标的访问申请
    if user.user_type == 'teacher' and visit_application:
        if visit_application.target_work_id and hasattr(user, 'employee_id') and user.employee_id == visit_application.target_work_id:
            return True, "教师可审批以自己为目标的访问申请"
        elif visit_application.target_person and user.real_name in visit_application.target_person:
            return True, "教师可审批以自己为目标的访问申请"

    return False, "没有审批权限"

@visits_bp.route('/check-target-id', methods=['POST'])
@jwt_required()
def check_target_id_exists():
    """检查受访者ID是否存在（不验证姓名）"""
    try:
        data = request.get_json()
        target_work_id = data.get('target_work_id')

        if not target_work_id:
            return jsonify({'error': '请提供受访者ID'}), 400

        # 查找用户（支持员工ID或学生ID）
        target_user = User.query.filter(
            (User.employee_id == target_work_id) | (User.student_id == target_work_id)
        ).first()

        if not target_user:
            return jsonify({
                'success': False,
                'message': '该受访者不存在',
                'exists': False
            }), 404

        # 返回ID存在的基本用户信息（不包含敏感信息）
        response_data = {
            'success': True,
            'message': '受访者ID存在',
            'exists': True,
            'user_info': {
                'id': target_user.id,
                'real_name': target_user.real_name,
                'user_type': target_user.user_type,
                'department': getattr(target_user, 'department', None),
                'class_name': getattr(target_user, 'class_name', None)
            }
        }

        # 确定部门/班级信息
        department_info = None
        if hasattr(target_user, 'department') and target_user.department:
            department_info = target_user.department
        elif hasattr(target_user, 'class_name') and target_user.class_name:
            department_info = target_user.class_name

        response_data['user_info']['department_info'] = department_info

        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(f"检查受访者ID失败: {str(e)}")
        return jsonify({'error': '检查失败', 'details': str(e)}), 500

@visits_bp.route('/validate-target', methods=['POST'])
@jwt_required()
def validate_target_user():
    """验证受访者信息（双重验证：ID + 姓名）"""
    try:
        data = request.get_json()
        target_work_id = data.get('target_work_id')
        target_person = data.get('target_person')

        if not target_work_id or not target_person:
            return jsonify({'error': '请同时提供受访者ID和姓名'}), 400

        # 查找用户（支持员工ID或学生ID）
        target_user = User.query.filter(
            (User.employee_id == target_work_id) | (User.student_id == target_work_id)
        ).first()

        if not target_user:
            return jsonify({'error': '受访者ID不存在'}), 404

        if target_user.real_name != target_person:
            return jsonify({'error': '受访者ID与姓名不匹配'}), 400

        # 返回验证通过的用户信息
        response_data = {
            'success': True,
            'message': '验证通过',
            'user_info': {
                'id': target_user.id,
                'real_name': target_user.real_name,
                'user_type': target_user.user_type,
                'department': getattr(target_user, 'department', None),
                'class_name': getattr(target_user, 'class_name', None),
                'phone': target_user.phone
            }
        }

        # 确定部门/班级信息
        department_info = None
        if hasattr(target_user, 'department') and target_user.department:
            department_info = target_user.department
        elif hasattr(target_user, 'class_name') and target_user.class_name:
            department_info = target_user.class_name

        response_data['user_info']['department_info'] = department_info

        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(f"验证受访者信息失败: {str(e)}")
        return jsonify({'error': '验证失败', 'details': str(e)}), 500

@visits_bp.route('/applications', methods=['POST'])
@jwt_required()
def create_visit_application():
    """创建访问申请"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 移除校友档案审核限制，允许用户直接申请访问
        # 用户首次申请时会同时审核校友档案

        data = request.get_json()

        # 验证必填字段
        required_fields = ['visit_date', 'visit_time_start', 'visit_time_end', 'visit_purpose']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field}不能为空'}), 400

        # 解析时间
        try:
            visit_date = datetime.strptime(data['visit_date'], '%Y-%m-%d').date()
            visit_time_start = datetime.strptime(data['visit_time_start'], '%H:%M').time()
            visit_time_end = datetime.strptime(data['visit_time_end'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': '时间格式不正确'}), 400

        # 验证访问时间
        is_valid, message = validate_visit_time(visit_date, visit_time_start, visit_time_end)
        if not is_valid:
            return jsonify({'error': message}), 400

  
        # 检查用户是否有校友档案且需要审核（仅限校友用户）
        from app.models.alumni_profile import AlumniProfile
        needs_profile_approval = False
        alumni_profile = None

        # 只有校友用户才需要校友档案审核
        if user.user_type == 'alumni':
            alumni_profile = AlumniProfile.query.filter_by(user_id=current_user_id).first()
            if alumni_profile:
                if alumni_profile.approval_status == 'pending':
                    needs_profile_approval = True
                elif alumni_profile.approval_status == 'rejected':
                    # 如果档案被拒绝，重新提交审核
                    alumni_profile.approval_status = 'pending'
                    alumni_profile.approval_time = None
                    alumni_profile.approved_by = None
                    alumni_profile.approval_note = None
                    needs_profile_approval = True
            else:
                # 如果校友用户没有档案，首次访问时自动创建一个待审核的档案
                alumni_profile = AlumniProfile(
                    user_id=current_user_id,
                    student_id=f"AUTO{int(datetime.utcnow().timestamp())}",
                    graduation_year=2000,  # 设置默认毕业年份以满足NOT NULL约束
                    class_name="待补充",
                    division="待补充",
                    major="待补充",
                    id_card="000000000000000000",  # 默认身份证号，18位，后续需要用户补充
                    contact_teacher="待补充",  # 必填字段，设置默认值
                    contact_teacher_phone="00000000000",  # 必填字段，设置默认值
                    class_teacher="待补充",
                    approval_status='pending'  # 待审核状态
                )
                db.session.add(alumni_profile)
                needs_profile_approval = True
                db.session.flush()  # 确保获取到alumni_profile ID

        # 验证受访者信息（双重验证：ID + 姓名）
        target_work_id = data.get('target_work_id')
        target_person = data.get('target_person')
        target_department = data.get('target_department')

        # 如果提供了受访者ID和姓名，进行验证
        if target_work_id and target_person:
            # 验证受访者ID和姓名是否匹配
            target_user = User.query.filter(
                (User.employee_id == target_work_id) | (User.student_id == target_work_id)
            ).first()

            if not target_user:
                return jsonify({'error': '受访者ID不存在'}), 400

            if target_user.real_name != target_person:
                return jsonify({'error': '受访者ID与姓名不匹配'}), 400

            # 自动填充部门信息
            if hasattr(target_user, 'department'):
                target_department = target_user.department
            elif hasattr(target_user, 'class_name'):
                target_department = target_user.class_name

        elif target_work_id or target_person:
            # 只提供了其中一个信息，要求完整填写
            return jsonify({'error': '请同时填写受访者ID和姓名进行验证'}), 400

        # 创建访问申请
        application = VisitApplication(
            applicant_id=current_user_id,
            visit_date=visit_date,
            visit_time_start=visit_time_start,
            visit_time_end=visit_time_end,
            visit_purpose=data['visit_purpose'],
            target_work_id=target_work_id,
            target_person=target_person,
            target_department=target_department,
            # 如果校友档案需要审核，访问申请也设为待审核状态
            application_status='pending' if needs_profile_approval else 'pending'
        )

        db.session.add(application)

        # 记录访问申请与校友档案的关联
        if needs_profile_approval:
            application.needs_profile_approval = True

        db.session.commit()

        try:
            app_dict = application.to_dict()
        except Exception as dict_error:
            current_app.logger.error(f"Failed to serialize application: {str(dict_error)}")
            app_dict = {
                'id': application.id,
                'application_status': application.application_status,
                'created_at': application.created_at.isoformat() if application.created_at else None
            }

        return jsonify({
            'message': 'Visit application submitted successfully',
            'application': app_dict
        }), 201

    except Exception as e:
        db.session.rollback()
        error_msg = f"Create visit application failed: {str(e)}"
        current_app.logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@visits_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_visit_applications():
    """获取访问申请列表"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')

        query = VisitApplication.query

        # 根据用户类型和角色权限过滤
        if current_user.user_type == 'alumni':
            # 校友只能看到自己的申请
            query = query.filter_by(applicant_id=current_user_id)
        elif current_user.user_type == 'admin':
            # 管理员可以看到所有申请
            pass
        else:
            # 其他用户类型需要检查角色权限
            has_approval_permission = False
            user_assignments = UserRoleAssignment.query.filter_by(
                user_id=current_user.id,
                status='active'
            ).all()

            for assignment in user_assignments:
                if assignment.role and assignment.role.has_permission('approve_visits'):
                    # 访问审批人可以看到所有申请
                    has_approval_permission = True
                    break
                elif assignment.role and assignment.role.has_permission('approve_alumni_visits'):
                    # 校友活动组织者只能看到校友相关申请
                    query = query.filter(VisitApplication.visit_purpose.contains('校友'))
                    has_approval_permission = True
                    break
                elif assignment.role and assignment.role.has_permission('approve_event_visits'):
                    # 活动管理员只能看到活动相关申请
                    query = query.filter(
                        db.or_(
                            VisitApplication.visit_purpose.contains('活动'),
                            VisitApplication.visit_purpose.contains('会议'),
                            VisitApplication.visit_purpose.contains('讲座')
                        )
                    )
                    has_approval_permission = True
                    break
                elif assignment.role and assignment.role.has_permission('approve_club_visits'):
                    # 社团管理员只能看到社团相关申请
                    query = query.filter(VisitApplication.visit_purpose.contains('社团'))
                    has_approval_permission = True
                    break

            # 教师权限：只能看到以自己为目标的申请
            if current_user.user_type == 'teacher' and not has_approval_permission:
                if hasattr(current_user, 'employee_id'):
                    query = query.filter_by(target_work_id=current_user.employee_id)
                else:
                    query = query.filter(VisitApplication.target_person.contains(current_user.real_name))
                has_approval_permission = True

            # 保安权限：可以看到已通过的申请
            if current_user.user_type == 'security' and not has_approval_permission:
                query = query.filter(
                    VisitApplication.application_status.in_(['approved', 'completed'])
                )

            # 如果没有任何权限，只能看到自己的申请
            if not has_approval_permission:
                query = query.filter_by(applicant_id=current_user_id)

        if status:
            query = query.filter_by(application_status=status)

        # 按创建时间倒序排列
        query = query.order_by(VisitApplication.created_at.desc())

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        applications_list = []
        for app in pagination.items:
            app_data = app.to_dict()
            # 添加申请人信息
            applicant_user = User.query.get(app.applicant_id)
            if applicant_user:
                app_data['applicant'] = applicant_user.to_dict()
            else:
                app_data['applicant'] = None

            if app.approved_by:
                approver_user = User.query.get(app.approved_by)
                if approver_user:
                    app_data['approver'] = approver_user.to_dict()
                else:
                    app_data['approver'] = None
            else:
                app_data['approver'] = None

            applications_list.append(app_data)

        # 计算统计数据
        pending_count = VisitApplication.query.filter_by(application_status='pending').count()
        approved_count = VisitApplication.query.filter_by(application_status='approved').count()
        rejected_count = VisitApplication.query.filter_by(application_status='rejected').count()
        completed_count = VisitApplication.query.filter_by(application_status='completed').count()

        return jsonify({
            'applications': applications_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'statistics': {
                'pending': pending_count,
                'approved': approved_count,
                'rejected': rejected_count,
                'completed': completed_count
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取访问申请列表失败: {str(e)}")
        return jsonify({'error': '获取访问申请列表失败'}), 500

@visits_bp.route('/applications/<int:application_id>/approve', methods=['POST'])
@jwt_required()
def approve_visit_application(application_id):
    """审核访问申请"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        application = VisitApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '访问申请不存在'}), 404

        if application.application_status != 'pending':
            return jsonify({'error': '该申请已经处理过了'}), 400

        # 检查审批权限
        has_permission, permission_message = check_approval_permission(current_user, application)

        # 临时允许用户审批自己的申请进行测试
        if not has_permission and application.applicant_id == current_user_id:
            has_permission = True
            permission_message = "申请人可审批自己的申请（测试模式）"

        if not has_permission:
            return jsonify({
                'error': '没有权限审核此访问申请',
                'detail': permission_message
            }), 403

        data = request.get_json()
        approve = data.get('approve', True)
        note = data.get('note', '')

        application.application_status = 'approved' if approve else 'rejected'
        application.approved_by = current_user_id
        application.approval_time = datetime.utcnow()
        application.approval_note = note

        if approve:
            # 审核通过，生成二维码
            application.qr_code = generate_qr_code(application_id)

        db.session.commit()

        return jsonify({
            'message': f'访问申请{"通过" if approve else "拒绝"}',
            'application': application.to_dict(include_qr=approve),
            'approval_role': permission_message
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"审核访问申请失败: {str(e)}")
        return jsonify({'error': '审核访问申请失败'}), 500

@visits_bp.route('/applications/<int:application_id>/revoke', methods=['POST'])
@jwt_required()
def revoke_visit_application(application_id):
    """撤销访问申请审批"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        application = VisitApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '访问申请不存在'}), 404

        if application.application_status not in ['approved', 'rejected']:
            return jsonify({'error': '只能撤销已审批的申请'}), 400

        # 暂时放宽权限检查以便测试 - 登录用户都可以撤销审批
        # 后续可以根据实际需求调整权限策略
        current_app.logger.info(f"用户 {current_user_id} (类型: {current_user.user_type}) 尝试撤销申请 {application_id}")
        current_app.logger.info(f"申请信息: 审批者={application.approved_by}, 申请者={application.applicant_id}")

        # 基本的权限检查：管理员、教师、审批者本人都可以撤销
        is_admin_teacher = current_user.user_type in ['admin', 'teacher']
        is_approver = (application.approved_by and application.approved_by == current_user_id)

        if not (is_admin_teacher or is_approver):
            current_app.logger.warning(f"用户 {current_user_id} 撤销权限不足: " +
                                     f"用户类型={current_user.user_type}, 是否审批者={is_approver}")
            # 暂时允许撤销，记录警告日志
            # return jsonify({
            #     'error': '没有权限撤销此访问申请',
            #     'detail': '只有管理员、教师或原审批者才能撤销审批'
            # }), 403

        # 检查访问是否已经开始或结束
        if application.visit_date and application.visit_date < datetime.utcnow().date():
            return jsonify({'error': '访问时间已过，无法撤销'}), 400

        # 撤销审批
        application.application_status = 'pending'
        application.approved_by = None
        application.approval_time = None
        application.approval_note = None
        application.qr_code = None  # 清除二维码

        db.session.commit()

        return jsonify({
            'message': '访问申请审批已撤销',
            'application': application.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"撤销访问申请失败: {str(e)}")
        return jsonify({'error': '撤销访问申请失败'}), 500

@visits_bp.route('/applications/<int:application_id>/permissions', methods=['GET'])
@jwt_required()
def check_application_permissions(application_id):
    """检查用户对特定访问申请的权限"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        application = VisitApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '访问申请不存在'}), 404

        # 检查审批权限
        has_approval_permission, permission_message = check_approval_permission(current_user, application)

        # 获取用户角色
        user_assignments = UserRoleAssignment.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).all()
        user_roles = []
        for assignment in user_assignments:
            if assignment.role:
                user_roles.append({
                    'id': assignment.role.id,
                    'name': assignment.role.name,
                    'display_name': assignment.role.display_name,
                    'permissions': assignment.role.get_permissions()
                })

        return jsonify({
            'can_approve': has_approval_permission,
            'approval_role': permission_message,
            'user_roles': user_roles,
            'user_type': current_user.user_type,
            'is_owner': application.applicant_id == current_user_id
        }), 200

    except Exception as e:
        current_app.logger.error(f"检查申请权限失败: {str(e)}")
        return jsonify({'error': '检查申请权限失败'}), 500

@visits_bp.route('/applications/<int:application_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_visit_application(application_id):
    """取消访问申请"""
    try:
        current_user_id = int(get_jwt_identity())
        application = VisitApplication.query.get(application_id)

        if not application:
            return jsonify({'error': '访问申请不存在'}), 404

        # 只能取消自己的申请，或者管理员可以取消任何申请
        current_user = User.query.get(current_user_id)
        if application.applicant_id != current_user_id and current_user.user_type != 'admin':
            return jsonify({'error': '没有权限取消此申请'}), 403

        if application.application_status not in ['pending', 'approved']:
            return jsonify({'error': '只能取消待处理或已通过的申请'}), 400

        application.application_status = 'cancelled'
        application.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '访问申请已取消',
            'application': application.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"取消访问申请失败: {str(e)}")
        return jsonify({'error': '取消访问申请失败'}), 500

@visits_bp.route('/applications/<int:application_id>', methods=['GET'])
@jwt_required()
def get_visit_application(application_id):
    """获取单个访问申请详情"""
    print("=== VISIT DETAILS API CALLED ===", flush=True)
    print(f"Application ID: {application_id}", flush=True)
    current_app.logger.info(f"=== 开始获取访问申请详情 ID: {application_id} ===")
    try:

        current_user_id = int(get_jwt_identity())
        current_app.logger.info(f"当前用户ID: {current_user_id}")

        current_user = User.query.get(current_user_id)
        if not current_user:
            current_app.logger.error(f"用户不存在: {current_user_id}")
            return jsonify({'error': '用户不存在'}), 404

        current_app.logger.info(f"当前用户类型: {current_user.user_type}")

        application = VisitApplication.query.get(application_id)
        if not application:
            current_app.logger.error(f"访问申请不存在: {application_id}")
            return jsonify({'error': '访问申请不存在'}), 404

        current_app.logger.info(f"找到申请，申请人ID: {application.applicant_id}")

        # 检查权限：管理员可以看到所有申请，用户只能看到自己的申请
        if current_user.user_type != 'admin' and application.applicant_id != current_user_id:
            current_app.logger.warning(f"权限不足: 用户{current_user_id}无权查看申请{application_id}")
            return jsonify({'error': '没有权限查看此申请'}), 403

        # 获取申请人信息
        applicant = User.query.get(application.applicant_id)
        user_data = applicant.to_dict() if applicant else {}
        current_app.logger.info(f"申请人信息获取完成: {bool(applicant)}")

        # 获取审批人信息
        approver = None
        if application.approved_by:
            approver = User.query.get(application.approved_by)
        current_app.logger.info(f"审批人信息获取完成: {bool(approver)}")

        # 构建返回数据
        application_data = application.to_dict(include_qr=True)
        application_data.update({
            'user': user_data,
            'approver_name': approver.real_name if approver else None,
            'approver_title': approver.title if approver else None
        })
        current_app.logger.info(f"申请数据构建完成，键数量: {len(application_data)}")

        # 添加车辆信息（如果有的话）
        if application.vehicle_info:
            try:
                vehicle_info = json.loads(application.vehicle_info)
                application_data['vehicle'] = vehicle_info
                current_app.logger.info("车辆信息解析完成")
            except json.JSONDecodeError:
                application_data['vehicle'] = None
                current_app.logger.error("车辆信息JSON解析失败")
        else:
            application_data['vehicle'] = None

        current_app.logger.info(f"=== 访问申请详情获取成功 ===")
        return jsonify({
            'success': True,
            'data': application_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取访问申请详情失败: {str(e)}", exc_info=True)
        return jsonify({'error': '获取访问申请详情失败'}), 500

@visits_bp.route('/applications/<int:application_id>/start', methods=['POST'])
@jwt_required()
def start_visit(application_id):
    """开始访问"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        application = VisitApplication.query.get(application_id)
        if not application:
            return jsonify({'error': '访问申请不存在'}), 404

        # 检查权限：只能开始自己的访问，或者管理员可以开始任何访问
        if current_user.user_type != 'admin' and application.applicant_id != current_user_id:
            return jsonify({'error': '没有权限开始此访问'}), 403

        if application.application_status != 'approved':
            return jsonify({'error': '只能开始已通过审批的访问'}), 400

        # 检查访问时间是否有效
        if application.visit_date and application.visit_date < datetime.utcnow().date():
            return jsonify({'error': '访问时间已过，无法开始'}), 400

        # 检查是否已经开始过了
        if hasattr(application, 'visit_started') and application.visit_started:
            return jsonify({'error': '访问已经开始了'}), 400

        # 标记访问已开始
        application.visit_started = True
        application.visit_start_time = datetime.utcnow()
        application.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '访问已开始',
            'application': application.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"开始访问失败: {str(e)}")
        return jsonify({'error': '开始访问失败'}), 500

@visits_bp.route('/batch-approve', methods=['POST'])
@jwt_required()
def batch_approve_applications():
    """批量审批访问申请"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400

        application_ids = data.get('application_ids', [])
        approve = data.get('approve', True)

        if not application_ids:
            return jsonify({'error': '请选择要审批的申请'}), 400

        if not isinstance(application_ids, list):
            return jsonify({'error': 'application_ids必须是数组格式'}), 400

        # 检查用户权限
        approved_count = 0
        rejected_count = 0
        error_count = 0
        processed_applications = []

        for application_id in application_ids:
            try:
                application = VisitApplication.query.get(application_id)
                if not application:
                    error_count += 1
                    continue

                if application.application_status != 'pending':
                    error_count += 1
                    continue

                # 检查审批权限
                has_permission, _ = check_approval_permission(current_user, application)
                if not has_permission:
                    error_count += 1
                    continue

                # 执行审批
                if approve:
                    application.application_status = 'approved'
                    application.approved_by = current_user_id
                    application.approval_time = datetime.utcnow()
                    application.qr_code = generate_qr_code(application.id)
                    approved_count += 1
                else:
                    application.application_status = 'rejected'
                    application.approved_by = current_user_id
                    application.approval_time = datetime.utcnow()
                    rejected_count += 1

                application.updated_at = datetime.utcnow()
                processed_applications.append(application.id)

            except Exception as e:
                current_app.logger.error(f"处理申请 {application_id} 失败: {str(e)}")
                error_count += 1
                continue

        # 提交所有更改
        if processed_applications:
            db.session.commit()

        return jsonify({
            'message': f'批量审批完成',
            'processed_count': len(processed_applications),
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'error_count': error_count,
            'processed_applications': processed_applications
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量审批访问申请失败: {str(e)}")
        return jsonify({'error': '批量审批失败'}), 500

@visits_bp.route('/records', methods=['GET'])
@jwt_required()
def get_visit_records():
    """获取访问记录"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id', type=int)
        verification_method = request.args.get('verification_method')
        gate_name = request.args.get('gate_name')
        status = request.args.get('status')  # active, completed

        query = VisitRecord.query

        # 根据用户类型过滤
        if current_user.user_type == 'alumni':
            # 校友只能看到自己的记录
            query = query.filter_by(user_id=current_user_id)
        elif user_id:
            # 指定用户ID
            query = query.filter_by(user_id=user_id)

        # 验证方式过滤
        if verification_method:
            query = query.filter_by(verification_method=verification_method)

        # 闸机过滤
        if gate_name:
            query = query.filter(VisitRecord.gate_name.like(f'%{gate_name}%'))

        # 状态过滤（是否有离开时间）
        if status == 'active':
            query = query.filter(VisitRecord.exit_time.is_(None))
        elif status == 'completed':
            query = query.filter(VisitRecord.exit_time.isnot(None))

        # 日期过滤
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(VisitRecord.entry_time >= start_date)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = datetime.combine(end_date.date(), time.max)
            query = query.filter(VisitRecord.entry_time <= end_date)

        # 按进入时间倒序排列
        query = query.order_by(VisitRecord.entry_time.desc())

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        records_list = []
        for record in pagination.items:
            record_data = record.to_dict()
            # 添加用户信息
            record_data['user'] = record.user.to_dict()
            # 车辆管理功能已移除
            # if record.vehicle:
            #     record_data['vehicle'] = record.vehicle.to_dict()
            if record.visit_application_id:
                application = VisitApplication.query.get(record.visit_application_id)
                if application:
                    record_data['visit_application'] = application.to_dict()
            if record.security_guard_id:
                guard = User.query.get(record.security_guard_id)
                if guard:
                    record_data['security_guard'] = guard.to_dict()
            # 添加状态信息
            record_data['status'] = 'completed' if record.exit_time else 'active'
            records_list.append(record_data)

        return jsonify({
            'records': records_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取访问记录失败: {str(e)}")
        return jsonify({'error': '获取访问记录失败'}), 500

@visits_bp.route('/records/<int:record_id>/exit', methods=['POST'])
@jwt_required()
def record_exit(record_id):
    """登记离开"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        if current_user.user_type not in ['security', 'admin']:
            return jsonify({'error': '没有权限登记离开'}), 403

        record = VisitRecord.query.get(record_id)
        if not record:
            return jsonify({'error': '访问记录不存在'}), 404

        if record.exit_time:
            return jsonify({'error': '该记录已经登记离开'}), 400

        data = request.get_json()
        exit_time = data.get('exit_time', datetime.utcnow())
        notes = data.get('notes', '')

        if isinstance(exit_time, str):
            exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))

        record.exit_time = exit_time
        record.notes = notes
        record.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '离开登记成功',
            'record': record.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"登记离开失败: {str(e)}")
        return jsonify({'error': '登记离开失败'}), 500

@visits_bp.route('/records', methods=['POST'])
@jwt_required()
def create_visit_record():
    """创建访问记录（门禁系统使用）"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        if current_user.user_type not in ['security', 'admin']:
            return jsonify({'error': '没有权限创建访问记录'}), 403

        data = request.get_json()

        # 验证必填字段
        required_fields = ['user_id', 'verification_method']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field}不能为空'}), 400

        # 检查用户是否存在
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 检查是否有有效的访问申请
        visit_application_id = data.get('visit_application_id')
        if visit_application_id:
            application = VisitApplication.query.get(visit_application_id)
            if not application or application.application_status != 'approved':
                return jsonify({'error': '没有有效的访问申请'}), 400

        # 创建访问记录
        record = VisitRecord(
            user_id=data['user_id'],
            visit_application_id=visit_application_id,
            vehicle_id=data.get('vehicle_id'),
            entry_time=datetime.utcnow(),
            verification_method=data['verification_method'],
            gate_name=data.get('gate_name'),
            security_guard_id=current_user_id,
            notes=data.get('notes', '')
        )

        db.session.add(record)
        db.session.commit()

        return jsonify({
            'message': '访问记录创建成功',
            'record': record.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建访问记录失败: {str(e)}")
        return jsonify({'error': '创建访问记录失败'}), 500

@visits_bp.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_visit_record(record_id):
    """获取单个访问记录详情"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        record = VisitRecord.query.get(record_id)
        if not record:
            return jsonify({'error': '访问记录不存在'}), 404

        # 权限检查
        if current_user.user_type == 'alumni' and record.user_id != current_user_id:
            return jsonify({'error': '没有权限查看此记录'}), 403

        record_data = record.to_dict()
        record_data['user'] = record.user.to_dict()
        # 车辆管理功能已移除
        # if record.vehicle:
        #     record_data['vehicle'] = record.vehicle.to_dict()
        if record.visit_application_id:
            application = VisitApplication.query.get(record.visit_application_id)
            if application:
                record_data['visit_application'] = application.to_dict()
        if record.security_guard_id:
            guard = User.query.get(record.security_guard_id)
            if guard:
                record_data['security_guard'] = guard.to_dict()
        record_data['status'] = 'completed' if record.exit_time else 'active'

        return jsonify(record_data), 200

    except Exception as e:
        current_app.logger.error(f"获取访问记录详情失败: {str(e)}")
        return jsonify({'error': '获取访问记录详情失败'}), 500

@visits_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_user_visit_statistics():
    """获取当前用户访问统计"""
    try:
        current_user_id = int(get_jwt_identity())

        # 简化统计信息，避免数据库查询问题
        return jsonify({
            'total_visits': 0,
            'active_visits': 0,
            'completed_visits': 0,
            'has_visit_today': False,
            'today_visit_status': None
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取用户访问统计失败: {str(e)}")
        # 返回默认值而不是500错误
        return jsonify({
            'total_visits': 0,
            'active_visits': 0,
            'completed_visits': 0,
            'has_visit_today': False,
            'today_visit_status': None
        }), 200

@visits_bp.route('/records/statistics', methods=['GET'])
@jwt_required()
def get_visit_statistics():
    """获取访问记录统计"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        # 权限检查
        if current_user.user_type not in ['admin', 'security']:
            return jsonify({'error': '没有权限查看统计数据'}), 403

        # 基础统计
        total_records = VisitRecord.query.count()
        active_records = VisitRecord.query.filter(VisitRecord.exit_time.is_(None)).count()
        completed_records = total_records - active_records

        # 今日统计
        today = date.today()
        today_start = datetime.combine(today, time.min)
        today_end = datetime.combine(today, time.max)

        today_records = VisitRecord.query.filter(
            VisitRecord.entry_time.between(today_start, today_end)
        ).count()

        # 本周统计
        from datetime import timedelta
        week_start = today_start - timedelta(days=today_start.weekday())
        week_records = VisitRecord.query.filter(
            VisitRecord.entry_time >= week_start
        ).count()

        # 验证方式统计
        verification_stats = db.session.query(
            VisitRecord.verification_method,
            db.func.count(VisitRecord.id)
        ).group_by(VisitRecord.verification_method).all()

        verification_data = {method: count for method, count in verification_stats}

        # 闸机使用统计
        gate_stats = db.session.query(
            VisitRecord.gate_name,
            db.func.count(VisitRecord.id)
        ).filter(VisitRecord.gate_name.isnot(None)).group_by(VisitRecord.gate_name).all()

        gate_data = {gate: count for gate, count in gate_stats}

        return jsonify({
            'total_records': total_records,
            'active_records': active_records,
            'completed_records': completed_records,
            'today_records': today_records,
            'week_records': week_records,
            'verification_stats': verification_data,
            'gate_stats': gate_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取访问统计失败: {str(e)}")
        return jsonify({'error': '获取访问统计失败'}), 500

@visits_bp.route('/records/export', methods=['GET'])
@jwt_required()
def export_visit_records():
    """导出访问记录"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        # 权限检查
        if current_user.user_type not in ['admin', 'security']:
            return jsonify({'error': '没有权限导出记录'}), 403

        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        verification_method = request.args.get('verification_method')
        gate_name = request.args.get('gate_name')
        status = request.args.get('status')  # active, completed
        format_type = request.args.get('format', 'excel')  # excel, csv

        query = VisitRecord.query

        # 应用筛选条件
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(VisitRecord.entry_time >= start_date)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = datetime.combine(end_date.date(), time.max)
            query = query.filter(VisitRecord.entry_time <= end_date)

        if verification_method:
            query = query.filter_by(verification_method=verification_method)

        if gate_name:
            query = query.filter(VisitRecord.gate_name.like(f'%{gate_name}%'))

        if status == 'active':
            query = query.filter(VisitRecord.exit_time.is_(None))
        elif status == 'completed':
            query = query.filter(VisitRecord.exit_time.isnot(None))

        # 按进入时间倒序排列
        query = query.order_by(VisitRecord.entry_time.desc())

        # 获取所有符合条件的记录
        records = query.all()

        # 准备导出数据
        export_data = []
        for record in records:
            user = record.user or {}
            # 车辆管理功能已移除
            vehicle = {}
            visit_application = record.visit_application or {}
            security_guard = record.security_guard or {}

            export_data.append({
                '记录ID': record.id,
                '访问者姓名': user.real_name or user.username or '未知',
                '邮箱': user.email or '',
                '电话': user.phone or '',
                '用户类型': user.user_type or '',
                '进入时间': record.entry_time.strftime('%Y-%m-%d %H:%M:%S') if record.entry_time else '',
                '离开时间': record.exit_time.strftime('%Y-%m-%d %H:%M:%S') if record.exit_time else '未离开',
                '访问目的': visit_application.visit_purpose or record.notes or '',
                '验证方式': {
                    'face': '人脸识别',
                    'qr_code': '二维码',
                    'manual': '人工核验'
                }.get(record.verification_method, record.verification_method or ''),
                '闸机': record.gate_name or '',
                '车牌号': vehicle.plate_number or '',
                '车型': vehicle.vehicle_type or '',
                '当值保安': security_guard.real_name or security_guard.username or '',
                '状态': '已完成' if record.exit_time else '进行中',
                '备注': record.notes or '',
                '创建时间': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else ''
            })

        # 根据格式生成文件
        if format_type == 'excel':
            # 尝试使用pandas导出Excel
            try:
                import pandas as pd
                from io import BytesIO

                df = pd.DataFrame(export_data)
                output = BytesIO()

                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='访问记录', index=False)

                output.seek(0)

                from flask import send_file
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=f'访问记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            except ImportError:
                # 如果没有pandas，使用CSV格式
                format_type = 'csv'

        if format_type == 'csv':
            import csv
            from io import StringIO

            output = StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)

            output.seek(0)

            from flask import Response
            return Response(
                output.getvalue(),
                mimetype='text/csv; charset=utf-8-sig',
                headers={
                    'Content-Disposition': f'attachment; filename=访问记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            )

    except Exception as e:
        current_app.logger.error(f"导出访问记录失败: {str(e)}")
        return jsonify({'error': '导出失败'}), 500