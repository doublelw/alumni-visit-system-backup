"""
检查数据库连接和保安人员账号
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def check_database_and_security_accounts():
    """检查数据库连接和保安人员账号"""
    try:
        print("=== 数据库连接和保安账号检查 ===")

        # 创建应用实例
        app = create_app()

        with app.app_context():
            print("1. 检查数据库连接...")
            try:
                # 执行数据库查询测试连接
                db.engine.execute("SELECT 1")
                print("✅ 数据库连接正常")
            except Exception as e:
                print(f"❌ 数据库连接失败: {e}")
                return False

            print("\n2. 检查数据库中的用户总数...")
            try:
                total_users = User.query.count()
                print(f"✅ 数据库中共有 {total_users} 个用户")
            except Exception as e:
                print(f"❌ 查询用户总数失败: {e}")
                return False

            print("\n3. 检查保安人员账号...")
            try:
                security_users = User.query.filter_by(user_type='security').all()
                print(f"✅ 找到 {len(security_users)} 个保安人员账号:")

                if security_users:
                    for i, user in enumerate(security_users, 1):
                        print(f"   {i}. 用户名: {user.username}")
                        print(f"      真实姓名: {user.real_name}")
                        print(f"      邮箱: {user.email}")
                        print(f"      手机号: {user.phone}")
                        print(f"      状态: {user.status}")
                        print(f"      可拜访: {user.is_visitable}")
                        print(f"      创建时间: {user.created_at}")
                        print()
                else:
                    print("   ⚠️  未找到保安人员账号")

                    # 检查是否有包含security的多用户类型
                    multi_security_users = User.query.filter(User.user_type.like('%security%')).all()
                    if multi_security_users:
                        print(f"✅ 找到 {len(multi_security_users)} 个包含保安身份的用户:")
                        for i, user in enumerate(multi_security_users, 1):
                            print(f"   {i}. 用户名: {user.username}")
                            print(f"      真实姓名: {user.real_name}")
                            print(f"      用户类型: {user.user_type}")
                            print(f"      状态: {user.status}")
                            print()

            except Exception as e:
                print(f"❌ 查询保安人员失败: {e}")
                return False

            print("\n4. 检查用户类型分布...")
            try:
                user_types = db.session.query(User.user_type, db.func.count(User.id)).group_by(User.user_type).all()
                print("用户类型分布:")
                for user_type, count in user_types:
                    print(f"   {user_type}: {count} 个用户")
            except Exception as e:
                print(f"❌ 查询用户类型分布失败: {e}")

            print("\n5. 测试数据库写入功能...")
            try:
                # 创建一个测试保安账号（如果不存在）
                test_username = "test_security_check"
                existing_user = User.query.filter_by(username=test_username).first()

                if existing_user:
                    print(f"✅ 测试账号 {test_username} 已存在，删除测试账号...")
                    db.session.delete(existing_user)
                    db.session.commit()
                    print("✅ 测试账号已删除")
                else:
                    print("✅ 准备创建测试保安账号...")

                # 创建新的测试保安账号
                test_user = User(
                    username=test_username,
                    real_name="测试保安",
                    email="test_security@example.com",
                    phone="13800138999",
                    user_type="security",
                    status="active"
                )
                test_user.set_password("test123456")

                db.session.add(test_user)
                db.session.commit()

                print("✅ 测试保安账号创建成功")

                # 立即删除测试账号
                db.session.delete(test_user)
                db.session.commit()
                print("✅ 测试账号清理完成")
                print("✅ 数据库读写功能正常")

            except Exception as e:
                print(f"❌ 数据库读写测试失败: {e}")
                db.session.rollback()
                return False

            print("\n=== 检查完成 ===")
            return True

    except Exception as e:
        print(f"❌ 检查过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = check_database_and_security_accounts()
    if success:
        print("\n🎉 数据库连接和保安账号检查通过！")
    else:
        print("\n💥 检查发现问题，请查看上述错误信息！")
        sys.exit(1)