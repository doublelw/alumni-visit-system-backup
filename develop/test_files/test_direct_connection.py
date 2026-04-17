#!/usr/bin/env python3
"""
测试直接连接，绕过代理
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
from flask_jwt_extended import create_access_token

def test_direct_api_connection():
    """测试直接的API连接，绕过代理"""
    app = create_app()

    with app.app_context():
        print("=== 测试直接API连接 ===")

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

        # 配置会话以绕过代理
        session = requests.Session()
        session.proxies = {}  # 清除代理设置
        session.verify = False  # 跳过SSL验证

        # 测试不同的URL格式
        test_urls = [
            ('HTTPS localhost', 'https://127.0.0.1:5000/api/calendar/events?status=published&per_page=5'),
            ('HTTPS localhost alternative', 'https://localhost:5000/api/calendar/events?status=published&per_page=5'),
            ('HTTP localhost', 'http://127.0.0.1:5000/api/calendar/events?status=published&per_page=5'),
            ('HTTP localhost alternative', 'http://localhost:5000/api/calendar/events?status=published&per_page=5')
        ]

        for name, url in test_urls:
            print(f"\n测试 {name}:")
            print(f"  URL: {url}")

            try:
                response = session.get(url, headers=headers, timeout=15)

                print(f"  状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"  成功! 返回 {len(data.get('events', []))} 个事件")
                    print(f"  第一个事件: {data['events'][0]['title'][:30]}...")
                    return True
                else:
                    print(f"  失败! 状态码: {response.status_code}")
                    print(f"  错误信息: {response.text[:200]}...")

            except requests.exceptions.SSLError as e:
                print(f"  SSL错误: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                print(f"  连接错误: {str(e)}")
            except requests.exceptions.Timeout as e:
                print(f"  超时错误: {str(e)}")
            except Exception as e:
                print(f"  其他错误: {str(e)}")

        return False

def test_flask_direct():
    """直接在Flask应用内测试API"""
    app = create_app()

    with app.test_client() as client:
        print("\n=== 使用Flask测试客户端 ===")

        # 获取admin token
        with app.app_context():
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("Admin user not found")
                return False

            token = create_access_token(identity=admin_user.id)
            print(f"Got token: {token[:50]}...")

        # 设置认证头
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # 测试Calendar API
        print("测试Calendar API...")
        response = client.get('/api/calendar/events?status=published&per_page=5', headers=headers)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.get_json()
            print(f"成功! 返回 {len(data.get('events', []))} 个事件")
            print(f"第一个事件: {data['events'][0]['title'][:30]}...")
            return True
        else:
            print(f"失败! 状态码: {response.status_code}")
            print(f"错误信息: {response.get_data(as_text=True)[:200]}...")
            return False

if __name__ == '__main__':
    print("开始测试直接连接...")

    # 先测试Flask内部测试客户端
    flask_ok = test_flask_direct()

    if flask_ok:
        print("\nFlask测试客户端成功，API逻辑正常")
        print("问题在于网络连接层面")
    else:
        print("\nFlask测试客户端失败，API逻辑有问题")

    # 测试外部连接
    print("\n" + "="*50)
    external_ok = test_direct_api_connection()

    if external_ok:
        print("\n找到可用的外部连接方式!")
    else:
        print("\n所有外部连接都失败")

    print("\n=== 问题总结 ===")
    if flask_ok and not external_ok:
        print("1. API逻辑完全正常")
        print("2. 问题在于HTTPS/网络连接配置")
        print("3. 建议解决方案:")
        print("   - 修改前端使用HTTP而不是HTTPS")
        print("   - 或者修复Flask的SSL配置")
        print("   - 或者检查网络代理设置")
    elif not flask_ok and not external_ok:
        print("1. API逻辑本身有问题")
        print("2. 需要修复代码问题")
    else:
        print("1. 一切正常工作")
        print("2. 可能是间歇性问题")