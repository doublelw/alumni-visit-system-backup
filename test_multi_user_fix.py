"""
测试多用户类型修复是否有效
"""

import requests

def test_multi_user_fix():
    """测试多用户类型功能"""

    # 登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        login_response = requests.post("http://127.0.0.1:5000/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return False

        token = login_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}

        print("✅ 登录成功")

        # 测试1: 获取用户ID 15的信息，确认有多用户类型
        print("\n📍 测试1: 获取用户信息")
        user_response = requests.get("http://127.0.0.1:5000/api/admin/users/15", headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()['user']
            print(f"用户ID: {user_data['id']}")
            print(f"用户姓名: {user_data['real_name']}")
            print(f"用户类型: {user_data['user_type']}")

            if user_data['user_type'] == 'teacher,student,alumni':
                print("✅ 多用户类型数据正确")
            else:
                print(f"❌ 用户类型不正确，期望 'teacher,student,alumni'，实际 '{user_data['user_type']}'")
        else:
            print(f"❌ 获取用户信息失败: {user_response.status_code}")
            return False

        # 测试2: 更新用户类型
        print("\n📍 测试2: 更新用户类型")
        update_data = {
            "real_name": user_data['real_name'],
            "email": user_data['email'],
            "phone": user_data['phone'],
            "user_type": "teacher,alumni",  # 改变用户类型
            "status": user_data['status']
        }

        update_response = requests.put(
            "http://127.0.0.1:5000/api/admin/users/15",
            headers=headers,
            json=update_data
        )

        if update_response.status_code == 200:
            updated_user = update_response.json()['user']
            print(f"更新后用户类型: {updated_user['user_type']}")

            if updated_user['user_type'] == 'teacher,alumni':
                print("✅ 用户类型更新成功")
            else:
                print(f"❌ 用户类型更新失败，期望 'teacher,alumni'，实际 '{updated_user['user_type']}'")
                return False
        else:
            print(f"❌ 更新用户失败: {update_response.status_code}")
            return False

        # 测试3: 再次获取确认更新
        print("\n📍 测试3: 确认更新结果")
        confirm_response = requests.get("http://127.0.0.1:5000/api/admin/users/15", headers=headers)
        if confirm_response.status_code == 200:
            confirm_user = confirm_response.json()['user']
            print(f"确认用户类型: {confirm_user['user_type']}")

            if confirm_user['user_type'] == 'teacher,alumni':
                print("✅ 更新结果确认成功")
            else:
                print(f"❌ 更新结果确认失败")
                return False
        else:
            print(f"❌ 确认请求失败: {confirm_response.status_code}")
            return False

        print("\n🎉 所有测试通过！多用户类型功能工作正常")
        return True

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    print("=== 多用户类型修复测试 ===")
    test_multi_user_fix()