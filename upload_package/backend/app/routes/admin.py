"""
管理员API
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

from app import db
from app.models.user import User
from app.models.alumni_profile import AlumniProfile
from app.models.visit_application import VisitApplication
from app.models.visit_record import VisitRecord

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@jwt_required()
def admin_required():
    """管理员权限检查"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or current_user.user_type != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403

@admin_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """获取仪表板数据"""
    try:
        # 基础统计数据
        total_users = User.query.count()
        total_alumni = User.query.filter_by(user_type='alumni').count()
        total_teachers = User.query.filter_by(user_type='teacher').count()
        total_security = User.query.filter_by(user_type='security').count()

        # 访问相关统计
        today = datetime.utcnow().date()
        today_visits = VisitRecord.query.filter(
            func.date(VisitRecord.entry_time) == today
        ).count()

        total_visits = VisitRecord.query.count()
        total_applications = VisitApplication.query.count()

        # 待审核事项
        pending_alumni = AlumniProfile.query.filter_by(approval_status='pending').count()
        pending_visits = VisitApplication.query.filter_by(application_status='pending').count()

        # 模拟趋势数据（避免复杂查询导致的错误）
        from datetime import date, timedelta
        visit_trend = []
        for i in range(7):
            d = date.today() - timedelta(days=6-i)
            count = VisitRecord.query.filter(
                func.date(VisitRecord.entry_time) == d
            ).count()
            visit_trend.append({'date': d.isoformat(), 'count': count})

        # 访问目的统计
        purpose_stats = db.session.query(
            VisitApplication.visit_purpose,
            func.count(VisitApplication.id).label('count')
        ).filter(
            VisitApplication.application_status.in_(['approved', 'completed'])
        ).group_by(VisitApplication.visit_purpose).limit(10).all()

        return jsonify({
            'statistics': {
                'total_users': total_users,
                'total_alumni': total_alumni,
                'total_teachers': total_teachers,
                'total_security': total_security,
                'today_visits': today_visits,
                'total_visits': total_visits,
                'total_applications': total_applications,
                'pending_alumni': pending_alumni,
                'pending_visits': pending_visits
            },
            'visit_trend': visit_trend,
            'purpose_stats': [{'purpose': stat.visit_purpose, 'count': stat.count} for stat in purpose_stats]
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取仪表板数据失败: {str(e)}")
        return jsonify({'error': '获取仪表板数据失败', 'details': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_type = request.args.get('user_type', '')
        status = request.args.get('status', '')
        search = request.args.get('search', '')

        query = User.query

        if user_type:
            query = query.filter_by(user_type=user_type)

        if status:
            query = query.filter_by(status=status)

        if search:
            query = query.filter(
                User.real_name.contains(search) |
                User.username.contains(search) |
                User.phone.contains(search) |
                User.email.contains(search)
            )

        # 关联校友档案搜索
        if search:
            query = query.outerjoin(AlumniProfile).filter(
                AlumniProfile.student_id.contains(search) |
                AlumniProfile.class_name.contains(search) |
                AlumniProfile.division.contains(search)
            )

        query = query.order_by(User.created_at.desc())

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        users_list = []
        for user in pagination.items:
            user_data = user.to_dict()
            if user.alumni_profile:
                user_data['alumni_profile'] = user.alumni_profile.to_dict()
            users_list.append(user_data)

        return jsonify({
            'users': users_list,
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
        current_app.logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({'error': '获取用户列表失败'}), 500

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
def update_user_status(user_id):
    """更新用户状态"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        data = request.get_json()
        status = data.get('status')

        if status not in ['active', 'inactive']:
            return jsonify({'error': '状态值无效'}), 400

        user.status = status
        user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': '用户状态更新成功',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新用户状态失败: {str(e)}")
        return jsonify({'error': '更新用户状态失败'}), 500

@admin_bp.route('/alumni-approve', methods=['GET'])
def get_alumni_for_approval():
    """获取校友审核列表 - 支持状态筛选"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', 'pending')  # pending, approved, rejected, all
        search = request.args.get('search', '')
        division = request.args.get('division', '')
        graduation_year = request.args.get('graduation_year', '')

        # 构建查询，明确指定join关系
        query = AlumniProfile.query.join(User, AlumniProfile.user_id == User.id)

        # 状态筛选
        if status != 'all':
            query = query.filter(AlumniProfile.approval_status == status)

        # 搜索筛选
        if search:
            query = query.filter(
                db.or_(
                    User.real_name.contains(search),
                    User.username.contains(search),
                    AlumniProfile.student_id.contains(search),
                    AlumniProfile.class_name.contains(search)
                )
            )

        # 学部筛选
        if division:
            query = query.filter(AlumniProfile.division == division)

        # 年级筛选
        if graduation_year:
            query = query.filter(AlumniProfile.graduation_year == graduation_year)

        # 排序：待审核优先，然后按创建时间倒序
        query = query.order_by(
            db.case(
                (AlumniProfile.approval_status == 'pending', 0),
                (AlumniProfile.approval_status == 'rejected', 2),
                (AlumniProfile.approval_status == 'approved', 3),
                else_=1
            ),
            AlumniProfile.created_at.desc()
        )

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        alumni_list = []
        for profile in pagination.items:
            alumni_data = profile.to_dict()
            alumni_data['user'] = profile.user.to_dict()
            # 添加审核历史信息
            if profile.approved_by:
                approver = User.query.get(profile.approved_by)
                alumni_data['approver_name'] = approver.real_name if approver else '未知'
            else:
                alumni_data['approver_name'] = None
            alumni_list.append(alumni_data)

        # 获取统计数据
        stats = {
            'pending': AlumniProfile.query.filter_by(approval_status='pending').count(),
            'approved': AlumniProfile.query.filter_by(approval_status='approved').count(),
            'rejected': AlumniProfile.query.filter_by(approval_status='rejected').count(),
            'total': AlumniProfile.query.count()
        }

        # 获取筛选选项
        divisions = db.session.query(AlumniProfile.division).distinct().all()
        graduation_years = db.session.query(AlumniProfile.graduation_year).distinct().order_by(AlumniProfile.graduation_year.desc()).all()

        return jsonify({
            'alumni': alumni_list,
            'statistics': stats,
            'filters': {
                'divisions': [div[0] for div in divisions if div[0]],
                'graduation_years': [year[0] for year in graduation_years]
            },
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
        current_app.logger.error(f"获取校友审核列表失败: {str(e)}")
        return jsonify({'error': '获取校友审核列表失败', 'details': str(e)}), 500

@admin_bp.route('/alumni/<int:profile_id>/approve', methods=['POST'])
def approve_alumni(profile_id):
    """审核校友"""
    try:
        current_user_id = get_jwt_identity()

        profile = AlumniProfile.query.get(profile_id)
        if not profile:
            return jsonify({'error': '校友档案不存在'}), 404

        if profile.approval_status != 'pending':
            return jsonify({'error': '该档案已经处理过了'}), 400

        data = request.get_json()
        approve = data.get('approve', True)
        note = data.get('note', '')

        profile.approval_status = 'approved' if approve else 'rejected'
        profile.approved_by = current_user_id
        profile.approval_time = datetime.utcnow()
        profile.approval_note = note

        # 如果审核通过，激活用户账户
        user = profile.user
        if approve and user.status == 'pending':
            user.status = 'active'

        db.session.commit()

        return jsonify({
            'message': f'校友档案{"通过" if approve else "拒绝"}审核',
            'alumni': profile.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"审核校友档案失败: {str(e)}")
        return jsonify({'error': '审核校友档案失败'}), 500

@admin_bp.route('/alumni/<int:profile_id>/reapprove', methods=['POST'])
def reapprove_alumni(profile_id):
    """重新审核校友"""
    try:
        current_user_id = get_jwt_identity()

        profile = AlumniProfile.query.get(profile_id)
        if not profile:
            return jsonify({'error': '校友档案不存在'}), 404

        # 只允许重新审核已拒绝的校友
        if profile.approval_status != 'rejected':
            return jsonify({'error': '只能重新审核已拒绝的校友档案'}), 400

        # 重置审核状态
        profile.approval_status = 'pending'
        profile.approved_by = None
        profile.approval_time = None
        profile.approval_note = ''

        db.session.commit()

        return jsonify({
            'message': '校友档案已重新提交审核',
            'alumni': profile.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"重新审核校友档案失败: {str(e)}")
        return jsonify({'error': '重新审核校友档案失败'}), 500

@admin_bp.route('/batch-approve', methods=['POST'])
def batch_approve():
    """批量授权访问"""
    try:
        current_user_id = get_jwt_identity()

        data = request.get_json()
        batch_type = data.get('type')  # 'class', 'year', 'division'
        target_value = data.get('target_value')
        visit_date = data.get('visit_date')
        time_start = data.get('time_start')
        time_end = data.get('time_end')
        visit_purpose = data.get('visit_purpose')

        if not all([batch_type, target_value, visit_date, time_start, time_end, visit_purpose]):
            return jsonify({'error': '请提供完整的批量授权信息'}), 400

        # 查找符合条件的校友
        query = AlumniProfile.query.filter_by(approval_status='approved')
        if batch_type == 'class':
            query = query.filter_by(class_name=target_value)
        elif batch_type == 'year':
            query = query.filter_by(graduation_year=int(target_value))
        elif batch_type == 'division':
            query = query.filter_by(division=target_value)
        else:
            return jsonify({'error': '批量授权类型无效'}), 400

        alumni_profiles = query.all()

        if not alumni_profiles:
            return jsonify({'error': '未找到符合条件的校友'}), 404

        # 解析时间
        visit_date = datetime.strptime(visit_date, '%Y-%m-%d').date()
        time_start = datetime.strptime(time_start, '%H:%M').time()
        time_end = datetime.strptime(time_end, '%H:%M').time()

        # 创建访问申请
        created_applications = []
        for profile in alumni_profiles:
            application = VisitApplication(
                applicant_id=profile.user_id,
                visit_date=visit_date,
                visit_time_start=time_start,
                visit_time_end=time_end,
                visit_purpose=f"批量授权: {visit_purpose}",
                application_status='approved',
                approved_by=current_user_id,
                approval_time=datetime.utcnow(),
                approval_note=f"批量授权 - {batch_type}: {target_value}"
            )
            db.session.add(application)
            created_applications.append(application)

        db.session.commit()

        return jsonify({
            'message': f'成功为 {len(created_applications)} 位校友创建访问授权',
            'count': len(created_applications)
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量授权失败: {str(e)}")
        return jsonify({'error': '批量授权失败'}), 500

@admin_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取详细统计数据"""
    try:
        # 时间范围参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')  # day, week, month
        statistic_type = request.args.get('type', 'overview')  # overview, visits, applications, people

        # 基础统计
        total_visits = VisitRecord.query.count()
        total_applications = VisitApplication.query.count()

        if statistic_type == 'overview':
            # 概览统计
            today = datetime.utcnow().date()

            # 时间段统计
            today_visits = VisitRecord.query.filter(
                func.date(VisitRecord.entry_time) == today
            ).count()

            week_start = today - timedelta(days=today.weekday())
            week_visits = VisitRecord.query.filter(
                func.date(VisitRecord.entry_time) >= week_start
            ).count()

            month_start = today.replace(day=1)
            month_visits = VisitRecord.query.filter(
                func.date(VisitRecord.entry_time) >= month_start
            ).count()

            year_start = today.replace(month=1, day=1)
            year_visits = VisitRecord.query.filter(
                func.date(VisitRecord.entry_time) >= year_start
            ).count()

            # 按状态统计申请
            application_stats = db.session.query(
                VisitApplication.application_status,
                func.count(VisitApplication.id).label('count')
            ).group_by(VisitApplication.application_status).all()

            # 按学部统计校友
            division_stats = db.session.query(
                AlumniProfile.division,
                func.count(AlumniProfile.id).label('count')
            ).join(User).filter(
                User.user_type == 'alumni',
                AlumniProfile.approval_status == 'approved'
            ).group_by(AlumniProfile.division).order_by(
                func.count(AlumniProfile.id).desc()
            ).limit(10).all()

            # 按年级统计校友
            grade_stats = db.session.query(
                AlumniProfile.graduation_year,
                func.count(AlumniProfile.id).label('count')
            ).join(User).filter(
                User.user_type == 'alumni',
                AlumniProfile.approval_status == 'approved'
            ).group_by(AlumniProfile.graduation_year).order_by(
                AlumniProfile.graduation_year.desc()
            ).all()

            return jsonify({
                'time_statistics': {
                    'today_visits': today_visits,
                    'week_visits': week_visits,
                    'month_visits': month_visits,
                    'year_visits': year_visits,
                    'total_visits': total_visits
                },
                'application_stats': [{'status': stat.application_status, 'count': stat.count} for stat in application_stats],
                'division_stats': [{'division': stat.division, 'count': stat.count} for stat in division_stats],
                'grade_stats': [{'year': stat.graduation_year, 'count': stat.count} for stat in grade_stats],
                'total_applications': total_applications
            }), 200

        elif statistic_type == 'visits':
            # 访问详细统计
            # 按受访人统计
            target_person_stats = db.session.query(
                VisitApplication.target_person,
                func.count(VisitApplication.id).label('count')
            ).filter(
                VisitApplication.application_status.in_(['approved', 'completed'])
            ).group_by(VisitApplication.target_person).order_by(
                func.count(VisitApplication.id).desc()
            ).limit(20).all()

            # 按访问人统计
            visitor_stats = db.session.query(
                User.real_name,
                func.count(VisitApplication.id).label('count')
            ).join(VisitApplication).filter(
                VisitApplication.application_status.in_(['approved', 'completed'])
            ).group_by(User.real_name).order_by(
                func.count(VisitApplication.id).desc()
            ).limit(20).all()

            # 按审批人统计
            approver_stats = db.session.query(
                User.real_name,
                func.count(VisitApplication.id).label('count')
            ).join(VisitApplication, User.id == VisitApplication.approved_by).filter(
                VisitApplication.application_status.in_(['approved', 'completed'])
            ).group_by(User.real_name).order_by(
                func.count(VisitApplication.id).desc()
            ).limit(20).all()

            # 按放行人统计（保安）
            security_stats = db.session.query(
                User.real_name,
                func.count(VisitRecord.id).label('count')
            ).join(VisitRecord).filter(
                User.user_type == 'security'
            ).group_by(User.real_name).order_by(
                func.count(VisitRecord.id).desc()
            ).limit(20).all()

            # 按访问目的统计
            purpose_stats = db.session.query(
                VisitApplication.visit_purpose,
                func.count(VisitApplication.id).label('count')
            ).filter(
                VisitApplication.application_status.in_(['approved', 'completed'])
            ).group_by(VisitApplication.visit_purpose).order_by(
                func.count(VisitApplication.id).desc()
            ).all()

            return jsonify({
                'target_person_stats': [{'name': stat.target_person, 'count': stat.count} for stat in target_person_stats],
                'visitor_stats': [{'name': stat.real_name, 'count': stat.count} for stat in visitor_stats],
                'approver_stats': [{'name': stat.real_name, 'count': stat.count} for stat in approver_stats],
                'security_stats': [{'name': stat.real_name, 'count': stat.count} for stat in security_stats],
                'purpose_stats': [{'purpose': stat.visit_purpose, 'count': stat.count} for stat in purpose_stats]
            }), 200

        elif statistic_type == 'people':
            # 人员统计
            # 按班级统计校友
            class_stats = db.session.query(
                AlumniProfile.class_name,
                func.count(AlumniProfile.id).label('count')
            ).join(User).filter(
                User.user_type == 'alumni',
                AlumniProfile.approval_status == 'approved'
            ).group_by(AlumniProfile.class_name).order_by(
                func.count(AlumniProfile.id).desc()
            ).limit(20).all()

            # 按年级和班级统计
            grade_class_stats = db.session.query(
                AlumniProfile.graduation_year,
                AlumniProfile.class_name,
                func.count(AlumniProfile.id).label('count')
            ).join(User).filter(
                User.user_type == 'alumni',
                AlumniProfile.approval_status == 'approved'
            ).group_by(
                AlumniProfile.graduation_year,
                AlumniProfile.class_name
            ).order_by(
                AlumniProfile.graduation_year.desc(),
                func.count(AlumniProfile.id).desc()
            ).limit(30).all()

            return jsonify({
                'class_stats': [{'class_name': stat.class_name, 'count': stat.count} for stat in class_stats],
                'grade_class_stats': [
                    {
                        'graduation_year': stat.graduation_year,
                        'class_name': stat.class_name,
                        'count': stat.count
                    } for stat in grade_class_stats
                ]
            }), 200

        
        else:
            return jsonify({'error': '统计类型无效'}), 400

    except Exception as e:
        current_app.logger.error(f"获取统计数据失败: {str(e)}")
        return jsonify({'error': '获取统计数据失败', 'details': str(e)}), 500