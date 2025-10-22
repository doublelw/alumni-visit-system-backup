#!/usr/bin/env python3
"""
创建管理员用户
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def create_admin_user():
    """创建管理员用户"""
    app = create_app()

    with app.app_context():
        print("正在创建管理员用户...")

        # 检查是否已存在admin用户
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            print("管理员用户已存在，更新密码...")
            existing_admin.set_password('123456')
            existing_admin.status = 'active'
            existing_admin.real_name = '系统管理员'
            existing_admin.email = 'admin@school.edu'
            existing_admin.phone = '13800138000'
        else:
            # 创建新的管理员用户
            admin_user = User(
                username='admin',
                email='admin@school.edu',
                phone='13800138000',
                real_name='系统管理员',
                user_type='admin',
                status='active'
            )
            admin_user.set_password('123456')
            db.session.add(admin_user)

        try:
            db.session.commit()
            print("✅ 管理员用户创建/更新成功！")
            print("📱 登录信息：")
            print("   用户名: admin")
            print("   密码: 123456")
            print("   类型: 管理员")
            print("🔗 管理后台: https://127.0.0.1:5000/admin")

        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建管理员用户失败: {str(e)}")
            return False

        return True

if __name__ == '__main__':
    success = create_admin_user()
    if success:
        print("\n🎉 管理员账户准备完成！现在可以使用管理员身份登录管理后台。")
    else:
        print("❌ 管理员账户创建失败！")
        sys.exit(1)