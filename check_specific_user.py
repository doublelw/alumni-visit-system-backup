#!/usr/bin/env python3
"""
检查特定用户的密码
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def check_user_password(username):
    """检查用户密码"""
    try:
        app = create_app()
        with app.app_context():
            user = User.query.filter_by(username=username).first()
            if user:
                print(f'用户: {user.username} ({user.real_name})')
                print(f'用户类型: {user.user_type}')
                print(f'用户状态: {user.status}')

                # 测试几种可能的密码
                passwords = ['student123', '123456', 'zhang123', 'xiaoming123', 'test123', 'password']
                for pwd in passwords:
                    if user.check_password(pwd):
                        print(f'[FOUND] 正确密码: {pwd}')
                        return pwd
                        break
                else:
                    print('[NOT FOUND] 未找到匹配的密码')
                    return None
            else:
                print(f'[NOT EXISTS] 用户 {username} 不存在')
                return None

    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 检查几个常见的用户
    users_to_check = ['zhang_xiaoming', 'li_laoshi', 'zhang_fumu', 'student01']

    for username in users_to_check:
        print(f"\n=== 检查用户: {username} ===")
        check_user_password(username)