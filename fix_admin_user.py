#!/usr/bin/env python3
"""
修复admin用户类型 - 直接操作数据库
"""

import sqlite3
import os

def fix_admin_user():
    """修复admin用户的user_type"""
    db_path = 'alumni_system_dev.db'  # SQLite数据库路径

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        print("连接数据库...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查找admin用户
        cursor.execute("SELECT id, username, user_type FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()

        if admin_user:
            user_id, username, current_type = admin_user
            print(f"找到admin用户: ID={user_id}, username={username}, current_type={current_type}")

            # 修复用户类型
            cursor.execute("UPDATE users SET user_type = 'admin' WHERE username = 'admin'")
            conn.commit()

            print("✅ 已将admin用户类型修复为 'admin'")

            # 验证修复结果
            cursor.execute("SELECT user_type FROM users WHERE username = 'admin'")
            new_type = cursor.fetchone()[0]
            print(f"✅ 验证结果: admin用户类型现在是 '{new_type}'")

            return True
        else:
            print("❌ 未找到admin用户")
            return False

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def show_all_users():
    """显示所有用户信息"""
    db_path = 'alumni_system_dev.db'

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, real_name, user_type, status, created_at
            FROM users
            ORDER BY id
        """)

        users = cursor.fetchall()

        print("\n所有用户列表:")
        print("-" * 80)
        print(f"{'ID':<5} {'用户名':<15} {'真实姓名':<15} {'类型':<10} {'状态':<10} {'创建时间'}")
        print("-" * 80)

        for user in users:
            user_id, username, real_name, user_type, status, created_at = user
            print(f"{user_id:<5} {username:<15} {real_name:<15} {user_type:<10} {status:<10} {created_at}")

        print("-" * 80)

    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== 修复admin用户类型 ===")
    print()

    # 先显示当前用户状态
    show_all_users()
    print()

    # 修复admin用户
    success = fix_admin_user()

    if success:
        print("\n=== 修复成功 ===")
        print("现在admin用户应该可以正常访问管理功能了")
        print("请重新登录管理界面测试")
    else:
        print("\n=== 修复失败 ===")
        print("请检查数据库连接和权限")