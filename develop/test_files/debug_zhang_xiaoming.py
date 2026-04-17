#!/usr/bin/env python3
"""
调试张小明用户的问题
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def debug_zhang_xiaoming():
    """调试张小明用户"""
    try:
        app = create_app()
        with app.app_context():
            print("=== 调试张小明用户 ===")

            # 查找用户
            user = User.query.filter_by(username='zhang_xiaoming').first()
            if not user:
                print("用户不存在")
                return

            print(f"用户ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"真实姓名: {user.real_name}")
            print(f"用户类型: {user.user_type}")
            print(f"用户状态: {user.status}")
            print(f"邮箱: {user.email}")
            print(f"手机: {user.phone}")
            print(f"创建时间: {user.created_at}")

            # 测试密码
            test_passwords = ['student123', '123456', 'zhang123', 'xiaoming123']
            print(f"\n=== 密码测试 ===")
            for pwd in test_passwords:
                result = user.check_password(pwd)
                print(f"密码 '{pwd}': {result}")

            # 检查用户模型方法
            print(f"\n=== 用户模型方法测试 ===")
            try:
                user_dict = user.to_dict(include_sensitive=True)
                print(f"to_dict方法成功: {list(user_dict.keys())}")
            except Exception as e:
                print(f"to_dict方法失败: {e}")
                import traceback
                traceback.print_exc()

            # 检查JWT token生成
            print(f"\n=== JWT Token 测试 ===")
            try:
                from flask_jwt_extended import create_access_token
                from datetime import timedelta

                access_token = create_access_token(
                    identity=str(user.id),
                    expires_delta=timedelta(hours=24)
                )
                print(f"JWT Token生成成功: {access_token[:50]}...")
            except Exception as e:
                print(f"JWT Token生成失败: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_zhang_xiaoming()