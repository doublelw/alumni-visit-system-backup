#!/usr/bin/env python3
"""
测试用户注册功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from datetime import datetime

def test_registration():
    app = create_app()

    with app.app_context():
        try:
            # 创建测试用户数据
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            user_data = {
                'username': f'test_visitor_{timestamp}',
                'password': 'Test123456',
                'real_name': '测试访客',
                'email': f'test{timestamp}@example.com',
                'phone': '13800138000',
                'user_type': 'alumni',
                'id_card': '110101199001011234'
            }

            print(f"正在创建测试用户: {user_data['username']}")

            # 检查用户是否已存在
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if existing_user:
                print(f"用户 {user_data['username']} 已存在")
                return existing_user

            # 创建新用户
            user = User(
                username=user_data['username'],
                real_name=user_data['real_name'],
                email=user_data['email'],
                phone=user_data['phone'],
                user_type=user_data['user_type']
            )
            user.set_password(user_data['password'])

            db.session.add(user)
            db.session.commit()

            print(f"✅ 用户 {user_data['username']} 创建成功")
            print(f"   用户ID: {user.id}")
            print(f"   用户类型: {user.user_type}")

            return user

        except Exception as e:
            print(f"❌ 用户创建失败: {str(e)}")
            db.session.rollback()
            return None

def create_test_accounts():
    """创建测试账户"""
    app = create_app()

    with app.app_context():
        try:
            # 创建教师账户
            teacher = User.query.filter_by(username='teacher001').first()
            if not teacher:
                teacher = User(
                    username='teacher001',
                    real_name='测试教师',
                    email='teacher001@test.com',
                    phone='13800000001',
                    user_type='teacher'
                )
                teacher.set_password('teacher123')
                db.session.add(teacher)
                print("✅ 教师账户创建成功")
            else:
                print("✅ 教师账户已存在")

            # 创建保安账户
            security = User.query.filter_by(username='security001').first()
            if not security:
                security = User(
                    username='security001',
                    real_name='测试保安',
                    email='security001@test.com',
                    phone='13800000002',
                    user_type='security'
                )
                security.set_password('security123')
                db.session.add(security)
                print("✅ 保安账户创建成功")
            else:
                print("✅ 保安账户已存在")

            db.session.commit()
            return True

        except Exception as e:
            print(f"❌ 测试账户创建失败: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🚀 开始测试用户注册功能...")

    # 创建测试账户
    if create_test_accounts():
        print("\n✅ 测试账户创建完成")

    # 创建访客测试用户
    user = test_registration()

    if user:
        print(f"\n🎉 测试完成！用户 {user.username} 已成功创建")
        print("\n📋 测试账户信息:")
        print("教师: teacher001 / teacher123")
        print("保安: security001 / security123")
        print(f"访客: {user.username} / Test123456")
    else:
        print("\n❌ 测试失败")