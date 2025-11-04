#!/usr/bin/env python3
"""
检查测试账号状态
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def check_accounts():
    """检查测试账号状态"""
    try:
        app = create_app()
        with app.app_context():
            print('=== 数据库中的所有用户 ===')
            users = User.query.all()
            for user in users:
                print(f'用户名: {user.username}, 姓名: {user.real_name}, 类型: {user.user_type}, 状态: {user.status}')

            print('\n=== 检查特定测试账号 ===')
            test_accounts = ['admin', 'security01', 'teacher01', 'parent01', 'student01']
            for username in test_accounts:
                user = User.query.filter_by(username=username).first()
                if user:
                    print(f'{username}: 存在, 状态={user.status}, 类型={user.user_type}')
                else:
                    print(f'{username}: 不存在')

            print('\n=== 检查admin账号密码验证 ===')
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print(f'Admin用户存在: {admin_user.real_name}')
                # 测试密码验证
                if admin_user.check_password('admin123'):
                    print('admin123密码验证成功')
                else:
                    print('admin123密码验证失败')

                # 显示密码哈希
                print(f'密码哈希: {admin_user.password_hash[:50]}...')

            return True

    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_accounts()