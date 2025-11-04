import sqlite3
import os

def fix_server_admin_user():
    """修复服务器数据库中的admin用户类型"""
    db_path = 'backend/instance/alumni_system_dev.db'

    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 显示当前admin用户信息
        cursor.execute("SELECT id, username, user_type, email, real_name FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()

        if admin_user:
            user_id, username, current_type, email, real_name = admin_user
            print(f"Current admin user: ID={user_id}, username={username}, type={current_type}")

            # 更新用户类型
            cursor.execute("UPDATE users SET user_type = 'admin' WHERE username = 'admin'")
            conn.commit()

            # 验证更新
            cursor.execute("SELECT username, user_type FROM users WHERE username = 'admin'")
            result = cursor.fetchone()

            if result:
                username, user_type = result
                print(f"Updated {username}: user_type = {user_type}")
                if user_type == 'admin':
                    print("SUCCESS: Server admin user type fixed!")
                    return True
                else:
                    print(f"ERROR: User type is still {user_type}")
                    return False
        else:
            print("ERROR: Admin user not found in server database")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Fixing server admin user type...")
    success = fix_server_admin_user()

    if success:
        print("\nThe admin user should now have proper admin privileges.")
        print("Please test the admin login again.")
    else:
        print("\nFailed to fix admin user type.")