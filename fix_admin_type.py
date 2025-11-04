import sqlite3
import os

def fix_admin_user_type():
    db_path = 'alumni_system_dev.db'

    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Update admin user type
        cursor.execute("UPDATE users SET user_type = 'admin' WHERE username = 'admin'")
        conn.commit()

        # Verify the update
        cursor.execute("SELECT username, user_type FROM users WHERE username = 'admin'")
        result = cursor.fetchone()

        if result:
            username, user_type = result
            print(f"Updated {username}: user_type = {user_type}")
            if user_type == 'admin':
                print("SUCCESS: Admin user type fixed!")
                return True
            else:
                print(f"ERROR: User type is still {user_type}")
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
    print("Fixing admin user type...")
    fix_admin_user_type()