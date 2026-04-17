import sqlite3
import sys
import os

def debug_single_user():
    """调试单个用户API问题"""
    db_path = 'backend/instance/alumni_system_dev.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询用户ID 14
        cursor.execute('''
            SELECT id, username, user_type, real_name, email, phone
            FROM users WHERE id = 14
        ''')

        user = cursor.fetchone()
        if user:
            print(f"Found user: ID={user[0]}, username={user[1]}, type={user[2]}")
        else:
            print("User ID 14 not found")
            return False

        # 检查是否有组织关系
        cursor.execute('''
            SELECT COUNT(*) FROM organizations WHERE id = ?
        ''', (user[0],))  # 假设organization_id = user.id

        org_count = cursor.fetchone()[0]
        print(f"Organization count: {org_count}")

        # 检查是否有校友档案
        cursor.execute('''
            SELECT COUNT(*) FROM alumni_profiles WHERE user_id = ?
        ''', (user[0],))

        profile_count = cursor.fetchone()[0]
        print(f"Alumni profile count: {profile_count}")

        return True

    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== Debugging Single User API ===")
    debug_single_user()