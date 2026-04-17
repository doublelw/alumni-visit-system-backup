#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试校友用户
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app import db
from werkzeug.security import generate_password_hash

def create_test_alumni():
    """创建测试校友用户"""
    app = create_app()

    with app.app_context():
        try:
            from app.models.user import User

            # 检查是否已存在测试校友
            existing_user = User.query.filter_by(username='TEST001').first()
            if existing_user:
                print("测试校友用户已存在")
                print(f"  用户名: {existing_user.username}")
                print(f"  姓名: {existing_user.real_name}")
                print(f"  密码: 12345678")
                return existing_user

            # 创建测试校友用户
            alumni_user = User(
                username='TEST001',
                real_name='张三',
                email='zhangsan@test.com',
                phone='13800138888',
                user_type='alumni',
                status='active',
                password_hash=generate_password_hash('12345678')
            )

            db.session.add(alumni_user)
            db.session.commit()

            print("成功创建测试校友用户:")
            print(f"  用户名: TEST001")
            print(f"  姓名: 张三")
            print(f"  密码: 12345678")
            print(f"  邮箱: zhangsan@test.com")
            print(f"  类型: alumni")

            return alumni_user

        except Exception as e:
            db.session.rollback()
            print(f"创建测试校友用户失败: {e}")
            return None

if __name__ == '__main__':
    create_test_alumni()