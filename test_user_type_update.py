import requests
import json

def test_user_type_update():
    """测试用户类型更新和持久化"""

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

    # 找一个测试用户（ID 14的学生用户）
    test_user = next((u for u in users if u['id'] == 14), None)
    if not test_user:
        print("Test user (ID: 14) not found")
        return False

    print(f"=== 测试用户类型更新 ===")
    print(f"当前用户: {test_user['username']} (类型: {test_user.get('user_type')})")

    # 1. 将用户类型改为 teacher
    print("\n1. 将用户类型改为 'teacher'")
    update_data = {
        "username": test_user['username'],
        "real_name": test_user['real_name'],
        "email": test_user['email'],
        "phone": test_user['phone'],
        "user_type": "teacher"
    }

    update_response = requests.put(
        f"http://localhost:5000/api/admin/users/{test_user['id']}",
        headers=headers,
        json=update_data
    )

    if update_response.status_code == 200:
        print("✅ 更新成功")
        result = update_response.json()
        updated_user = result.get('user', {})
        print(f"更新后类型: {updated_user.get('user_type')}")
    else:
        print(f"❌ 更新失败: {update_response.text}")
        return False

    # 2. 立即获取单个用户API验证
    print("\n2. 验证单个用户API")
    detail_response = requests.get(
        f"http://localhost:5000/api/admin/users/{test_user['id']}",
        headers=headers
    )

    if detail_response.status_code == 200:
        detail_data = detail_response.json()
        detail_user = detail_data.get('user', {})
        print(f"单个API返回类型: {detail_user.get('user_type')}")

        if detail_user.get('user_type') == 'teacher':
            print("✅ 单个API验证成功")
        else:
            print("❌ 单个API验证失败")
            return False
    else:
        print(f"❌ 单个API访问失败: {detail_response.status_code}")
        return False

    # 3. 从用户列表API验证
    print("\n3. 验证用户列表API")
    list_response = requests.get("http://localhost:5000/api/admin/users", headers=headers)
    if list_response.status_code == 200:
        list_data = list_response.json()
        updated_user_in_list = next((u for u in list_data.get('users', []) if u['id'] == test_user['id']), None)

        if updated_user_in_list:
            print(f"列表API返回类型: {updated_user_in_list.get('user_type')}")

            if updated_user_in_list.get('user_type') == 'teacher':
                print("✅ 列表API验证成功")
            else:
                print("❌ 列表API验证失败")
                return False
        else:
            print("❌ 用户在列表中未找到")
            return False
    else:
        print(f"❌ 列表API访问失败: {list_response.status_code}")
        return False

    # 4. 将用户类型改回 student
    print("\n4. 将用户类型改回 'student'")
    update_data['user_type'] = 'student'
    restore_response = requests.put(
        f"http://localhost:5000/api/admin/users/{test_user['id']}",
        headers=headers,
        json=update_data
    )

    if restore_response.status_code == 200:
        print("✅ 恢复成功")
    else:
        print(f"❌ 恢复失败: {restore_response.text}")
        return False

    print("\n=== 测试完成 ===")
    return True

if __name__ == "__main__":
    print("=== 用户类型持久化测试 ===")
    test_user_type_update()
