#!/usr/bin/env python3
"""
检查所有用户的正确密码
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def check_all_users_password():
    """检查所有用户的正确密码"""
    try:
        app = create_app()
        with app.app_context():
            # 获取所有活跃用户
            users = User.query.filter_by(status='active').all()

            # 常见密码列表
            common_passwords = [
                'admin123', '123456', 'student123', 'zhang123', 'xiaoming123',
                'test123', 'password', 'teacher123', 'parent123', 'security123',
                'alumni123', 'test123456', 'li123', 'laoshi123', 'fumu123',
                'test_security_api', 'test_student004'
            ]

            print("=== 所有活跃用户的密码检查 ===")

            found_passwords = {}

            for user in users:
                print(f"\n--- 用户: {user.username} ({user.real_name}) [{user.user_type}] ---")

                # 检查常见密码
                for pwd in common_passwords:
                    if user.check_password(pwd):
                        print(f"[FOUND] 正确密码: {pwd}")
                        found_passwords[user.username] = pwd
                        break
                else:
                    print("[NOT FOUND] 未找到匹配的常见密码")
                    found_passwords[user.username] = None

            print(f"\n=== 密码映射表 ===")
            print("known_passwords = {")
            for username, password in found_passwords.items():
                if password:
                    print(f"    '{username}': '{password}',")
            print("}")

            return found_passwords

    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    check_all_users_password()