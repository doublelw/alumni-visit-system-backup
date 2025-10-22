#!/usr/bin/env python3
"""
测试修复后的JWT Token
"""

import sys
import os
import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from flask_jwt_extended import create_access_token, decode_token

def test_fixed_jwt():
    """测试修复后的JWT token"""
    app = create_app()

    with app.app_context():
        print("=== 测试修复后的JWT Token ===")

        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found")
            return False

        print(f"Admin用户ID: {admin_user.id}")

        # 使用字符串ID创建token - 这是修复的关键!
        token = create_access_token(identity=str(admin_user.id))
        print(f"修复后的Token: {token[:50]}...")

        try:
            # 验证token
            decoded = decode_token(token)
            print(f"Token验证成功!")
            print(f"用户ID: {decoded['sub']} (类型: {type(decoded['sub'])})")
            return True
        except Exception as e:
            print(f"Token验证失败: {str(e)}")
            return False

def test_calendar_api_fixed():
    """测试修复后的Calendar API"""
    print("\n=== 测试修复后的Calendar API ===")

    app = create_app()

    with app.app_context():
        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            return False

        # 使用字符串ID创建token
        token = create_access_token(identity=str(admin_user.id))

        # 配置请求
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # 使用localhost
        url = 'https://localhost:5000/api/calendar/events?status=published&per_page=5&sort_by=start_date&order=asc'

        try:
            session = requests.Session()
            session.proxies = {}
            session.verify = False

            response = session.get(url, headers=headers, timeout=15)

            print(f"Calendar API状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                print(f"Calendar API成功! 返回 {len(events)} 个事件")

                # 显示事件
                for i, event in enumerate(events[:3]):
                    print(f"  事件 {i+1}: {event['title'][:40]}...")
                    print(f"    类型: {event.get('event_type', 'N/A')}")
                    print(f"    状态: {event.get('status', 'N/A')}")

                pagination = data.get('pagination', {})
                print(f"分页: 第{pagination.get('page', 1)}页，共{pagination.get('total', 0)}条")

                return True
            else:
                print(f"Calendar API失败: {response.status_code}")
                print(f"错误: {response.text}")
                return False

        except Exception as e:
            print(f"请求异常: {str(e)}")
            return False

def test_login_api_fixed():
    """测试修复后的登录API"""
    print("\n=== 测试修复后的登录API ===")

    login_url = 'https://localhost:5000/api/auth/login'
    login_data = {
        'username': 'admin',
        'password': '123456'
    }

    try:
        session = requests.Session()
        session.proxies = {}
        session.verify = False

        response = session.post(login_url, json=login_data, timeout=15)

        print(f"登录状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')

            if token:
                print(f"登录成功! Token: {token[:50]}...")

                # 测试这个token
                headers = {'Authorization': f'Bearer {token}'}
                calendar_url = 'https://localhost:5000/api/calendar/events?status=published&per_page=5'

                cal_response = session.get(calendar_url, headers=headers, timeout=15)
                print(f"Calendar API状态码: {cal_response.status_code}")

                if cal_response.status_code == 200:
                    cal_data = cal_response.json()
                    events = cal_data.get('events', [])
                    print(f"Calendar API成功! 返回 {len(events)} 个事件")
                    return True
                else:
                    print(f"Calendar API失败: {cal_response.status_code}")
                    print(f"错误: {cal_response.text}")
            else:
                print("登录响应中没有token")
        else:
            print(f"登录失败: {response.status_code}")
            print(f"错误: {response.text}")

        return False

    except Exception as e:
        print(f"登录异常: {str(e)}")
        return False

if __name__ == '__main__':
    print("开始修复后的测试...")

    # 1. 测试JWT修复
    jwt_ok = test_fixed_jwt()

    # 2. 测试Calendar API修复
    api_ok = test_calendar_api_fixed()

    # 3. 测试登录API
    login_ok = test_login_api_fixed()

    print("\n" + "="*60)
    print("修复测试结果:")
    print(f"JWT修复: {'OK' if jwt_ok else 'FAIL'}")
    print(f"Calendar API修复: {'OK' if api_ok else 'FAIL'}")
    print(f"登录API修复: {'OK' if login_ok else 'FAIL'}")

    if jwt_ok and (api_ok or login_ok):
        print("\n🎉 Calendar API 500错误完全解决!")
        print("\n解决方案总结:")
        print("1. JWT Token必须使用字符串用户ID: create_access_token(identity=str(user.id))")
        print("2. 前端必须使用 https://localhost:5000 而不是 https://127.0.0.1:5000")
        print("3. Calendar API逻辑完全正常，数据也没有问题")

        print("\n需要修复的配置:")
        print("- 检查app/routes/auth.py中的登录逻辑")
        print("- 确保所有创建JWT token的地方都使用字符串ID")
        print("- 前端JavaScript中的API URL配置")

    else:
        print("\n仍有问题需要解决")