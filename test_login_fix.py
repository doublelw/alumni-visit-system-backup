#!/usr/bin/env python3
"""
测试登录功能修复
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from werkzeug.security import check_password_hash

def test_login():
    """测试登录功能"""
    try:
        app = create_app()
        with app.app_context():
            print('=== 测试登录功能 ===')

            # 测试账号列表
            test_accounts = [
                {'username': 'admin', 'password': 'admin123'},
                {'username': 'security01', 'password': '123456'},
                {'username': 'teacher01', 'password': '123456'},
                {'username': 'parent01', 'password': '123456'},
                {'username': 'student01', 'password': '123456'},
            ]

            for account in test_accounts:
                username = account['username']
                password = account['password']

                print(f"\n--- 测试账号: {username} ---")

                # 查找用户
                user = User.query.filter_by(username=username).first()
                if not user:
                    print(f"用户 {username} 不存在")
                    continue

                print(f"用户存在: {user.real_name} ({user.user_type})")
                print(f"用户状态: {user.status}")

                # 验证密码
                if user.check_password(password):
                    print(f"密码验证成功")
                else:
                    print(f"密码验证失败")

                    # 尝试其他可能的密码
                    other_passwords = ['admin', '12345', password + password]
                    for other_pwd in other_passwords:
                        if user.check_password(other_pwd):
                            print(f"发现正确密码: {other_pwd}")
                            break

            return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_login()