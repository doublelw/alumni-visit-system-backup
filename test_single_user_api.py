import requests
import json

def test_single_user_api():
    """测试单个用户API"""

    # 先登录获取token
    login_response = requests.post(
        "http://localhost:5000/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )

    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        return False

    token = login_response.json()['access_token']
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 测试获取用户列表
    users_response = requests.get("http://localhost:5000/api/admin/users", headers=headers)

    if users_response.status_code != 200:
        print(f"Get users failed: {users_response.status_code}")
        return False

    users_data = users_response.json()
    users = users_data.get('users', [])

    if not users:
        print("No users found")
        return False

    # 测试获取第一个用户的详细信息
    test_user = users[0]
    user_id = test_user['id']

    print(f"Testing single user API for user ID: {user_id}")
    print(f"User from list: {test_user['username']} ({test_user.get('user_type')})")

    # 测试单个用户API
    single_user_response = requests.get(
        f"http://localhost:5000/api/admin/users/{user_id}",
        headers=headers
    )

    print(f"Single user API status: {single_user_response.status_code}")

    if single_user_response.status_code == 200:
        single_user_data = single_user_response.json()
        user_detail = single_user_data.get('user', {})
        print(f"User from detail API: {user_detail.get('username')} ({user_detail.get('user_type')})")

        # 检查数据一致性
        if (user_detail.get('username') == test_user['username'] and
            user_detail.get('user_type') == test_user.get('user_type')):
            print("SUCCESS: Single user API working correctly")
            return True
        else:
            print("ERROR: Data inconsistency between list and detail APIs")
            print(f"List API:  {test_user.get('user_type')}")
            print(f"Detail API: {user_detail.get('user_type')}")
            return False
    else:
        print(f"ERROR: Single user API failed: {single_user_response.text}")
        return False

if __name__ == "__main__":
    print("=== Testing Single User API ===")
    test_single_user_api()