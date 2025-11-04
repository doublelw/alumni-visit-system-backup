#!/usr/bin/env python3
"""
直接测试API接口
"""

import requests
import json

def test_api():
    """测试API接口"""
    BASE_URL = "http://localhost:5000"

    print("=== 直接测试API接口 ===")

    # 测试登录API
    login_url = f"{BASE_URL}/api/auth/login"

    test_accounts = [
        {'username': 'admin', 'password': 'admin123'},
        {'username': 'security01', 'password': '123456'},
        {'username': 'teacher01', 'password': '123456'},
    ]

    for account in test_accounts:
        print(f"\n--- 测试账号: {account['username']} ---")

        login_data = {
            "username": account['username'],
            "password": account['password']
        }

        try:
            response = requests.post(login_url, json=login_data)
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print(f"登录成功: {data.get('message', '')}")
                print(f"Token: {data.get('access_token', 'N/A')[:20]}...")
                print(f"用户信息: {data.get('user', {}).get('real_name', 'N/A')}")
            else:
                try:
                    error_data = response.json()
                    print(f"登录失败: {error_data.get('error', '未知错误')}")
                except:
                    print(f"登录失败: HTTP {response.status_code}")
                    print(f"响应内容: {response.text[:200]}")

        except Exception as e:
            print(f"请求异常: {e}")

    return True

if __name__ == "__main__":
    test_api()