import requests
import json

def test_admin_login():
    """测试管理员登录"""
    login_url = "http://localhost:5000/api/auth/login"

    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        print("Testing admin login...")
        response = requests.post(login_url, json=login_data)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("SUCCESS: Admin login successful!")
                return data["access_token"]
            else:
                print("ERROR: No token in response")
                return None
        else:
            print("ERROR: Admin login failed")
            return None

    except Exception as e:
        print(f"ERROR: {e}")
        return None

def test_admin_users_api(token):
    """测试管理员用户API"""
    users_url = "http://localhost:5000/api/admin/users"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        print("\nTesting admin users API...")
        response = requests.get(users_url, headers=headers)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Admin users API access successful!")
            print(f"Found {len(data.get(\"users\", []))} users")
            return True
        else:
            print(f"ERROR: Admin users API access failed: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=== Admin Permission Test ===")
    print()

    # Test admin login
    token = test_admin_login()

    if token:
        # Test admin API access
        success = test_admin_users_api(token)

        if success:
            print("\nSUCCESS: All admin permission tests passed!")
        else:
            print("\nERROR: Admin API test failed")
    else:
        print("\nERROR: Cannot test admin API without token")
