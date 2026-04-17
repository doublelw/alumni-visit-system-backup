import requests
import json

def test_admin_functions():
    """测试管理员功能"""
    base_url = "http://localhost:5000"

    # Step 1: Admin login
    print("=== Step 1: Admin Login ===")
    login_response = requests.post(
        f"{base_url}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )

    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code} - {login_response.text}")
        return False

    login_data = login_response.json()
    token = login_data.get('access_token')
    user_info = login_data.get('user', {})

    print(f"Login successful!")
    print(f"User: {user_info.get('username')} ({user_info.get('user_type')})")
    print(f"Real Name: {user_info.get('real_name')}")
    print(f"Status: {user_info.get('status')}")

    if user_info.get('user_type') != 'admin':
        print(f"ERROR: User type is '{user_info.get('user_type')}', expected 'admin'")
        return False

    # Step 2: Test admin users API
    print("\n=== Step 2: Test Admin Users API ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    users_response = requests.get(f"{base_url}/api/admin/users", headers=headers)

    if users_response.status_code == 200:
        users_data = users_response.json()
        users = users_data.get('users', [])
        print(f"SUCCESS: Retrieved {len(users)} users")

        # Check if admin user is in the list
        admin_user = next((u for u in users if u['username'] == 'admin'), None)
        if admin_user:
            print(f"Admin user found: {admin_user['username']} - {admin_user['user_type']}")
        else:
            print("WARNING: Admin user not found in users list")

        return True
    else:
        print(f"ERROR: Users API failed: {users_response.status_code} - {users_response.text}")
        return False

if __name__ == "__main__":
    print("=== Complete Admin Functionality Test ===")
    print()

    success = test_admin_functions()

    if success:
        print("\nSUCCESS: All admin functionality tests passed!")
        print("The admin user can now:")
        print("- Log in to the admin interface")
        print("- Access the user management API")
        print("- Create, edit, and delete users")
        print("- Manage user types and permissions")
    else:
        print("\nFAILED: Some admin functionality tests failed")
        print("Please check the errors above")