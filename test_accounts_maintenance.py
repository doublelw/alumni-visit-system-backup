#!/usr/bin/env python3
"""
测试账号关系维护脚本
"""

import sys
import os
import uuid
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
import bcrypt

def setup_test_accounts():
    """设置完整的测试账号关系网络"""

    app = create_app()

    with app.app_context():
        print("开始检查和维护测试账号关系...")

        # 定义测试账号数据
        test_accounts = {
            # 管理员
            'admin': {
                'username': 'admin',
                'real_name': '系统管理员',
                'email': 'admin@school.edu.cn',
                'phone': '13800000000',
                'user_type': 'admin',
                'employee_id': 'ADMIN001'
            },

            # 保安
            'security': {
                'username': 'security001',
                'real_name': '保安张三',
                'email': 'zhangsan@security.edu.cn',
                'phone': '13800000001',
                'user_type': 'security',
                'employee_id': 'SEC001'
            },

            # 教师
            'teacher1': {
                'username': 'teacher001',
                'real_name': '李老师',
                'email': 'liteacher@school.edu.cn',
                'phone': '13800000002',
                'user_type': 'teacher',
                'employee_id': 'TCH001',
                'class_id': '高三1班',
                'is_class_teacher': True
            },
            'teacher2': {
                'username': 'teacher002',
                'real_name': '王老师',
                'email': 'wangteacher@school.edu.cn',
                'phone': '13800000003',
                'user_type': 'teacher',
                'employee_id': 'TCH002',
                'class_id': '高三2班',
                'is_class_teacher': True
            },

            # 学生
            'student1': {
                'username': 'student001',
                'real_name': '张小明',
                'email': 'zhangxiaoming@student.edu.cn',
                'phone': '13800000004',
                'user_type': 'student',
                'student_id': 'STU001',
                'class_id': '高三1班',
                'grade': '高三'
            },
            'student2': {
                'username': 'student002',
                'real_name': '李小华',
                'email': 'lixiaohua@student.edu.cn',
                'phone': '13800000005',
                'user_type': 'student',
                'student_id': 'STU002',
                'class_id': '高三1班',
                'grade': '高三'
            },
            'student3': {
                'username': 'student003',
                'real_name': '王小红',
                'email': 'wangxiaohong@student.edu.cn',
                'phone': '13800000006',
                'user_type': 'student',
                'student_id': 'STU003',
                'class_id': '高三2班',
                'grade': '高三'
            },

            # 家长
            'parent1': {
                'username': 'parent001',
                'real_name': '张父',
                'email': 'zhangfu@parent.edu.cn',
                'phone': '13800000007',
                'user_type': 'parent'
            },
            'parent2': {
                'username': 'parent002',
                'real_name': '李母',
                'email': 'limu@parent.edu.cn',
                'phone': '13800000008',
                'user_type': 'parent'
            }
        }

        created_users = {}

        # 创建或更新用户
        for key, user_data in test_accounts.items():
            user = User.query.filter_by(username=user_data['username']).first()

            if not user:
                print(f"创建新用户: {user_data['real_name']} ({user_data['username']})")
                user = User(
                    uuid=str(uuid.uuid4()),
                    username=user_data['username'],
                    real_name=user_data['real_name'],
                    email=user_data['email'],
                    phone=user_data['phone'],
                    user_type=user_data['user_type'],
                    status='active'
                )

                # 设置密码
                password = 'test123456'
                user.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            else:
                print(f"更新用户: {user_data['real_name']} ({user_data['username']})")
                user.real_name = user_data['real_name']
                user.email = user_data['email']
                user.phone = user_data['phone']
                user.user_type = user_data['user_type']
                user.status = 'active'

            # 设置特有字段
            if 'employee_id' in user_data:
                user.employee_id = user_data['employee_id']
            if 'student_id' in user_data:
                user.student_id = user_data['student_id']
            if 'class_id' in user_data:
                user.class_id = user_data['class_id']
            if 'grade' in user_data:
                user.grade = user_data['grade']
            if 'is_class_teacher' in user_data:
                user.is_class_teacher = user_data['is_class_teacher']

            db.session.add(user)
            db.session.commit()
            created_users[key] = user

        # 建立关系
        print("\n建立用户关系...")

        # 家长-学生关系
        # 张父是张小明和李小华的家长
        created_users['parent1'].parent_student_id = created_users['student1'].id
        created_users['student1'].student_parent_id = created_users['parent1'].id

        created_users['parent1'].parent_student_id = created_users['student2'].id
        created_users['student2'].student_parent_id = created_users['parent1'].id

        # 李母是王小红的家长
        created_users['parent2'].parent_student_id = created_users['student3'].id
        created_users['student3'].student_parent_id = created_users['parent2'].id

        db.session.commit()

        print("\n测试账号关系设置完成！")
        print("\n账号信息汇总:")
        print("=" * 50)

        # 管理员
        print(f"管理员: admin / test123456")

        # 保安
        print(f"保安: security001 / test123456")

        # 教师
        print(f"教师1 (高三1班班主任): teacher001 / test123456")
        print(f"教师2 (高三2班班主任): teacher002 / test123456")

        # 学生
        print(f"学生1 (高三1班): student001 / test123456")
        print(f"学生2 (高三1班): student002 / test123456")
        print(f"学生3 (高三2班): student003 / test123456")

        # 家长
        print(f"家长1 (张小明+李小华的父亲): parent001 / test123456")
        print(f"家长2 (王小红的母亲): parent002 / test123456")

        print("\n关系说明:")
        print("- 李老师 (teacher001) 是高三1班班主任，可以管理张小明和李小华")
        print("- 王老师 (teacher002) 是高三2班班主任，可以管理王小红")
        print("- 张父 (parent001) 是张小明和李小华的家长")
        print("- 李母 (parent002) 是王小红的家长")

        print("\n功能测试场景:")
        print("- 李老师可以为高三1班的学生申请出校")
        print("- 张父可以为张小明和李小华申请出校")
        print("- 学生可以为自己申请出校")
        print("- 紧急联系人会自动填充为对应家长信息")

def show_current_relations():
    """显示当前的用户关系"""

    app = create_app()

    with app.app_context():
        print("当前数据库中的用户关系:")
        print("=" * 50)

        users = User.query.filter(
            User.user_type.in_(['student', 'parent', 'teacher'])
        ).order_by(User.user_type, User.real_name).all()

        for user in users:
            type_icon = {
                'teacher': '[教师]',
                'student': '[学生]',
                'parent': '[家长]'
            }.get(user.user_type, '[用户]')

            print(f"{type_icon} {user.real_name} ({user.username}) - {user.user_type}")

            if user.user_type == 'student':
                if user.student_parent_id:
                    parent = User.query.get(user.student_parent_id)
                    if parent:
                        print(f"    └─ 家长: {parent.real_name} ({parent.username})")
                class_name = getattr(user, 'class_name', None)
                if class_name:
                    print(f"    └─ 班级: {class_name}")

            elif user.user_type == 'parent':
                # 查找这个家长的孩子
                children = User.query.filter_by(student_parent_id=user.id).all()
                for child in children:
                    child_class = getattr(child, 'class_name', '未分班')
                    print(f"    └─ 孩子: {child.real_name} ({child.username}) - {child_class}")

            elif user.user_type == 'teacher':
                class_name = getattr(user, 'class_name', None)
                if class_name:
                    print(f"    └─ 负责班级: {class_name}")
                    # 查找这个班级的学生
                    students = User.query.filter(
                        User.user_type == 'student',
                        getattr(User, 'class_name', None) == class_name
                    ).all()
                    for student in students:
                        print(f"        └─ 学生: {student.real_name} ({student.username})")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='测试账号关系维护工具')
    parser.add_argument('--show', action='store_true', help='显示当前关系')
    parser.add_argument('--setup', action='store_true', help='设置测试账号')

    args = parser.parse_args()

    if args.show:
        show_current_relations()
    elif args.setup:
        setup_test_accounts()
    else:
        print("用法:")
        print("  python test_accounts_maintenance.py --show   # 显示当前关系")
        print("  python test_accounts_maintenance.py --setup  # 设置测试账号")