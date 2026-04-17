#!/usr/bin/env python3
"""
测试API访问权限
"""
import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:5001/api"

def test_authentication():
    """测试认证状态"""
    print("=== 测试API访问权限 ===")

    # 首先测试登录
    print("\n1. 测试登录...")
    login_data = {
        "username": "liuwei",
        "password": "Symmetry66787687"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"登录响应状态: {response.status_code}")

        if response.status_code == 200:
            login_result = response.json()
            print(f"登录响应完整内容: {login_result}")
            token = login_result.get('access_token')
            print(f"登录成功，获得token: {token[:20]}..." if token else "登录成功但未获得token")

            # 使用token访问受保护的API
            print("\n2. 使用token访问访问申请API...")
            headers = {"Authorization": f"Bearer {token}"}

            applications_response = requests.get(
                f"{BASE_URL}/visits/applications?per_page=3",
                headers=headers
            )
            print(f"访问申请API状态: {applications_response.status_code}")

            if applications_response.status_code == 200:
                apps_data = applications_response.json()
                print(f"成功获取数据，申请数量: {len(apps_data.get('applications', []))}")
            else:
                print(f"API调用失败: {applications_response.text}")

        else:
            print(f"登录失败: {response.text}")

    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    test_authentication()