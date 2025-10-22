#!/usr/bin/env python3
"""
测试管理员登录
"""

import requests
import json
import sys
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def test_admin_login():
    """测试管理员登录"""

    login_url = 'https://127.0.0.1:5000/api/auth/login'
    dashboard_url = 'https://127.0.0.1:5000/api/admin/dashboard'

    # 登录数据
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }

    try:
        print("=== 测试管理员登录 ===")

        # 第一步：登录
        print("1. 尝试登录...")
        response = requests.post(login_url, json=login_data, verify=False)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            login_result = response.json()
            print("登录成功!")
            print(f"用户信息: {json.dumps(login_result.get('user', {}), indent=2, ensure_ascii=False)}")

            token = login_result.get('access_token')
            if token:
                print(f"Token长度: {len(token)}")

                # 第二步：使用token访问管理界面
                print("\n2. 尝试访问管理仪表板...")
                headers = {'Authorization': f'Bearer {token}'}
                dashboard_response = requests.get(dashboard_url, headers=headers, verify=False)

                print(f"仪表板状态码: {dashboard_response.status_code}")

                if dashboard_response.status_code == 200:
                    print("仪表板访问成功!")
                    dashboard_data = dashboard_response.json()
                    print(f"仪表板数据: {json.dumps(dashboard_data, indent=2, ensure_ascii=False)}")
                else:
                    print("仪表板访问失败!")
                    print(f"错误信息: {dashboard_response.text}")
            else:
                print("未获取到访问令牌")
        else:
            print("登录失败!")
            print(f"错误信息: {response.text}")

    except requests.exceptions.SSLError:
        print("SSL连接错误 - 请检查服务器是否正在运行HTTPS")
    except requests.exceptions.ConnectionError:
        print("连接错误 - 请检查服务器是否正在运行")
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == '__main__':
    test_admin_login()