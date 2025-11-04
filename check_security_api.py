"""
通过API检查数据库连接和保安人员账号
"""

import requests
import json

def test_api_and_security_accounts():
    """通过API测试数据库连接和保安人员账号"""

    base_url = "http://127.0.0.1:5000"

    try:
        print("=== API检查数据库连接和保安账号 ===")

        # 1. 测试服务器连接
        print("1. 测试服务器连接...")
        try:
            response = requests.get(f"{base_url}/api/auth/health", timeout=10)
            if response.status_code == 200:
                print("成功: 服务器连接正常")
            else:
                print(f"警告: 服务器响应状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"失败: 服务器连接失败: {e}")
            print("请确保服务器正在运行在 http://127.0.0.1:5000")
            return False

        # 2. 测试管理员登录
        print("\n2. 测试管理员登录...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }

        try:
            login_response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=10)
            if login_response.status_code == 200:
                token = login_response.json()['access_token']
                headers = {"Authorization": f"Bearer {token}"}
                print("成功: 管理员登录成功")
            else:
                print(f"失败: 登录失败，状态码: {login_response.status_code}")
                print(f"响应内容: {login_response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"失败: 登录请求失败: {e}")
            return False

        # 3. 获取用户列表
        print("\n3. 获取用户列表...")
        try:
            users_response = requests.get(f"{base_url}/api/admin/users", headers=headers, timeout=10)
            if users_response.status_code == 200:
                users_data = users_response.json()
                total_users = len(users_data['users'])
                print(f"成功: 获取到 {total_users} 个用户")

                # 分析用户类型
                user_types = {}
                security_users = []

                for user in users_data['users']:
                    user_type = user['user_type']
                    user_types[user_type] = user_types.get(user_type, 0) + 1

                    # 查找保安人员
                    if 'security' in user_type.lower() or user_type == 'security':
                        security_users.append(user)

                print("\n4. 用户类型分布:")
                for user_type, count in sorted(user_types.items()):
                    print(f"   {user_type}: {count} 个用户")

                print(f"\n5. 保安人员账号检查:")
                if security_users:
                    print(f"成功: 找到 {len(security_users)} 个保安人员账号:")
                    for i, user in enumerate(security_users, 1):
                        print(f"   {i}. 用户名: {user['username']}")
                        print(f"      真实姓名: {user['real_name']}")
                        print(f"      邮箱: {user['email']}")
                        print(f"      手机号: {user['phone']}")
                        print(f"      用户类型: {user['user_type']}")
                        print(f"      状态: {user['status']}")
                        print(f"      可拜访: {user['is_visitable']}")
                        print(f"      创建时间: {user['created_at']}")
                        print()
                else:
                    print("警告: 未找到保安人员账号")
                    print("建议: 可以通过管理界面添加保安人员账号")

                # 6. 测试创建保安账号
                print("6. 测试创建保安账号...")
                test_security_data = {
                    "username": "test_security_api",
                    "real_name": "API测试保安",
                    "email": "test_security_api@example.com",
                    "phone": "13800138999",
                    "password": "test123456",
                    "user_type": "security",
                    "status": "active"
                }

                create_response = requests.post(f"{base_url}/api/admin/users", headers=headers, json=test_security_data, timeout=10)

                if create_response.status_code == 200:
                    new_user = create_response.json()['user']
                    print(f"成功: 测试保安账号创建成功")
                    print(f"   用户名: {new_user['username']}")
                    print(f"   真实姓名: {new_user['real_name']}")
                    print(f"   用户类型: {new_user['user_type']}")
                    print(f"   可拜访状态: {new_user['is_visitable']}")

                    # 删除测试账号
                    delete_response = requests.delete(f"{base_url}/api/admin/users/{new_user['id']}", headers=headers, timeout=10)
                    if delete_response.status_code == 200:
                        print("成功: 测试账号清理完成")
                    else:
                        print(f"警告: 测试账号清理失败，状态码: {delete_response.status_code}")

                    print("成功: 数据库读写功能正常")
                else:
                    print(f"失败: 创建测试保安账号失败，状态码: {create_response.status_code}")
                    print(f"错误信息: {create_response.text}")
                    return False

            else:
                print(f"失败: 获取用户列表失败，状态码: {users_response.status_code}")
                print(f"响应内容: {users_response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"失败: API请求失败: {e}")
            return False

        print("\n=== API检查完成 ===")
        return True

    except Exception as e:
        print(f"失败: 检查过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_api_and_security_accounts()
    if success:
        print("\nAPI检查通过！数据库连接和保安账号功能正常！")
    else:
        print("\nAPI检查发现问题，请查看上述错误信息！")