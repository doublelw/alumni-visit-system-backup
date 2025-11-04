"""
添加常用测试账号到数据库
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def add_test_accounts():
    """添加常用测试账号"""
    try:
        print("=== 添加常用测试账号 ===")

        # 创建应用实例
        app = create_app()

        with app.app_context():
            # 测试账号列表
            test_accounts = [
                {
                    "username": "security01",
                    "real_name": "保安张三",
                    "email": "security01@example.com",
                    "phone": "13800010001",
                    "password": "123456",
                    "user_type": "security",
                    "employee_id": "SEC001"
                },
                {
                    "username": "security02",
                    "real_name": "保安李四",
                    "email": "security02@example.com",
                    "phone": "13800010002",
                    "password": "123456",
                    "user_type": "security",
                    "employee_id": "SEC002"
                },
                {
                    "username": "teacher01",
                    "real_name": "王老师",
                    "email": "teacher01@example.com",
                    "phone": "13800020001",
                    "password": "123456",
                    "user_type": "teacher",
                    "employee_id": "TCH001"
                },
                {
                    "username": "parent01",
                    "real_name": "家长张明",
                    "email": "parent01@example.com",
                    "phone": "13800030001",
                    "password": "123456",
                    "user_type": "parent"
                },
                {
                    "username": "student01",
                    "real_name": "学生张小明",
                    "email": "student01@example.com",
                    "phone": "13800040001",
                    "password": "123456",
                    "user_type": "student",
                    "student_id": "S2024001"
                }
            ]

            added_count = 0
            updated_count = 0

            for account_data in test_accounts:
                username = account_data["username"]
                user = User.query.filter_by(username=username).first()

                if user:
                    print(f"用户 {username} 已存在，更新信息...")
                    user.real_name = account_data["real_name"]
                    user.email = account_data["email"]
                    user.phone = account_data["phone"]
                    if account_data.get("employee_id"):
                        user.employee_id = account_data["employee_id"]
                    if account_data.get("student_id"):
                        user.student_id = account_data["student_id"]
                    updated_count += 1
                else:
                    print(f"创建新用户 {username}...")
                    user = User(
                        username=username,
                        real_name=account_data["real_name"],
                        email=account_data["email"],
                        phone=account_data["phone"],
                        user_type=account_data["user_type"],
                        status="active"
                    )

                    # 设置特定字段
                    if account_data.get("employee_id"):
                        user.employee_id = account_data["employee_id"]
                    if account_data.get("student_id"):
                        user.student_id = account_data["student_id"]

                    # 设置密码
                    user.set_password(account_data["password"])

                    db.session.add(user)
                    added_count += 1

            # 提交所有更改
            db.session.commit()

            print(f"\n=== 操作完成 ===")
            print(f"新增用户: {added_count} 个")
            print(f"更新用户: {updated_count} 个")

            # 显示所有用户统计
            total_users = User.query.count()
            print(f"数据库中总用户数: {total_users} 个")

            # 按类型统计
            user_types = db.session.query(User.user_type, db.func.count(User.id)).group_by(User.user_type).all()
            print("\n用户类型分布:")
            for user_type, count in user_types:
                print(f"  {user_type}: {count} 个")

            return True

    except Exception as e:
        print(f"操作失败: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    success = add_test_accounts()
    if success:
        print("\n测试账号添加成功！")
    else:
        print("\n测试账号添加失败！")
        sys.exit(1)