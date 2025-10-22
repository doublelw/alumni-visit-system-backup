#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建EMP002审核员账号
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app import db
from werkzeug.security import generate_password_hash

def create_reviewer_account():
    """创建EMP002审核员账号"""
    app = create_app()

    with app.app_context():
        try:
            # 导入模型
            from app.models.user import User

            # 检查是否已存在EMP002用户
            existing_user = User.query.filter_by(username='EMP002').first()
            if existing_user:
                print(f"用户EMP002已存在，跳过创建")
                print(f"用户信息: {existing_user.real_name} ({existing_user.user_type})")
                return

            # 创建EMP002用户账号
            reviewer_user = User(
                username='EMP002',
                real_name='李娜',
                email='lina@university.edu.cn',
                phone='13800138002',
                user_type='teacher',  # 教师类型，有审核权限
                status='active',      # 激活状态
                password_hash=generate_password_hash('123456')  # 默认密码
            )

            db.session.add(reviewer_user)
            db.session.commit()

            print(f"成功创建EMP002审核员账号:")
            print(f"  用户名: EMP002")
            print(f"  姓名: 李娜")
            print(f"  密码: 123456")
            print(f"  类型: teacher (教师)")
            print(f"  权限: 有访问申请审核权限")

        except Exception as e:
            db.session.rollback()
            print(f"创建审核员账号失败: {e}")

if __name__ == '__main__':
    create_reviewer_account()