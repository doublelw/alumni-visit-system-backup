#!/usr/bin/env python3
"""
测试员工编号修复 - 验证编辑用户功能
"""

import requests
import json

def test_edit_user():
    """测试编辑用户功能"""
    base_url = "http://localhost:5000"

    print("🔧 测试员工编号修复...")

    # 首先测试登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        print("📍 测试管理员登录...")
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)

        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print("✅ 管理员登录成功")

            # 获取用户列表
            print("📍 获取用户列表...")
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            list_response = requests.get(f"{base_url}/api/admin/users", headers=headers)

            if list_response.status_code == 200:
                users_data = list_response.json()
                users = users_data.get('users', [])
                print(f"✅ 获取到 {len(users)} 个用户")

                # 找一个测试用户
                test_user = None
                for user in users:
                    if user['username'] != 'admin':
                        test_user = user
                        break

                if test_user:
                    user_id = test_user['id']
                    print(f"📍 测试编辑用户: {test_user['username']} (ID: {user_id})")

                    # 测试编辑用户 - 不修改员工编号
                    edit_data = {
                        "real_name": f"测试编辑_{test_user['real_name']}",
                        "email": test_user['email'],
                        "phone": test_user['phone'],
                        "user_type": test_user['user_type'],
                        "status": test_user['status'],
                        "employee_id": test_user.get('employee_id', '')  # 保持原有员工编号
                    }

                    edit_response = requests.put(
                        f"{base_url}/api/admin/users/{user_id}",
                        json=edit_data,
                        headers=headers
                    )

                    if edit_response.status_code == 200:
                        print("✅ 编辑用户成功 - 员工编号验证通过")
                        print(f"📍 响应: {edit_response.json()}")
                        return True
                    else:
                        print(f"❌ 编辑用户失败: {edit_response.status_code}")
                        print(f"📍 错误响应: {edit_response.text}")
                        return False
                else:
                    print("❌ 没有找到可测试的用户")
                    return False
            else:
                print(f"❌ 获取用户列表失败: {list_response.status_code}")
                print(f"📍 响应: {list_response.text}")
                return False

        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"📍 响应: {login_response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    print("=== 员工编号修复验证测试 ===")
    print("修复内容: 员工编号为空时不进行重复性检查")
    print()

    success = test_edit_user()

    print()
    if success:
        print("🎉 员工编号修复验证通过！")
        print("📝 现在可以正常编辑用户信息:")
        print("   1. 访问 http://localhost:5000/admin-login")
        print("   2. 登录后进入用户管理页面")
        print("   3. 编辑用户信息应该不会报错")
    else:
        print("❌ 员工编号修复验证失败")
        print("📝 请检查服务器是否正常运行")

if __name__ == "__main__":
    main()