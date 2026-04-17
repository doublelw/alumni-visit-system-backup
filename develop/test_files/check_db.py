import sqlite3
import os

def check_database():
    db_path = 'alumni_system_dev.db'

    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")

        # Check if users table exists
        users_table_exists = any('user' in table[0].lower() for table in tables)
        print(f"\nUsers table exists: {users_table_exists}")

        if users_table_exists:
            # Find the correct table name
            users_table_name = None
            for table in tables:
                if 'user' in table[0].lower():
                    users_table_name = table[0]
                    break

            if users_table_name:
                print(f"Using table: {users_table_name}")

                # Get admin user
                cursor.execute(f"SELECT * FROM {users_table_name} WHERE username = 'admin'")
                admin_user = cursor.fetchone()

                if admin_user:
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({users_table_name})")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]

                    print(f"\nAdmin user columns:")
                    for i, value in enumerate(admin_user):
                        if i < len(column_names):
                            print(f"  {column_names[i]}: {value}")

                    # Find user_type column
                    user_type_index = None
                    for i, col in enumerate(column_names):
                        if 'user_type' in col.lower():
                            user_type_index = i
                            break

                    if user_type_index is not None:
                        current_type = admin_user[user_type_index]
                        print(f"\nCurrent user_type: {current_type}")

                        # Fix it if needed
                        if current_type != 'admin':
                            cursor.execute(f"UPDATE {users_table_name} SET user_type = 'admin' WHERE username = 'admin'")
                            conn.commit()
                            print("✅ Fixed admin user type to 'admin'")
                        else:
                            print("✅ Admin user type is already 'admin'")
                    else:
                        print("❌ user_type column not found")
                else:
                    print("❌ Admin user not found")
            else:
                print("❌ No users table found")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database()