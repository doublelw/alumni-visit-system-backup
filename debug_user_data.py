import requests
import json

def debug_user_data():
    """调试用户数据，检查API返回的实际数据"""

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

    # 获取用户列表
    users_response = requests.get("http://localhost:5000/api/admin/users", headers=headers)
    if users_response.status_code != 200:
        print(f"Get users failed: {users_response.status_code}")
        return False

    users = users_response.json().get('users', [])

    # 找一个测试用户
    test_user = next((u for u in users if u['user_type'] in ['student', 'teacher']), None)
    if not test_user:
        print("No test user found")
        return False

    user_id = test_user['id']
    print(f"=== 测试用户: {test_user['username']} (ID: {user_id}) ===")
    print(f"列表中的用户类型: {test_user['user_type']}")
    print(f"列表中的状态: {test_user['status']}")

    # 获取单个用户详情
    detail_response = requests.get(
        f"http://localhost:5000/api/admin/users/{user_id}",
        headers=headers
    )

    if detail_response.status_code == 200:
        detail_data = detail_response.json()
        user = detail_data.get('user', {})
        print(f"\n=== 单个用户API返回数据 ===")
        print(f"用户名: {user.get('username')}")
        print(f"真实姓名: {user.get('real_name')}")
        print(f"用户类型: {user.get('user_type')} (类型: {type(user.get('user_type'))})")
        print(f"状态: {user.get('status')} (类型: {type(user.get('status'))})")
        print(f"学生ID: {user.get('student_id')}")
        print(f"员工ID: {user.get('employee_id')}")
        print(f"可拜访: {user.get('is_visitable')}")

        # 检查完整的数据结构
        print(f"\n=== 完整用户数据 ===")
        print(json.dumps(user, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 单个用户API访问失败: {detail_response.status_code}")
        print(f"Response: {detail_response.text}")
        return False

    return True

if __name__ == "__main__":
    print("=== 调试用户数据 ===")
    debug_user_data()