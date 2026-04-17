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
import bcrypt

def reset_admin_password():
    """重置admin用户密码为admin123"""
    # 强制使用生产环境配置
    app = create_app('production')

    with app.app_context():
        # 创建所有数据库表
        print("正在创建数据库表...")
        db.create_all()
        print("数据库表创建完成")

        # 删除现有的admin用户（如果存在）
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            print("删除现有的admin用户...")
            db.session.delete(existing_admin)
            db.session.commit()

        # 查找admin用户
        admin_user = User.query.filter_by(username='admin').first()

        if not admin_user:
            print("未找到admin用户，正在创建...")

            # 创建admin用户
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), salt).decode('utf-8')
            admin_user = User(
                username='admin',
                real_name='系统管理员',
                email='admin@lsalumni.com',
                phone='13800000000',
                user_type='admin',
                status='active',
                password_hash=password_hash
            )

            db.session.add(admin_user)
            db.session.commit()

            print(f"Admin用户创建成功!")
            print(f"用户名: {admin_user.username}")
            print(f"验证密码: {admin_user.check_password('admin123')}")

if __name__ == '__main__':
    try:
        reset_admin_password()
        print("\n操作完成!")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()