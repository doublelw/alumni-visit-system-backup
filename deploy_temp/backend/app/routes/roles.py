"""
角色和权限管理API
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.organization import UserRole, UserRoleAssignment

roles_bp = Blueprint('roles', __name__)

def check_admin_permission():
    """检查管理员权限"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.user_type != 'admin':
        return False
    return True

@roles_bp.route('', methods=['GET'])
@jwt_required()
def get_roles():
    """获取所有角色列表"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以查看角色'
            }), 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')

        query = UserRole.query

        if search:
            query = query.filter(
                UserRole.name.contains(search) |
                UserRole.display_name.contains(search) |
                UserRole.description.contains(search)
            )

        query = query.order_by(UserRole.created_at.desc())

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'data': {
                'roles': [role.to_dict() for role in pagination.items],
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
            'message': f'获取角色列表失败: {str(e)}'
        }), 500

@roles_bp.route('/<int:role_id>', methods=['GET'])
@jwt_required()
def get_role(role_id):
    """获取单个角色详情"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以查看角色详情'
            }), 403

        role = UserRole.query.get_or_404(role_id)

        # 获取角色分配的用户
        assignments = UserRoleAssignment.query.filter_by(
            role_id=role_id,
            status='active'
        ).all()

        users = []
        for assignment in assignments:
            if assignment.user:
                user_data = assignment.user.to_dict()
                user_data['assigned_at'] = assignment.assigned_at.isoformat() if assignment.assigned_at else None
                users.append(user_data)

        role_data = role.to_dict()
        role_data['users'] = users
        role_data['user_count'] = len(users)

        return jsonify({
            'success': True,
            'data': role_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取角色详情失败: {str(e)}'
        }), 500

@roles_bp.route('', methods=['POST'])
@jwt_required()
def create_role():
    """创建新角色"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以创建角色'
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

        # 检查角色名是否已存在
        existing_role = UserRole.query.filter_by(name=data['name']).first()
        if existing_role:
            return jsonify({
                'success': False,
                'message': f'角色名 {data["name"]} 已存在'
            }), 400

        # 创建新角色
        role = UserRole(
            name=data['name'],
            display_name=data['display_name'],
            description=data.get('description', ''),
            permissions=str(data.get('permissions', [])),
            status='active'
        )

        db.session.add(role)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '角色创建成功',
            'data': role.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建角色失败: {str(e)}'
        }), 500

@roles_bp.route('/<int:role_id>', methods=['PUT'])
@jwt_required()
def update_role(role_id):
    """更新角色信息"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以更新角色'
            }), 403

        role = UserRole.query.get_or_404(role_id)
        data = request.get_json()

        # 更新字段
        if 'display_name' in data:
            role.display_name = data['display_name']
        if 'description' in data:
            role.description = data['description']
        if 'permissions' in data:
            role.permissions = str(data['permissions'])
        if 'status' in data:
            role.status = data['status']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '角色更新成功',
            'data': role.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新角色失败: {str(e)}'
        }), 500

@roles_bp.route('/<int:role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(role_id):
    """删除角色（软删除）"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以删除角色'
            }), 403

        role = UserRole.query.get_or_404(role_id)

        # 软删除：标记为非活跃
        role.status = 'inactive'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '角色删除成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除角色失败: {str(e)}'
        }), 500

@roles_bp.route('/assign', methods=['POST'])
@jwt_required()
def assign_role():
    """为用户分配角色"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以分配角色'
            }), 403

        data = request.get_json()

        # 验证必填字段
        required_fields = ['user_id', 'role_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400

        # 检查是否已分配
        existing_assignment = UserRoleAssignment.query.filter_by(
            user_id=data['user_id'],
            role_id=data['role_id'],
            status='active'
        ).first()

        if existing_assignment:
            return jsonify({
                'success': False,
                'message': '该用户已分配此角色'
            }), 400

        # 创建角色分配
        assignment = UserRoleAssignment(
            user_id=data['user_id'],
            role_id=data['role_id'],
            organization_id=data.get('organization_id'),
            assigned_by=get_jwt_identity()
        )

        db.session.add(assignment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '角色分配成功',
            'data': assignment.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'角色分配失败: {str(e)}'
        }), 500

@roles_bp.route('/unassign', methods=['POST'])
@jwt_required()
def unassign_role():
    """取消用户角色分配"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以取消角色分配'
            }), 403

        data = request.get_json()

        # 验证必填字段
        required_fields = ['user_id', 'role_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400

        # 查找分配记录
        assignment = UserRoleAssignment.query.filter_by(
            user_id=data['user_id'],
            role_id=data['role_id'],
            status='active'
        ).first()

        if not assignment:
            return jsonify({
                'success': False,
                'message': '未找到该用户的角色分配'
            }), 404

        # 软删除：标记为非活跃
        assignment.status = 'inactive'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '角色分配已取消'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'取消角色分配失败: {str(e)}'
        }), 500

@roles_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_roles(user_id):
    """获取用户的角色列表"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以查看用户角色'
            }), 403

        user = User.query.get_or_404(user_id)

        # 获取用户的活跃角色
        assignments = UserRoleAssignment.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()

        roles = []
        for assignment in assignments:
            if assignment.role:
                role_data = assignment.role.to_dict()
                role_data['assigned_at'] = assignment.assigned_at.isoformat() if assignment.assigned_at else None
                role_data['organization'] = assignment.organization.to_dict() if assignment.organization else None
                roles.append(role_data)

        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'roles': roles
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户角色失败: {str(e)}'
        }), 500

@roles_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_role_stats():
    """获取角色统计信息"""
    try:
        if not check_admin_permission():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以查看角色统计'
            }), 403

        # 统计信息
        total_roles = UserRole.query.count()
        active_roles = UserRole.query.filter_by(status='active').count()
        total_assignments = UserRoleAssignment.query.count()
        active_assignments = UserRoleAssignment.query.filter_by(status='active').count()

        # 按角色统计
        role_stats = []
        roles = UserRole.query.filter_by(status='active').all()
        for role in roles:
            user_count = UserRoleAssignment.query.filter_by(
                role_id=role.id,
                status='active'
            ).count()
            role_stats.append({
                'role': role.to_dict(),
                'user_count': user_count
            })

        return jsonify({
            'success': True,
            'data': {
                'total_roles': total_roles,
                'active_roles': active_roles,
                'total_assignments': total_assignments,
                'active_assignments': active_assignments,
                'role_stats': role_stats
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取角色统计失败: {str(e)}'
        }), 500