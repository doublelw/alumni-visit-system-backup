#!/usr/bin/env python3
"""
测试其他API是否工作正常
"""

import sys
import os
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from flask_jwt_extended import create_access_token

def test_different_apis():
    """测试不同的API端点"""
    app = create_app()

    with app.app_context():
        print("=== 测试不同API端点 ===")

        # 获取admin token
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found")
            return False

        token = create_access_token(identity=admin_user.id)
        print(f"Got token: {token[:50]}...")

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # 测试不同的API端点
        test_endpoints = [
            {
                'name': 'Visits API',
                'url': 'https://127.0.0.1:5000/api/visits/records'
            },
            {
                'name': 'Calendar API',
                'url': 'https://127.0.0.1:5000/api/calendar/events'
            },
            {
                'name': 'Users API',
                'url': 'https://127.0.0.1:5000/api/users'
            },
            {
                'name': 'Statistics API',
                'url': 'https://127.0.0.1:5000/api/statistics/dashboard'
            }
        ]

        for endpoint in test_endpoints:
            print(f"\n测试 {endpoint['name']}: {endpoint['url']}")

            try:
                response = requests.get(endpoint['url'], headers=headers, verify=False, timeout=10)

                print(f"  状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"  成功! 响应数据: {str(data)[:100]}...")
                elif response.status_code == 404:
                    print(f"  端点不存在 (404)")
                else:
                    print(f"  失败! 状态码: {response.status_code}")
                    print(f"  错误: {response.text[:200]}...")

            except requests.exceptions.ConnectionError as e:
                print(f"  连接错误: {str(e)}")
            except requests.exceptions.Timeout as e:
                print(f"  超时错误: {str(e)}")
            except Exception as e:
                print(f"  其他错误: {str(e)}")

        return True

def test_calendar_api_without_auth():
    """测试不带认证的Calendar API"""
    print("\n=== 测试不带认证的Calendar API ===")

    url = 'https://127.0.0.1:5000/api/calendar/events'

    try:
        response = requests.get(url, verify=False, timeout=10)

        print(f"状态码: {response.status_code}")

        if response.status_code == 401:
            print("正确返回401 - 需要认证")
        elif response.status_code == 500:
            print("500错误 - 服务器内部错误")
            print(f"错误信息: {response.text}")
        else:
            print(f"意外状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}...")

    except Exception as e:
        print(f"请求失败: {str(e)}")

if __name__ == '__main__':
    print("开始测试不同API端点...")

    # 测试不同API
    test_different_apis()

    # 测试不带认证的请求
    test_calendar_api_without_auth()