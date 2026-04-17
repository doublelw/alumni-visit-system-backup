#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试用户账户脚本
用于快速创建各类测试账户
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app import create_app, db
from backend.app.models import User, AlumniProfile
import time

def create_admin_account():
    """创建管理员账户"""
    print("👨‍💼 创建管理员账户...")

    admin_data = {
        'username': 'admin',
        'password': 'admin123',
        'real_name': '系统管理员',
        'email': 'admin@school.edu.cn',
        'phone': '13800000000',
        'user_type': 'admin',
        'status': 'active'
    }

    app = create_app()
    with app.app_context():
        # 检查管理员账户是否存在
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("⚠️  管理员账户已存在，跳过创建")
            return admin

        # 创建管理员账户
        admin = User(
            username=admin_data['username'],
            real_name=admin_data['real_name'],
            email=admin_data['email'],
            phone=admin_data['phone'],
            user_type=admin_data['user_type'],
            status=admin_data['status']
        )
        admin.set_password(admin_data['password'])

        db.session.add(admin)
        db.session.commit()

        print("✅ 管理员账户创建成功")
        print(f"   用户名: {admin_data['username']}")
        print(f"   密码: {admin_data['password']}")
        print(f"   类型: {admin_data['user_type']}")

        return admin

def create_teacher_accounts():
    """创建教师测试账户"""
    print("\n👨‍🏫 创建教师测试账户...")

    teachers = [
        {
            'username': 'teacher001',
            'password': 'teacher123',
            'real_name': '测试教师一',
            'email': 'teacher1@school.edu.cn',
            'phone': '13800000001'
        },
        {
            'username': 'teacher002',
            'password': 'teacher123',
            'real_name': '测试教师二',
            'email': 'teacher2@school.edu.cn',
            'phone': '13800000002'
        }
    ]

    app = create_app()
    with app.app_context():
        created_count = 0

        for teacher_data in teachers:
            # 检查教师账户是否存在
            teacher = User.query.filter_by(username=teacher_data['username']).first()
            if teacher:
                print(f"⚠️  教师账户 {teacher_data['username']} 已存在，跳过创建")
                continue

            # 创建教师账户
            teacher = User(
                username=teacher_data['username'],
                real_name=teacher_data['real_name'],
                email=teacher_data['email'],
                phone=teacher_data['phone'],
                user_type='teacher',
                status='active'
            )
            teacher.set_password(teacher_data['password'])

            db.session.add(teacher)
            created_count += 1
            print(f"✅ 创建教师账户: {teacher_data['username']}")

        db.session.commit()
        print(f"\n📊 教师账户创建完成，共创建 {created_count} 个账户")

        if created_count > 0:
            print("\n教师账户信息:")
            for teacher_data in teachers:
                print(f"   用户名: {teacher_data['username']}")
                print(f"   密码: {teacher_data['password']}")
                print(f"   姓名: {teacher_data['real_name']}")
                print(f"   ---")

def create_security_accounts():
    """创建保安测试账户"""
    print("\n👮‍♂️ 创建保安测试账户...")

    security_users = [
        {
            'username': 'security001',
            'password': 'security123',
            'real_name': '测试保安一',
            'email': 'security1@school.edu.cn',
            'phone': '13800000011'
        },
        {
            'username': 'security002',
            'password': 'security123',
            'real_name': '测试保安二',
            'email': 'security2@school.edu.cn',
            'phone': '13800000012'
        }
    ]

    app = create_app()
    with app.app_context():
        created_count = 0

        for security_data in security_users:
            # 检查保安账户是否存在
            security = User.query.filter_by(username=security_data['username']).first()
            if security:
                print(f"⚠️  保安账户 {security_data['username']} 已存在，跳过创建")
                continue

            # 创建保安账户
            security = User(
                username=security_data['username'],
                real_name=security_data['real_name'],
                email=security_data['email'],
                phone=security_data['phone'],
                user_type='security',
                status='active'
            )
            security.set_password(security_data['password'])

            db.session.add(security)
            created_count += 1
            print(f"✅ 创建保安账户: {security_data['username']}")

        db.session.commit()
        print(f"\n📊 保安账户创建完成，共创建 {created_count} 个账户")

        if created_count > 0:
            print("\n保安账户信息:")
            for security_data in security_users:
                print(f"   用户名: {security_data['username']}")
                print(f"   密码: {security_data['password']}")
                print(f"   姓名: {security_data['real_name']}")
                print(f"   ---")

def create_sample_alumni():
    """创建示例校友账户"""
    print("\n🎓 创建示例校友账户...")

    alumni_data = {
        'username': f'sample_alumni_{int(time.time())}',
        'password': 'Sample123456',
        'real_name': '示例校友',
        'email': f'sample_{int(time.time())}@alumni.edu.cn',
        'phone': f'138{int(time.time()) % 100000000:08d}',
        'id_card': '110101199001011234',
        'graduation_year': '2020',
        'class_name': '计算机1班',
        'department': '计算机学院',
        'major': '计算机科学与技术',
        'class_teacher': '王老师',
        'current_city': '北京市',
        'work_unit': '示例科技有限公司',
        'position': '软件工程师'
    }

    app = create_app()
    with app.app_context():
        # 检查是否已有示例校友账户
        existing_alumni = User.query.filter_by(username=alumni_data['username']).first()
        if existing_alumni:
            print("⚠️  示例校友账户已存在，跳过创建")
            return

        # 创建校友用户
        alumni_user = User(
            username=alumni_data['username'],
            real_name=alumni_data['real_name'],
            email=alumni_data['email'],
            phone=alumni_data['phone'],
            user_type='alumni',
            status='active'
        )
        alumni_user.set_password(alumni_data['password'])

        db.session.add(alumni_user)
        db.session.flush()  # 获取用户ID

        # 创建校友档案
        alumni_profile = AlumniProfile(
            user_id=alumni_user.id,
            student_id=f"SAMPLE{int(time.time())}",
            graduation_year=int(alumni_data['graduation_year']),
            class_name=alumni_data['class_name'],
            department=alumni_data['department'],
            major=alumni_data['major'],
            id_card=alumni_data['id_card'],
            class_teacher=alumni_data['class_teacher'],
            current_city=alumni_data['current_city'],
            work_unit=alumni_data['work_unit'],
            position=alumni_data['position'],
            approval_status='approved'
        )

        db.session.add(alumni_profile)
        db.session.commit()

        print("✅ 示例校友账户创建成功")
        print(f"   用户名: {alumni_data['username']}")
        print(f"   密码: {alumni_data['password']}")
        print(f"   姓名: {alumni_data['real_name']}")

def activate_all_users():
    """激活所有用户账户"""
    print("\n🔄 激活所有用户账户...")

    app = create_app()
    with app.app_context():
        inactive_users = User.query.filter_by(status='inactive').all()

        if not inactive_users:
            print("✅ 所有用户账户都已激活")
            return

        for user in inactive_users:
            user.status = 'active'
            if user.alumni_profile:
                user.alumni_profile.approval_status = 'approved'

        db.session.commit()

        print(f"✅ 成功激活 {len(inactive_users)} 个用户账户")

def list_all_users():
    """列出所有用户账户"""
    print("\n📋 用户账户列表:")
    print("-" * 80)
    print(f"{'用户名':<15} {'类型':<8} {'姓名':<10} {'邮箱':<25} {'状态':<8}")
    print("-" * 80)

    app = create_app()
    with app.app_context():
        users = User.query.order_by(User.user_type, User.username).all()

        if not users:
            print("📭 没有找到任何用户账户")
            return

        for user in users:
            status_emoji = "✅" if user.status == 'active' else "❌"
            type_emoji = {"admin": "👨‍💼", "teacher": "👨‍🏫", "alumni": "🎓", "security": "👮‍♂️"}.get(user.user_type, "👤")

            print(f"{user.username:<15} {user.user_type:<8} {user.real_name:<10} {user.email:<25} {user.status:<8}")

        print("-" * 80)
        print(f"📊 总计: {len(users)} 个用户账户")

def clean_test_users():
    """清理测试用户账户（保留预设账户）"""
    print("\n🧹 清理测试用户账户...")

    # 预设账户列表（不删除）
    preserved_accounts = {
        'admin', 'teacher001', 'teacher002', 'security001', 'security002'
    }

    app = create_app()
    with app.app_context():
        # 查找测试账户（包含 test_ 或 sample_ 的用户名）
        test_users = User.query.filter(
            User.username.like('%test_%') |
            User.username.like('%sample_%') |
            User.username.like('%demo_%')
        ).all()

        if not test_users:
            print("✅ 没有找到需要清理的测试账户")
            return

        deleted_count = 0
        for user in test_users:
            if user.username not in preserved_accounts:
                # 删除校友档案（如果存在）
                if user.alumni_profile:
                    db.session.delete(user.alumni_profile)

                # 删除用户
                db.session.delete(user)
                deleted_count += 1
                print(f"🗑️  删除测试账户: {user.username}")

        db.session.commit()

        print(f"\n📊 清理完成，共删除 {deleted_count} 个测试账户")

def main():
    """主函数"""
    print("🚀 校友入校登记系统 - 测试账户管理工具")
    print("=" * 60)

    import argparse

    parser = argparse.ArgumentParser(description='测试账户管理工具')
    parser.add_argument('action', choices=[
        'create-all', 'create-admin', 'create-teachers', 'create-security',
        'create-alumni', 'activate-all', 'list', 'clean'
    ], help='要执行的操作')

    args = parser.parse_args()

    try:
        if args.action == 'create-all':
            create_admin_account()
            create_teacher_accounts()
            create_security_accounts()
            create_sample_alumni()
            activate_all_users()
            print("\n🎉 所有测试账户创建完成！")

        elif args.action == 'create-admin':
            create_admin_account()

        elif args.action == 'create-teachers':
            create_teacher_accounts()

        elif args.action == 'create-security':
            create_security_accounts()

        elif args.action == 'create-alumni':
            create_sample_alumni()

        elif args.action == 'activate-all':
            activate_all_users()

        elif args.action == 'list':
            list_all_users()

        elif args.action == 'clean':
            clean_test_users()

    except Exception as e:
        print(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()