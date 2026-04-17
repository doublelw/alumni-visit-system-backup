"""
组织管理页面路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.organization import Organization, UserRole

admin_organization_bp = Blueprint('admin_organization', __name__)

@admin_organization_bp.route('/admin/organization')
def admin_organization_page():
    """组织管理页面"""
    return render_template('admin/organization.html')

@admin_organization_bp.route('/admin/organization/stats')
@jwt_required()
def get_organization_stats():
    """获取组织统计信息"""
    try:
        # 总组织数
        total_orgs = Organization.query.count()

        # 总用户数
        total_users = User.query.count()

        # 总角色数
        total_roles = UserRole.query.count()

        # 教师数量
        total_teachers = User.query.filter_by(user_type='teacher').count()

        # 可拜访教师数量
        visitable_teachers = User.query.filter_by(
            user_type='teacher',
            status='active',
            is_visitable=True
        ).count()

        # 按组织类型统计
        org_types = {}
        for org in Organization.query.all():
            org_type = org.org_type
            if org_type not in org_types:
                org_types[org_type] = 0
            org_types[org_type] += 1

        # 按用户类型统计
        user_types = {}
        for user in User.query.all():
            user_type = user.user_type
            if user_type not in user_types:
                user_types[user_type] = 0
            user_types[user_type] += 1

        return jsonify({
            'success': True,
            'data': {
                'total_orgs': total_orgs,
                'total_users': total_users,
                'total_roles': total_roles,
                'total_teachers': total_teachers,
                'visitable_teachers': visitable_teachers,
                'org_types': org_types,
                'user_types': user_types
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500

@admin_organization_bp.route('/admin/organization/users')
@jwt_required()
def get_organization_users():
    """获取组织用户列表"""
    try:
        org_id = request.args.get('org_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = User.query
        if org_id:
            query = query.filter_by(organization_id=org_id)

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        users_data = []
        for user in pagination.items:
            user_data = user.to_dict()
            if user.organization:
                user_data['organization_name'] = user.organization.name
            users_data.append(user_data)

        return jsonify({
            'success': True,
            'data': {
                'users': users_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500