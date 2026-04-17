#!/usr/bin/env python3
"""
测试认证脚本
"""
import requests
import json

# 测试用户登录
def test_login():
    print("=== 测试用户登录 ===")

    # 首先检查是否有测试用户
    try:
        response = requests.get('http://127.0.0.1:5000/api/auth/test')
        print(f"API测试端点: {response.json()}")
    except Exception as e:
        print(f"API不可用: {e}")
        return

    # 尝试登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        response = requests.post('http://127.0.0.1:5000/api/auth/login',
                               json=login_data)
        print(f"登录响应状态码: {response.status_code}")
        print(f"登录响应内容: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"获取到token: {token[:20]}..." if token else "未获取到token")

            # 测试token是否有效
            if token:
                test_profile(token)

        else:
            print("登录失败")

    except Exception as e:
        print(f"登录请求失败: {e}")

def test_profile(token):
    print("\n=== 测试用户profile接口 ===")

    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        response = requests.get('http://127.0.0.1:5000/api/auth/profile',
                               headers=headers)
        print(f"Profile响应状态码: {response.status_code}")
        print(f"Profile响应内容: {response.json()}")

    except Exception as e:
        print(f"Profile请求失败: {e}")

if __name__ == "__main__":
    test_login()