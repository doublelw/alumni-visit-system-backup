import sqlite3
import os

def verify_admin():
    db_path = 'alumni_system_dev.db'

    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("Users table does not exist")
            return False

        # Check admin user
        cursor.execute("SELECT id, username, user_type, status, employee_id FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()

        if admin_user:
            user_id, username, user_type, status, employee_id = admin_user
            print("Admin user found:")
            print(f"  ID: {user_id}")
            print(f"  Username: {username}")
            print(f"  User Type: {user_type}")
            print(f"  Status: {status}")
            print(f"  Employee ID: {employee_id}")

            if user_type == 'admin':
                print("SUCCESS: Admin user has correct permissions!")
                return True
            else:
                print(f"ERROR: Admin user has wrong type: {user_type}")
                return False
        else:
            print("ERROR: Admin user not found")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Verifying admin user...")
    verify_admin()