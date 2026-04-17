#!/usr/bin/env python3
"""
添加缺失的测试账号
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def add_missing_accounts():
    """添加缺失的测试账号"""
    try:
        app = create_app()
        with app.app_context():
            print('=== 添加缺失的测试账号 ===')

            # 需要添加的账号
            missing_accounts = [
                {
                    'username': 'security001',
                    'real_name': '保安人员001',
                    'email': 'security001@example.com',
                    'phone': '13800010001',
                    'password': 'security123',
                    'user_type': 'security'
                },
                {
                    'username': 'security002',
                    'real_name': '保安人员002',
                    'email': 'security002@example.com',
                    'phone': '13800010002',
                    'password': 'security123',
                    'user_type': 'security'
                },
                {
                    'username': 'alumni001',
                    'real_name': '校友001',
                    'email': 'alumni001@example.com',
                    'phone': '13800020001',
                    'password': 'test123456',
                    'user_type': 'alumni'
                }
            ]

            for account_data in missing_accounts:
                username = account_data['username']
                password = account_data['password']

                print(f"\n--- 检查账号: {username} ---")

                # 检查用户是否已存在
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    print(f"用户 {username} 已存在，跳过")
                    continue

                # 创建新用户
                user = User(
                    username=account_data['username'],
                    real_name=account_data['real_name'],
                    email=account_data['email'],
                    phone=account_data['phone'],
                    user_type=account_data['user_type'],
                    status='active'
                )
                user.set_password(password)

                db.session.add(user)
                db.session.commit()

                print(f"成功创建用户: {user.real_name} ({user.user_type})")

            print('\n=== 账号添加完成 ===')
            return True

    except Exception as e:
        print(f"添加失败: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

if __name__ == "__main__":
    add_missing_accounts()