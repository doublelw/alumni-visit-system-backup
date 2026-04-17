"""
创建admin用户
"""
import sys
sys.path.insert(0, '.')

from app import create_app, db
from app.models.user import User
import bcrypt

app = create_app()

with app.app_context():
    print("=" * 60)
    print("创建Admin用户")
    print("=" * 60)

    # 检查admin用户是否已存在
    existing_admin = User.query.filter_by(email='admin@school.edu.cn').first()

    if existing_admin:
        print(f"\nAdmin用户已存在:")
        print(f"  ID: {existing_admin.id}")
        print(f"  用户名: {existing_admin.username}")
        print(f"  Email: {existing_admin.email}")
        print(f"  用户类型: {existing_admin.user_type}")

        # 更新为admin类型（如果不是）
        if existing_admin.user_type != 'admin':
            print(f"\n更新用户类型为 'admin'...")
            existing_admin.user_type = 'admin'
            db.session.commit()
            print("[OK] 更新成功")
        else:
            print("[OK] 用户类型正确")

        sys.exit(0)

    # 创建新的admin用户
    print("\n创建新的admin用户...")

    # 密码哈希
    password = 'admin123'
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    admin_user = User(
        username='admin',
        password_hash=password_hash,
        real_name='系统管理员',
        email='admin@school.edu.cn',
        phone='13800000000',
        user_type='admin',
        status='active',
        employee_id='ADMIN001'
    )

    db.session.add(admin_user)
    db.session.commit()

    print("\n[OK] Admin用户创建成功！")
    print(f"  用户名: admin")
    print(f"  密码: {password}")
    print(f"  Email: admin@school.edu.cn")
    print(f"  手机号: 13800000000")
    print(f"  用户类型: admin")
    print(f"\n请妥善保管登录信息！")
