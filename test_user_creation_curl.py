#!/usr/bin/env python3
"""
使用curl测试用户创建API
"""

import subprocess
import json
import requests

def test_with_requests():
    """使用requests库测试用户创建"""
    API_BASE_URL = "http://127.0.0.1:5000/api"

    print("=== 使用requests库测试 ===")

    # 1. 首先登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    print("正在登录...")
    login_response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data)

    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result.get('access_token')
        print(f"登录成功！获取到token: {token[:50]}...")

        # 2. 创建用户
        user_data = {
            "username": "testuser456",
            "password": "testpass456",
            "real_name": "测试用户456",
            "email": "test456@example.com",
            "phone": "13800138001",
            "user_type": "teacher"
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        print(f"\n正在创建用户: {user_data['username']}")
        create_response = requests.post(f"{API_BASE_URL}/admin/users", json=user_data, headers=headers)

        print(f"响应状态码: {create_response.status_code}")
        print(f"响应内容: {create_response.text}")

        if create_response.status_code == 201:
            print("✅ 用户创建成功!")
        else:
            print("❌ 用户创建失败!")
    else:
        print(f"❌ 登录失败: {login_response.status_code}")
        print(f"错误信息: {login_response.text}")

def test_with_curl():
    """使用curl命令测试"""
    print("\n=== 使用curl命令测试 ===")

    # 登录获取token
    login_cmd = '''curl -X POST http://127.0.0.1:5000/api/auth/login \\
    -H "Content-Type: application/json" \\
    -d '{"username": "admin", "password": "admin123"}'''

    print("执行登录命令...")
    try:
        result = subprocess.run(login_cmd, shell=True, capture_output=True, text=True)
        print(f"登录响应: {result.stdout}")

        if result.returncode == 0:
            try:
                login_data = json.loads(result.stdout)
                token = login_data.get('access_token')
                if token:
                    print(f"获取到token: {token[:50]}...")

                    # 创建用户
                    user_data = {
                        "username": "testuser789",
                        "password": "testpass789",
                        "real_name": "测试用户789",
                        "email": "test789@example.com",
                        "phone": "13800138002",
                        "user_type": "teacher"
                    }

                    create_cmd = f'''curl -X POST http://127.0.0.1:5000/api/admin/users \\
                    -H "Authorization: Bearer {token}" \\
                    -H "Content-Type: application/json" \\
                    -d '{json.dumps(user_data)}' '''

                    print(f"\n执行创建用户命令...")
                    create_result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
                    print(f"创建用户响应: {create_result.stdout}")

                    if create_result.returncode == 0:
                        print("✅ curl测试完成!")
                    else:
                        print(f"❌ curl测试失败: {create_result.stderr}")

            except json.JSONDecodeError as e:
                print(f"解析登录响应失败: {e}")
        else:
            print(f"curl登录失败: {result.stderr}")
    except Exception as e:
        print(f"执行curl命令失败: {e}")

if __name__ == "__main__":
    test_with_requests()
    test_with_curl()