"""
测试多用户类型功能
"""

import requests
import json

# 测试数据
BASE_URL = "http://127.0.0.1:5000"

def test_multi_user_types():
    """测试多用户类型的保存和读取"""

    # 首先需要管理员登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        # 登录
        print("正在登录管理员账户...")
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"登录失败: {login_response.status_code} - {login_response.text}")
            return False

        token = login_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        print("登录成功!")

        # 获取现有用户列表
        print("\n获取现有用户列表...")
        users_response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        if users_response.status_code != 200:
            print(f"获取用户列表失败: {users_response.status_code}")
            return False

        users = users_response.json()
        print(f"当前有 {len(users)} 个用户")

        # 找一个用户进行测试
        test_user = None
        for user in users:
            if user['username'] != 'admin':  # 不测试admin用户
                test_user = user
                break

        if not test_user:
            print("没有找到可用于测试的用户")
            return False

        print(f"\n选择测试用户: {test_user['real_name']} (当前类型: {test_user['user_type']})")

        # 测试更新为多用户类型
        user_id = test_user['id']
        multi_types = "teacher,student,alumni"

        print(f"\n将用户类型更新为: {multi_types}")
        update_data = {
            "real_name": test_user['real_name'],
            "email": test_user['email'],
            "phone": test_user['phone'],
            "user_type": multi_types,
            "status": test_user['status']
        }

        update_response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}",
            headers=headers,
            json=update_data
        )

        if update_response.status_code != 200:
            print(f"更新用户失败: {update_response.status_code} - {update_response.text}")
            return False

        updated_user = update_response.json()
        print(f"更新成功! 新用户类型: {updated_user['user_type']}")

        # 验证数据是否正确保存
        print("\n验证数据是否正确保存...")
        get_user_response = requests.get(f"{BASE_URL}/api/admin/users/{user_id}", headers=headers)
        if get_user_response.status_code != 200:
            print(f"获取用户信息失败: {get_user_response.status_code}")
            return False

        verified_user = get_user_response.json()
        print(f"验证结果: 用户类型 = {verified_user['user_type']}")

        if verified_user['user_type'] == multi_types:
            print("✅ 多用户类型功能测试成功!")
            return True
        else:
            print(f"❌ 测试失败: 期望 {multi_types}, 实际 {verified_user['user_type']}")
            return False

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    print("=== 多用户类型功能测试 ===")
    success = test_multi_user_types()

    if success:
        print("\n🎉 所有测试通过! 多用户类型功能正常工作")
    else:
        print("\n❌ 测试失败")