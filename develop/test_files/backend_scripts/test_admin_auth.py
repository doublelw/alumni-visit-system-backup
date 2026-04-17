"""
测试admin API认证
"""
import sys
sys.path.insert(0, '.')

from app import create_app, db
from app.models.user import User
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    print("=" * 60)
    print("测试Admin API认证")
    print("=" * 60)

    # 查找admin用户
    admin = User.query.filter_by(email='admin@school.edu.cn').first()

    if not admin:
        print("\n错误：未找到admin用户")
        sys.exit(1)

    print(f"\nAdmin用户信息:")
    print(f"  ID: {admin.id}")
    print(f"  用户名: {admin.username}")
    print(f"  Email: {admin.email}")
    print(f"  用户类型: '{admin.user_type}'")
    print(f"  状态: {admin.status}")

    # 创建JWT token
    print("\n" + "=" * 60)
    print("创建JWT Token")
    print("=" * 60)

    token = create_access_token(identity=admin.id)
    print(f"\nToken: {token[:50]}...")

    # 测试admin_required逻辑
    print("\n" + "=" * 60)
    print("测试认证逻辑")
    print("=" * 60)

    # 模拟admin_required函数的逻辑
    from flask_jwt_extended import decode_token
    try:
        decoded = decode_token(token)
        print(f"\nToken解码成功:")
        print(f"  Identity (user_id): {decoded['sub']}")
        print(f"  Type: {decoded.get('type', 'N/A')}")
        print(f"  Fresh: {decoded.get('fresh', 'N/A')}")
    except Exception as e:
        print(f"\nToken解码失败: {e}")
        sys.exit(1)

    # 检查用户是否存在且类型正确
    current_user_id = decoded['sub']
    current_user = User.query.get(current_user_id)

    print(f"\n用户查询结果:")
    print(f"  查询ID: {current_user_id}")
    print(f"  查询结果: {current_user}")

    if not current_user:
        print(f"  ❌ 用户不存在")
        sys.exit(1)

    print(f"  用户名: {current_user.username}")
    print(f"  用户类型: '{current_user.user_type}'")

    # 检查admin权限
    print(f"\n权限检查:")
    print(f"  user_type == 'admin': {current_user.user_type == 'admin'}")
    print(f"  结果: {'通过' if current_user.user_type == 'admin' else '失败'}")

    if current_user.user_type != 'admin':
        print(f"\n❌ 权限检查失败：用户类型不是 'admin'")
        print(f"  实际类型: '{current_user.user_type}'")
        sys.exit(1)

    print("\n[OK] 所有检查通过！")
    print("\n可以尝试以下命令测试API：")
    print(f"curl -H \"Authorization: Bearer {token}\" http://localhost:5000/api/admin/dashboard")
