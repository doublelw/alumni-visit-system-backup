#!/usr/bin/env python3
"""
调试500登录错误
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def debug_login_500():
    """调试导致500错误的用户"""
    try:
        app = create_app()
        with app.app_context():
            print('=== 调试500登录错误 ===')

            # 从日志中看到的失败账号
            failing_accounts = [
                'zhang_fumu',
                'zhang_xiaoming',
                'security001'
            ]

            for username in failing_accounts:
                print(f"\n--- 检查用户: {username} ---")

                user = User.query.filter_by(username=username).first()
                if not user:
                    print(f"用户 {username} 不存在")
                    continue

                print(f"用户存在: {user.real_name}")
                print(f"ID: {user.id}")
                print(f"类型: {user.user_type}")
                print(f"状态: {user.status}")
                print(f"密码哈希: {user.password_hash[:50]}...")

                # 检查所有可能导致问题的字段
                try:
                    print(f"用户名: {user.username}")
                    print(f"邮箱: {user.email}")
                    print(f"电话: {user.phone}")
                    print(f"UUID: {user.uuid}")
                    print(f"创建时间: {user.created_at}")
                    print(f"更新时间: {user.updated_at}")

                    # 检查密码验证
                    test_passwords = ['parent123', 'student123', 'security123']
                    for pwd in test_passwords:
                        try:
                            if user.check_password(pwd):
                                print(f"密码验证成功: {pwd}")
                                break
                        except Exception as e:
                            print(f"密码验证异常: {e}")

                    # 检查to_dict方法
                    try:
                        user_dict = user.to_dict()
                        print(f"to_dict方法正常: {len(user_dict)} 字段")
                    except Exception as e:
                        print(f"to_dict方法异常: {e}")

                except Exception as e:
                    print(f"用户数据检查异常: {e}")
                    import traceback
                    traceback.print_exc()

            return True

    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_login_500()