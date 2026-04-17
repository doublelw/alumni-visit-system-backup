import sys
import os
sys.path.append('backend')

from app import create_app, db

def main():
    print("手动初始化数据库...")

    app = create_app()

    with app.app_context():
        print("创建所有表...")
        db.create_all()
        print("数据库表创建完成!")

        # 检查users表是否创建成功
        from backend.app.models.user import User

        # 检查是否有admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("创建admin用户...")
            admin = User(
                username='admin',
                real_name='系统管理员',
                email='admin@school.edu.cn',
                phone='13800000000',
                user_type='admin',
                status='active',
                employee_id='ADMIN001'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("admin用户创建成功!")
        else:
            print(f"admin用户已存在: {admin_user.user_type}")

            # 确保admin用户类型正确
            if admin_user.user_type != 'admin':
                print("修复admin用户类型...")
                admin_user.user_type = 'admin'
                db.session.commit()
                print("admin用户类型已修复!")

if __name__ == "__main__":
    main()