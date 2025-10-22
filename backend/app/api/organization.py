"""
组织管理API
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.organization import Organization, UserRole, UserRoleAssignment
from datetime import datetime

organization_bp = Blueprint('organization', __name__, url_prefix='/api/organization')

def check_permission(permission):
    """检查用户权限"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return False

    # 超级管理员拥有所有权限
    if user.user_type == 'admin':
        return True

    # 检查用户角色权限
    for assignment in user.role_assignments:
        if assignment.status == 'active' and assignment.role and assignment.role.has_permission(permission):
            return True

    return False

@organization_bp.route('/tree', methods=['GET'])
@jwt_required()
def get_organization_tree():
    """获取组织架构树"""
    try:
        tree = Organization.get_tree()
        return jsonify({
            'success': True,
            'data': tree
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取组织架构失败: {str(e)}'
        }), 500

@organization_bp.route('/list', methods=['GET'])
@jwt_required()
def get_organizations():
    """获取组织列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        parent_id = request.args.get('parent_id', type=int)
        org_type = request.args.get('org_type')
        status = request.args.get('status', 'active')

        query = Organization.query

        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)
        if org_type:
            query = query.filter_by(org_type=org_type)
        if status:
            query = query.filter_by(status=status)

        query = query.order_by(Organization.level, Organization.sort_order, Organization.name)

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'data': {
                'organizations': [org.to_dict(include_children=False) for org in pagination.items],
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
            'message': f'获取组织列表失败: {str(e)}'
        }), 500

@organization_bp.route('/<int:org_id>', methods=['GET'])
@jwt_required()
def get_organization(org_id):
    """获取组织详情"""
    try:
        organization = Organization.query.get_or_404(org_id)

        # 获取子组织
        children = Organization.query.filter_by(parent_id=org_id, status='active')\
                                  .order_by(Organization.sort_order, Organization.name).all()

        # 获取组织用户
        users = User.query.filter_by(organization_id=org_id).all()

        return jsonify({
            'success': True,
            'data': {
                'organization': organization.to_dict(),
                'children': [child.to_dict() for child in children],
                'users': [user.to_dict() for user in users],
                'user_count': len(users)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取组织详情失败: {str(e)}'
        }), 500

@organization_bp.route('', methods=['POST'])
@jwt_required()
def create_organization():
    """创建组织"""
    try:
        if not check_permission('org_management'):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403

        data = request.get_json()

        # 验证必填字段
        required_fields = ['name', 'code', 'org_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400

        # 检查代码是否已存在
        if Organization.query.filter_by(code=data['code']).first():
            return jsonify({
                'success': False,
                'message': '组织代码已存在'
            }), 400

        # 创建组织
        organization = Organization(
            name=data['name'],
            code=data['code'],
            description=data.get('description'),
            parent_id=data.get('parent_id'),
            org_type=data['org_type'],
            status=data.get('status', 'active'),
            sort_order=data.get('sort_order', 0),
            contact_person=data.get('contact_person'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email'),
            address=data.get('address'),
            created_by=get_jwt_identity()
        )

        # 设置路径和层级
        organization.before_save()

        db.session.add(organization)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '组织创建成功',
            'data': organization.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建组织失败: {str(e)}'
        }), 500

@organization_bp.route('/<int:org_id>', methods=['PUT'])
@jwt_required()
def update_organization(org_id):
    """更新组织"""
    try:
        if not check_permission('org_management'):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403

        organization = Organization.query.get_or_404(org_id)
        data = request.get_json()

        # 验证代码唯一性（如果要修改代码）
        if 'code' in data and data['code'] != organization.code:
            if Organization.query.filter_by(code=data['code']).first():
                return jsonify({
                    'success': False,
                    'message': '组织代码已存在'
                }), 400

        # 更新字段
        updatable_fields = [
            'name', 'code', 'description', 'parent_id', 'org_type',
            'status', 'sort_order', 'contact_person', 'contact_phone',
            'contact_email', 'address'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(organization, field, data[field])

        # 如果修改了父级组织，需要重新计算路径和层级
        if 'parent_id' in data and data['parent_id'] != organization.parent_id:
            organization.before_save()

        organization.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '组织更新成功',
            'data': organization.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新组织失败: {str(e)}'
        }), 500

@organization_bp.route('/<int:org_id>', methods=['DELETE'])
@jwt_required()
def delete_organization(org_id):
    """删除组织"""
    try:
        if not check_permission('org_management'):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403

        organization = Organization.query.get_or_404(org_id)

        # 检查是否有子组织
        children_count = Organization.query.filter_by(parent_id=org_id).count()
        if children_count > 0:
            return jsonify({
                'success': False,
                'message': '该组织下还有子组织，无法删除'
            }), 400

        # 检查是否有用户
        users_count = User.query.filter_by(organization_id=org_id).count()
        if users_count > 0:
            return jsonify({
                'success': False,
                'message': f'该组织下还有 {users_count} 个用户，无法删除'
            }), 400

        # 软删除：标记为inactive
        organization.status = 'inactive'
        organization.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '组织删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除组织失败: {str(e)}'
        }), 500

@organization_bp.route('/types', methods=['GET'])
@jwt_required()
def get_organization_types():
    """获取组织类型列表"""
    try:
        types = [
            {'value': 'school', 'label': '学校'},
            {'value': 'campus', 'label': '校区'},
            {'value': 'college', 'label': '学院'},
            {'value': 'department', 'label': '部门'},
            {'value': 'class', 'label': '班级'},
            {'value': 'club', 'label': '社团'},
            {'value': 'office', 'label': '办公室'},
            {'value': 'other', 'label': '其他'}
        ]

        return jsonify({
            'success': True,
            'data': types
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取组织类型失败: {str(e)}'
        }), 500

# 角色管理API
@organization_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """获取角色列表"""
    try:
        roles = UserRole.query.filter_by(status='active').all()
        return jsonify({
            'success': True,
            'data': [role.to_dict() for role in roles]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取角色列表失败: {str(e)}'
        }), 500

@organization_bp.route('/roles', methods=['POST'])
@jwt_required()
def create_role():
    """创建角色"""
    try:
        if not check_permission('org_management'):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403

        data = request.get_json()

        # 验证必填字段
        required_fields = ['name', 'display_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400

        # 检查名称是否已存在
        if UserRole.query.filter_by(name=data['name']).first():
            return jsonify({
                'success': False,
                'message': '角色名称已存在'
            }), 400

        # 创建角色
        role = UserRole(
            name=data['name'],
            display_name=data['display_name'],
            description=data.get('description'),
            permissions=str(data.get('permissions', [])),
            status=data.get('status', 'active'),
            created_by=get_jwt_identity()
        )

        db.session.add(role)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '角色创建成功',
            'data': role.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建角色失败: {str(e)}'
        }), 500

@organization_bp.route('/users/<int:user_id>/roles', methods=['GET'])
@jwt_required()
def get_user_roles(user_id):
    """获取用户角色"""
    try:
        user = User.query.get_or_404(user_id)

        assignments = UserRoleAssignment.query.filter_by(
            user_id=user_id, status='active'
        ).all()

        roles_data = []
        for assignment in assignments:
            role_data = assignment.to_dict()
            if assignment.organization:
                role_data['organization_name'] = assignment.organization.name
            roles_data.append(role_data)

        return jsonify({
            'success': True,
            'data': roles_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户角色失败: {str(e)}'
        }), 500

@organization_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@jwt_required()
def assign_user_role(user_id):
    """分配用户角色"""
    try:
        if not check_permission('user_management'):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403

        user = User.query.get_or_404(user_id)
        data = request.get_json()

        role_id = data.get('role_id')
        organization_id = data.get('organization_id')

        if not role_id:
            return jsonify({
                'success': False,
                'message': '缺少角色ID'
            }), 400

        # 检查角色是否存在
        role = UserRole.query.get(role_id)
        if not role:
            return jsonify({
                'success': False,
                'message': '角色不存在'
            }), 404

        # 检查是否已经分配过相同角色
        existing = UserRoleAssignment.query.filter_by(
            user_id=user_id, role_id=role_id, organization_id=organization_id, status='active'
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'message': '用户已分配该角色'
            }), 400

        # 创建角色分配
        assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
            assigned_by=get_jwt_identity()
        )

        db.session.add(assignment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '角色分配成功',
            'data': assignment.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'角色分配失败: {str(e)}'
        }), 500

@organization_bp.route('/users/<int:user_id>/roles/<int:assignment_id>', methods=['DELETE'])
@jwt_required()
def revoke_user_role(user_id, assignment_id):
    """撤销用户角色"""
    try:
        if not check_permission('user_management'):
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403

        assignment = UserRoleAssignment.query.get_or_404(assignment_id)

        if assignment.user_id != user_id:
            return jsonify({
                'success': False,
                'message': '角色分配不匹配'
            }), 400

        # 软删除：标记为inactive
        assignment.status = 'inactive'

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '角色撤销成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'角色撤销失败: {str(e)}'
        }), 500

@organization_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_organization_stats():
    """获取组织统计信息"""
    try:
        # 统计各类型组织数量
        org_types = ['school', 'campus', 'graduation_year', 'class', 'club', 'office']
        stats = {}

        for org_type in org_types:
            count = Organization.query.filter_by(org_type=org_type, status='active').count()
            type_name = {
                'school': '学校',
                'campus': '校区',
                'graduation_year': '毕业年份',
                'class': '班级',
                'club': '社团',
                'office': '办公室'
            }.get(org_type, org_type)
            stats[org_type] = {
                'name': type_name,
                'count': count
            }

        # 总组织数
        total_orgs = Organization.query.filter_by(status='active').count()

        # 统计用户分布
        users_with_org = User.query.filter(User.organization_id.isnot(None)).count()
        total_users = User.query.count()

        return jsonify({
            'success': True,
            'data': {
                'total_organizations': total_orgs,
                'organization_types': stats,
                'users_with_organization': users_with_org,
                'total_users': total_users,
                'organization_coverage': round(users_with_org / total_users * 100, 1) if total_users > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取组织统计失败: {str(e)}'
        }), 500