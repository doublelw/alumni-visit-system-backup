#!/usr/bin/env python3
"""
简单的数据库查询测试
"""
import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:5001/api"

def test_simple_query():
    """测试简单的数据库查询"""
    print("=== 测试简单数据库查询 ===")

    # 登录获取token
    print("\n1. 登录...")
    login_data = {
        "username": "liuwei",
        "password": "Symmetry66787687"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"登录响应状态: {response.status_code}")

        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get('access_token')
            print(f"登录成功，获得token: {token[:20]}..." if token else "登录成功但未获得token")

            # 测试简单的用户信息API
            print("\n2. 测试用户信息API...")
            headers = {"Authorization": f"Bearer {token}"}

            user_response = requests.get(f"{BASE_URL}/auth/user", headers=headers)
            print(f"用户信息API状态: {user_response.status_code}")

            if user_response.status_code == 200:
                print("用户信息API正常")
            else:
                print(f"用户信息API失败: {user_response.text}")

            # 测试访问申请API，但只获取第一页，每页1条记录
            print("\n3. 测试访问申请API（限制数量）...")

            applications_response = requests.get(
                f"{BASE_URL}/visits/applications?page=1&per_page=1",
                headers=headers
            )
            print(f"访问申请API状态: {applications_response.status_code}")

            if applications_response.status_code == 200:
                apps_data = applications_response.json()
                print(f"成功获取数据，申请数量: {len(apps_data.get('applications', []))}")
                print(f"返回数据: {apps_data}")
            else:
                print(f"API调用失败: {applications_response.text}")

        else:
            print(f"登录失败: {response.text}")

    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    test_simple_query()