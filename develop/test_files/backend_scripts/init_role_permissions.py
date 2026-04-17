#!/usr/bin/env python3
"""
初始化角色和权限系统
基于校园访问系统的合理权限设计
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.organization import UserRole, UserRoleAssignment

def init_roles_and_permissions():
    """初始化角色和权限"""

    app = create_app()
    with app.app_context():
        print("正在初始化角色和权限系统...")

        # 定义角色和权限
        roles_data = [
            {
                'name': 'visitable_teacher',
                'display_name': '可拜访教师',
                'description': '可以作为被拜访对象的教师',
                'permissions': ['be_visitable', 'receive_visits']
            },
            {
                'name': 'alumni_organizer',
                'display_name': '校友活动组织者',
                'description': '可以组织校友活动并审批相关访问申请',
                'permissions': ['organize_alumni_activities', 'approve_alumni_visits', 'manage_events']
            },
            {
                'name': 'club_manager',
                'display_name': '社团管理员',
                'description': '管理社团相关事务和活动',
                'permissions': ['manage_club_activities', 'approve_club_visits', 'manage_club_events']
            },
            {
                'name': 'visit_approver',
                'display_name': '访问审批人',
                'description': '可以审批特定类型的访问申请',
                'permissions': ['approve_visits', 'manage_visit_schedule']
            },
            {
                'name': 'event_manager',
                'display_name': '活动管理员',
                'description': '管理和审批校园活动',
                'permissions': ['manage_events', 'approve_event_visits', 'manage_event_resources']
            }
        ]

        # 创建角色
        created_roles = {}
        for role_data in roles_data:
            existing_role = UserRole.query.filter_by(name=role_data['name']).first()
            if not existing_role:
                role = UserRole(
                    name=role_data['name'],
                    display_name=role_data['display_name'],
                    description=role_data['description'],
                    permissions=str(role_data['permissions'])
                )
                db.session.add(role)
                created_roles[role_data['name']] = role
                print(f"创建角色: {role_data['display_name']}")
            else:
                created_roles[role_data['name']] = existing_role
                print(f"角色已存在: {role_data['display_name']}")

        # 为现有用户分配合适的角色
        users = User.query.all()
        for user in users:
            roles_to_assign = []

            # 教师用户：自动分配可拜访教师角色
            if user.user_type == 'teacher' and user.is_visitable:
                roles_to_assign.append('visitable_teacher')

            # 根据用户名模拟分配角色（实际应用中应该有更复杂的逻辑）
            if 'admin' in user.username.lower():
                # 管理员用户：获得所有权限
                roles_to_assign.extend(['alumni_organizer', 'club_manager', 'visit_approver', 'event_manager'])
            elif 'organizer' in user.username.lower():
                # 活动组织者
                roles_to_assign.extend(['alumni_organizer', 'event_manager'])
            elif 'club' in user.username.lower():
                # 社团相关
                roles_to_assign.extend(['club_manager'])

            # 分配角色
            for role_name in roles_to_assign:
                if role_name in created_roles:
                    # 检查是否已分配
                    existing_assignment = UserRoleAssignment.query.filter_by(
                        user_id=user.id,
                        role_id=created_roles[role_name].id
                    ).first()

                    if not existing_assignment:
                        assignment = UserRoleAssignment(
                            user_id=user.id,
                            role_id=created_roles[role_name].id,
                            status='active'
                        )
                        db.session.add(assignment)
                        print(f"为用户 {user.real_name} 分配角色: {created_roles[role_name].display_name}")

        try:
            db.session.commit()
            print(f"\n=== 初始化完成 ===")
            print(f"创建了 {len(roles_data)} 个角色")

            # 显示统计
            total_assignments = UserRoleAssignment.query.count()
            active_assignments = UserRoleAssignment.query.filter_by(status='active').count()
            print(f"角色分配总数: {total_assignments}")
            print(f"活跃角色分配: {active_assignments}")

        except Exception as e:
            db.session.rollback()
            print(f"初始化失败: {str(e)}")
            return

def show_role_statistics():
    """显示角色统计信息"""
    app = create_app()
    with app.app_context():
        print("=== 角色统计信息 ===")

        # 角色统计
        roles = UserRole.query.all()
        for role in roles:
            assignments = UserRoleAssignment.query.filter_by(
                role_id=role.id,
                status='active'
            ).count()
            print(f"{role.display_name}: {assignments} 个用户")

        # 用户权限统计
        users_with_roles = db.session.query(User.id).join(UserRoleAssignment).distinct().count()
        total_users = User.query.count()
        print(f"\n拥有角色的用户: {users_with_roles}/{total_users}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        show_role_statistics()
    else:
        init_roles_and_permissions()
        print("\n" + "="*50)
        show_role_statistics()