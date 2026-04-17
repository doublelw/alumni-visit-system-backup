#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员账号检查和密码重置工具
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def check_admin_users():
    """检查所有管理员账号"""
    app = create_app()
    with app.app_context():
        admin_users = User.query.filter(User.user_type.like('%admin%')).all()

        print("="*70)
        print("管理员账号列表")
        print("="*70)

        if not admin_users:
            print("未找到管理员账号！")
            return None

        for i, user in enumerate(admin_users, 1):
            print(f"\n{i}. 用户名: {user.username}")
            print(f"   真实姓名: {user.real_name}")
            print(f"   用户类型: {user.user_type}")
            print(f"   邮箱: {user.email}")
            print(f"   手机: {user.phone}")
            print(f"   创建时间: {user.created_at}")
            print(f"   是否激活: {user.is_active}")

        return admin_users

def reset_admin_password(username='admin', new_password='admin123'):
    """重置管理员密码"""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"错误: 用户 '{username}' 不存在")
            return False

        # 使用bcrypt生成密码哈希
        import bcrypt
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
        user.password_hash = password_hash
        db.session.commit()

        print(f"成功重置用户 '{username}' 的密码")
        print(f"新密码: {new_password}")
        return True

def create_admin_user(username='admin', password='admin123', real_name='系统管理员'):
    """创建新的管理员账号"""
    app = create_app()
    with app.app_context():
        # 检查用户是否已存在
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"用户 '{username}' 已存在")
            return False

        # 使用bcrypt生成密码哈希
        import bcrypt
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        from datetime import datetime

        user = User(
            username=username,
            password_hash=password_hash,
            real_name=real_name,
            user_type='admin',
            email='admin@school.edu',
            phone='13800138000',
            status='active',
            created_at=datetime.now()
        )

        db.session.add(user)
        db.session.commit()

        print(f"成功创建管理员账号")
        print(f"用户名: {username}")
        print(f"密码: {password}")
        print(f"真实姓名: {real_name}")
        return True

def main():
    import argparse

    parser = argparse.ArgumentParser(description='管理员账号管理工具')
    parser.add_argument('action', choices=['check', 'reset', 'create'],
                       help='操作类型: check(查看), reset(重置密码), create(创建)')
    parser.add_argument('--username', default='admin',
                       help='用户名 (默认: admin)')
    parser.add_argument('--password', default='admin123',
                       help='密码 (默认: admin123)')
    parser.add_argument('--real-name', default='系统管理员',
                       help='真实姓名 (仅用于create)')

    args = parser.parse_args()

    try:
        if args.action == 'check':
            check_admin_users()
        elif args.action == 'reset':
            reset_admin_password(args.username, args.password)
        elif args.action == 'create':
            create_admin_user(args.username, args.password, args.real_name)

        print("\n操作完成！")
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
