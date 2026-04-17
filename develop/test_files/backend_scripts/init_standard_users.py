"""
标准用户初始化脚本
创建四个端的标准用户账户：校友、受访老师、管理员、保安
"""

import sys
import uuid
import os
sys.path.insert(0, '.')

from app import create_app
from app.models import User
from app import db

# 标准用户配置
STANDARD_USERS = [
    {
        'username': 'test_user',
        'password': 'test123456',
        'user_type': 'alumni',
        'real_name': '测试校友用户',
        'email': 'alumni@test.com',
        'phone': '13800000001',
        'status': 'active'
    },
    {
        'username': 'admin',
        'password': 'admin123',
        'user_type': 'admin',
        'real_name': '系统管理员',
        'email': 'admin@test.com',
        'phone': '13800000003',
        'status': 'active'
    },
    {
        'username': 'security001',
        'password': 'security123',
        'user_type': 'security',
        'real_name': '保安人员001',
        'email': 'security001@test.com',
        'phone': '13800000004',
        'status': 'active'
    }
]

def create_standard_users():
    """创建标准用户账户"""
    app = create_app()

    with app.app_context():
        print("=== 创建标准用户账户 ===")

        for user_config in STANDARD_USERS:
            username = user_config['username']
            user_type = user_config['user_type']

            # 检查用户是否已存在
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"* 用户 {username} ({user_type}) 已存在")
                continue

            # 创建新用户
            user = User(
                uuid=str(uuid.uuid4()),
                username=username,
                real_name=user_config['real_name'],
                email=user_config['email'],
                phone=user_config['phone'],
                user_type=user_type,
                status=user_config['status']
            )

            # 设置密码
            user.set_password(user_config['password'])

            # 设置可访问性（仅对教师）
            if 'is_visitable' in user_config:
                user.is_visitable = user_config['is_visitable']

            db.session.add(user)
            db.session.commit()

            print(f"* 创建用户 {username} ({user_type}) - 密码: {user_config['password']}")

        print("\n=== 用户账户创建完成 ===")
        print("\n登录信息:")
        for user_config in STANDARD_USERS:
            print(f"  {user_config['real_name']} ({user_config['user_type']}):")
            print(f"    用户名: {user_config['username']}")
            print(f"    密码: {user_config['password']}")
            print()

if __name__ == '__main__':
    create_standard_users()