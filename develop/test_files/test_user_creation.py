#!/usr/bin/env python3
"""
测试用户创建API
"""

import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:5000/api"

def test_user_creation():
    """测试用户创建"""

    # 首先需要登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    print("正在登录...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)

    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result.get('access_token')
        print("登录成功!")

        # 测试创建用户
        user_data = {
            "username": "testuser123",
            "password": "testpass123",
            "real_name": "测试用户",
            "email": "test@example.com",
            "phone": "13800138000",
            "user_type": "teacher"
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        print("正在创建用户...")
        create_response = requests.post(f"{BASE_URL}/admin/users", json=user_data, headers=headers)

        print(f"响应状态码: {create_response.status_code}")
        print(f"响应内容: {create_response.text}")

        if create_response.status_code == 201:
            print("用户创建成功!")
        else:
            print("用户创建失败!")

    else:
        print(f"登录失败: {login_response.status_code} - {login_response.text}")

if __name__ == "__main__":
    test_user_creation()