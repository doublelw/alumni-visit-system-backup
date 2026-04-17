#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员账户
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app import db
from werkzeug.security import generate_password_hash

def create_admin_account():
    """创建管理员账户"""
    app = create_app()

    with app.app_context():
        try:
            # 导入模型
            from app.models.user import User

            # 检查是否已存在管理员用户
            existing_admin = User.query.filter_by(user_type='admin').first()
            if existing_admin:
                print(f"管理员账户已存在，跳过创建")
                print(f"用户名: {existing_admin.username}")
                print(f"姓名: {existing_admin.real_name}")
                return existing_admin

            # 创建管理员账户
            admin_user = User(
                username='admin',
                real_name='系统管理员',
                email='admin@university.edu.cn',
                phone='13800138000',
                user_type='admin',    # 管理员类型
                status='active',      # 激活状态
                password_hash=generate_password_hash('admin123')  # 默认密码
            )

            db.session.add(admin_user)
            db.session.commit()

            print(f"成功创建管理员账户:")
            print(f"  用户名: admin")
            print(f"  姓名: 系统管理员")
            print(f"  密码: admin123")
            print(f"  类型: admin (管理员)")
            print(f"  权限: 系统管理权限")

            return admin_user

        except Exception as e:
            db.session.rollback()
            print(f"创建管理员账户失败: {e}")
            return None

if __name__ == '__main__':
    create_admin_account()