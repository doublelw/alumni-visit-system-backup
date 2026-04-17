#!/usr/bin/env python3
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, '/var/www/lsalumni/backend')

# 设置环境变量
os.environ['PYTHONPATH'] = '/var/www/lsalumni/backend'
os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models import User

def check_admin_user():
    """检查admin用户是否存在并测试密码"""
    app = create_app()

    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('Admin user found:')
            print(f'Username: {admin.username}')
            print(f'User Type: {admin.user_type}')
            print(f'Status: {admin.status}')
            print(f'Password Hash: {admin.password_hash[:50]}...')

            # Test password verification
            print('Testing password verification:')
            try:
                result = admin.check_password('admin123')
                print(f'Password check result for "admin123": {result}')
            except Exception as e:
                print(f'Password check error: {e}')
                import traceback
                traceback.print_exc()
        else:
            print('Admin user not found')
            print('All users in database:')
            users = User.query.all()
            for user in users:
                print(f'  - {user.username} ({user.user_type}) - {user.status}')

if __name__ == '__main__':
    try:
        check_admin_user()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()