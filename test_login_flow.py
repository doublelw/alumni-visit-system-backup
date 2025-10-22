#!/usr/bin/env python3
"""
测试完整的登录流程
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

def test_jwt_token_generation():
    """测试JWT token生成和验证"""
    app = create_app()

    with app.app_context():
        print("=== 测试JWT Token生成和验证 ===")

        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found")
            return False

        print(f"Admin用户ID: {admin_user.id}")
        print(f"Admin用户类型: {admin_user.user_type}")

        # 生成token
        token = create_access_token(identity=admin_user.id)
        print(f"生成的Token: {token}")

        try:
            # 验证token
            decoded = decode_token(token)
            print(f"Token验证成功: {decoded}")
            print(f"用户ID: {decoded['sub']}")
            return True
        except Exception as e:
            print(f"Token验证失败: {str(e)}")
            return False

def test_login_api():
    """测试登录API"""
    print("\n=== 测试登录API ===")

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
        print(f"登录响应: {response.text}")

        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')

            if token:
                print(f"登录成功! 获得Token: {token[:50]}...")

                # 立即测试这个token
                return test_calendar_with_token(token)
            else:
                print("登录响应中没有token")
                return False
        else:
            print(f"登录失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"登录请求异常: {str(e)}")
        return False

def test_calendar_with_token(token):
    """使用获得的token测试Calendar API"""
    print("\n=== 使用登录Token测试Calendar API ===")

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    url = 'https://localhost:5000/api/calendar/events?status=published&per_page=5'

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

            # 显示前几个事件
            for i, event in enumerate(events[:2]):
                print(f"  事件 {i+1}: {event['title'][:30]}...")

            return True
        else:
            print(f"Calendar API失败: {response.status_code}")
            print(f"错误: {response.text}")
            return False

    except Exception as e:
        print(f"Calendar API请求异常: {str(e)}")
        return False

def test_admin_user_status():
    """检查admin用户状态"""
    app = create_app()

    with app.app_context():
        print("\n=== 检查Admin用户状态 ===")

        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f"用户名: {admin_user.username}")
            print(f"用户类型: {admin_user.user_type}")
            print(f"邮箱: {admin_user.email}")
            print(f"状态: {admin_user.status}")
            print(f"创建时间: {admin_user.created_at}")
            return True
        else:
            print("Admin用户不存在")
            return False

if __name__ == '__main__':
    print("开始完整登录流程测试...")

    # 1. 检查admin用户状态
    user_ok = test_admin_user_status()

    # 2. 测试JWT token生成
    jwt_ok = test_jwt_token_generation()

    # 3. 测试完整的登录流程
    if user_ok and jwt_ok:
        login_ok = test_login_api()

        print("\n" + "="*60)
        print("测试结果:")
        print(f"Admin用户: {'OK' if user_ok else 'FAIL'}")
        print(f"JWT生成: {'OK' if jwt_ok else 'FAIL'}")
        print(f"登录流程: {'OK' if login_ok else 'FAIL'}")

        if login_ok:
            print("\n解决方案确认:")
            print("1. 使用 https://localhost:5000 (不是127.0.0.1)")
            print("2. 通过正常登录流程获得token")
            print("3. Calendar API完全正常工作")
        else:
            print("\n需要进一步调试登录问题")
    else:
        print("基础检查失败，需要修复用户或JWT配置")