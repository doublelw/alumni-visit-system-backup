"""
测试多用户类型功能 - 简化版本
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

        users_data = users_response.json()
        print(f"返回数据类型: {type(users_data)}")
        print(f"返回数据: {users_data}")

        # 处理不同的响应格式
        users = []
        if isinstance(users_data, dict):
            if 'users' in users_data:
                users = users_data['users']
            elif 'data' in users_data:
                users = users_data['data']
            else:
                print(f"无法识别的响应格式: {users_data}")
                return False
        elif isinstance(users_data, list):
            users = users_data
        else:
            print(f"意外的响应格式: {type(users_data)}")
            return False

        print(f"当前有 {len(users)} 个用户")

        # 找一个用户进行测试
        test_user = None
        for user in users:
            if user.get('username') != 'admin':  # 不测试admin用户
                test_user = user
                break

        if not test_user:
            print("没有找到可用于测试的用户")
            return False

        print(f"\n选择测试用户: {test_user.get('real_name', 'Unknown')} (当前类型: {test_user.get('user_type', 'Unknown')})")

        # 测试更新为多用户类型
        user_id = test_user.get('id')
        multi_types = "teacher,student,alumni"

        print(f"\n将用户类型更新为: {multi_types}")
        update_data = {
            "real_name": test_user.get('real_name'),
            "email": test_user.get('email'),
            "phone": test_user.get('phone'),
            "user_type": multi_types,
            "status": test_user.get('status', 'active')
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
        print(f"更新成功! 新用户类型: {updated_user.get('user_type')}")

        # 验证数据是否正确保存
        print("\n验证数据是否正确保存...")
        get_user_response = requests.get(f"{BASE_URL}/api/admin/users/{user_id}", headers=headers)
        if get_user_response.status_code != 200:
            print(f"获取用户信息失败: {get_user_response.status_code}")
            return False

        verified_user = get_user_response.json()
        print(f"验证结果: 用户类型 = {verified_user.get('user_type')}")

        if verified_user.get('user_type') == multi_types:
            print("多用户类型功能测试成功!")
            return True
        else:
            print(f"测试失败: 期望 {multi_types}, 实际 {verified_user.get('user_type')}")
            return False

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    print("=== 多用户类型功能测试 ===")
    success = test_multi_user_types()

    if success:
        print("\n测试成功! 多用户类型功能正常工作")
    else:
        print("\n测试失败")