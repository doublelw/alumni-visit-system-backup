#!/usr/bin/env python3
"""
测试公开Calendar API
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

def test_public_calendar_api():
    """测试公开Calendar API"""
    app = create_app()

    with app.app_context():
        print("=== 测试公开Calendar API ===")

        # 使用localhost
        base_url = 'https://localhost:5000'

        # 测试公开API（不需要认证）
        print("1. 测试公开API（不需要认证）...")
        public_url = f"{base_url}/api/calendar/public/events?status=published&per_page=5"

        try:
            session = requests.Session()
            session.proxies = {}
            session.verify = False

            response = session.get(public_url, timeout=15)

            print(f"   状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                print(f"   ✅ 公开API成功! 返回 {len(events)} 个事件")

                # 显示前两个事件
                for i, event in enumerate(events[:2]):
                    print(f"     事件 {i+1}: {event['title'][:30]}...")

                return True
            else:
                print(f"   ❌ 公开API失败: {response.status_code}")
                print(f"   错误: {response.text[:200]}...")

        except Exception as e:
            print(f"   ❌ 请求异常: {str(e)}")

        return False

def test_private_calendar_api():
    """测试私有Calendar API（需要认证）"""
    app = create_app()

    with app.app_context():
        print("\n2. 测试私有API（需要认证）...")

        # 获取admin用户和token
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("   Admin user not found")
            return False

        token = create_access_token(identity=str(admin_user.id))

        base_url = 'https://localhost:5000'
        private_url = f"{base_url}/api/calendar/events?status=published&per_page=5"

        try:
            session = requests.Session()
            session.proxies = {}
            session.verify = False

            headers = {'Authorization': f'Bearer {token}'}
            response = session.get(private_url, headers=headers, timeout=15)

            print(f"   状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                print(f"   ✅ 私有API成功! 返回 {len(events)} 个事件")
                return True
            else:
                print(f"   ❌ 私有API失败: {response.status_code}")
                print(f"   错误: {response.text[:200]}...")

        except Exception as e:
            print(f"   ❌ 请求异常: {str(e)}")

        return False

def test_unauthorized_private_api():
    """测试未认证的私有API访问"""
    print("\n3. 测试未认证的私有API访问...")

    base_url = 'https://localhost:5000'
    private_url = f"{base_url}/api/calendar/events?status=published&per_page=5"

    try:
        session = requests.Session()
        session.proxies = {}
        session.verify = False

        response = session.get(private_url, timeout=15)

        print(f"   状态码: {response.status_code}")

        if response.status_code == 401:
            print("   ✅ 正确返回401 - 需要认证")
            return True
        else:
            print(f"   ❌ 应该返回401，但返回了: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")
        return False

if __name__ == '__main__':
    print("开始测试公开Calendar API...")

    # 测试公开API
    public_ok = test_public_calendar_api()

    # 测试私有API
    private_ok = test_private_calendar_api()

    # 测试未认证访问
    unauthorized_ok = test_unauthorized_private_api()

    print("\n" + "="*60)
    print("测试结果:")
    print(f"公开API: {'✅ OK' if public_ok else '❌ FAIL'}")
    print(f"私有API: {'✅ OK' if private_ok else '❌ FAIL'}")
    print(f"未认证检查: {'✅ OK' if unauthorized_ok else '❌ FAIL'}")

    if public_ok and private_ok and unauthorized_ok:
        print("\n🎉 所有API测试通过!")
        print("前端现在应该可以正常加载活动数据了。")
    else:
        print("\n❌ 仍有API问题需要解决")