#!/usr/bin/env python3
"""
测试学生出校申请API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import requests
import json

def test_api():
    base_url = "http://localhost:5000"

    # 1. 先登录获取token
    login_data = {
        "username": "student001",
        "password": "test123456"
    }

    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"登录状态: {login_response.status_code}")

        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('access_token')
            print(f"获取到token: {token[:20]}...")

            # 2. 测试最近申请API
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            recent_response = requests.get(f"{base_url}/api/student-exit/applications/recent", headers=headers)
            print(f"\n最近申请API状态: {recent_response.status_code}")

            if recent_response.status_code == 200:
                data = recent_response.json()
                print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            else:
                print(f"API错误: {recent_response.text}")

        else:
            print(f"登录失败: {login_response.text}")

    except Exception as e:
        print(f"测试出错: {e}")

if __name__ == '__main__':
    test_api()