import requests
import json

def test_admin_user():
    base_url = "http://localhost:5000"

    print("Testing admin user update...")

    # Login as admin
    login_data = {"username": "admin", "password": "admin123"}

    try:
        print("Logging in...")
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)

        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print("Login successful")

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Get current admin user info
            print("Getting admin user info...")
            list_response = requests.get(f"{base_url}/api/admin/users", headers=headers)

            if list_response.status_code == 200:
                users_data = list_response.json()
                admin_user = None

                for user in users_data.get('users', []):
                    if user['username'] == 'admin':
                        admin_user = user
                        break

                if admin_user:
                    print(f"Admin user current type: {admin_user['user_type']}")
                    print(f"Admin user ID: {admin_user['id']}")

                    # Try to update admin user type (temporarily)
                    update_data = {
                        "username": admin_user['username'],
                        "real_name": admin_user['real_name'],
                        "email": admin_user['email'],
                        "phone": admin_user['phone'],
                        "user_type": "teacher",  # Change to teacher temporarily
                        "status": admin_user['status']
                    }

                    print("Attempting to update admin user type to 'teacher'...")
                    update_response = requests.put(
                        f"{base_url}/api/admin/users/{admin_user['id']}",
                        json=update_data,
                        headers=headers
                    )

                    print(f"Update response status: {update_response.status_code}")
                    print(f"Update response: {update_response.text}")

                    if update_response.status_code == 200:
                        print("SUCCESS: User type update works!")

                        # Verify the change
                        print("Verifying change...")
                        verify_response = requests.get(f"{base_url}/api/admin/users/{admin_user['id']}", headers=headers)

                        if verify_response.status_code == 200:
                            verify_data = verify_response.json()
                            updated_user = verify_data.get('user', verify_data)
                            print(f"Updated user type: {updated_user.get('user_type')}")

                            # Change back to admin
                            print("Changing back to 'admin' type...")
                            restore_data = update_data.copy()
                            restore_data['user_type'] = 'admin'

                            restore_response = requests.put(
                                f"{base_url}/api/admin/users/{admin_user['id']}",
                                json=restore_data,
                                headers=headers
                            )

                            if restore_response.status_code == 200:
                                print("SUCCESS: Restored admin user type")
                                return True
                            else:
                                print("FAILED to restore admin type")
                                return False
                        else:
                            print("FAILED to verify update")
                            return False
                    else:
                        print("FAILED to update user type")
                        return False
                else:
                    print("FAILED: Admin user not found")
                    return False
            else:
                print(f"FAILED to get users: {list_response.status_code}")
                return False
        else:
            print(f"FAILED to login: {login_response.status_code}")
            return False

    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_admin_user()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")