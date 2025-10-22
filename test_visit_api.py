#!/usr/bin/env python3
"""
测试访问申请API
"""
import requests
import json

def test_visit_api():
    """测试访问申请API"""
    base_url = "http://127.0.0.1:5001"

    print("=== 测试访问申请API ===")

    # 1. 先测试登录
    print("1. 测试登录...")
    login_data = {
        "username": "test_alumni",
        "password": "test123"
    }

    try:
        response = requests.post(f"{base_url}/api/auth/login",
                               json=login_data,
                               timeout=5,
                               proxies={'http': None, 'https': None})
        print(f"登录响应状态码: {response.status_code}")

        if response.status_code == 200:
            login_result = response.json()
            access_token = login_result.get('access_token')
            print("登录成功!")

            # 2. 测试访问申请API
            print("\n2. 测试访问申请API...")
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # 测试获取访问申请列表
            response = requests.get(f"{base_url}/api/visits/applications?per_page=3",
                                  headers=headers,
                                  timeout=5,
                                  proxies={'http': None, 'https': None})

            print(f"访问申请API状态码: {response.status_code}")

            if response.status_code == 200:
                applications_data = response.json()
                print("✅ 访问申请API调用成功!")
                print(f"返回数据: {json.dumps(applications_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 访问申请API调用失败: {response.status_code}")
                print(f"错误信息: {response.text}")

        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"错误信息: {response.text}")

    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_visit_api()