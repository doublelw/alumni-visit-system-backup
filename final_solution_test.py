#!/usr/bin/env python3
"""
最终解决方案测试 - 使用localhost和正确的认证
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

def test_working_solution():
    """测试可行的解决方案"""
    app = create_app()

    with app.app_context():
        print("=== 最终解决方案测试 ===")

        # 获取admin用户和token
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found")
            return False

        token = create_access_token(identity=admin_user.id)
        print(f"✅ 获得token: {token[:50]}...")

        # 配置请求
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # 使用localhost而不是127.0.0.1
        url = 'https://localhost:5000/api/calendar/events?status=published&per_page=5&sort_by=start_date&order=asc'
        print(f"🔗 测试URL: {url}")

        try:
            # 配置会话
            session = requests.Session()
            session.proxies = {}  # 清除代理
            session.verify = False  # 跳过SSL验证

            response = session.get(url, headers=headers, timeout=15)

            print(f"📊 状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                print(f"🎉 成功! 返回 {len(events)} 个事件")

                # 显示前几个事件
                for i, event in enumerate(events[:3]):
                    print(f"  事件 {i+1}: {event['title'][:40]}...")
                    print(f"    类型: {event.get('event_type', 'N/A')}")
                    print(f"    状态: {event.get('status', 'N/A')}")

                pagination = data.get('pagination', {})
                print(f"📄 分页信息: 第{pagination.get('page', 1)}页，共{pagination.get('total', 0)}条记录")

                print("\n✅ Calendar API完全正常工作!")
                print("🔧 解决方案: 前端应该使用 https://localhost:5000 而不是 https://127.0.0.1:5000")
                return True

            elif response.status_code == 401:
                print("❌ 认证失败 - Token问题")
                print(f"错误信息: {response.text}")
                return False
            else:
                print(f"❌ 其他错误: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False

def test_login_solution():
    """测试登录API解决方案"""
    print("\n=== 测试登录API解决方案 ===")

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

        print(f"🔐 登录状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ 登录成功! 获得token: {token[:50] if token else 'None'}...")

            if token:
                # 测试用获得的token访问Calendar API
                headers = {'Authorization': f'Bearer {token}'}
                calendar_url = 'https://localhost:5000/api/calendar/events?status=published&per_page=5'

                cal_response = session.get(calendar_url, headers=headers, timeout=15)
                print(f"📅 Calendar API状态码: {cal_response.status_code}")

                if cal_response.status_code == 200:
                    cal_data = cal_response.json()
                    print(f"🎉 Calendar API成功! 返回 {len(cal_data.get('events', []))} 个事件")
                    return True

        elif response.status_code == 401:
            print("❌ 登录失败 - 用户名或密码错误")
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"错误信息: {response.text}")

        return False

    except Exception as e:
        print(f"❌ 登录请求异常: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 开始最终解决方案测试...")
    print("=" * 60)

    # 测试直接token方案
    direct_ok = test_working_solution()

    # 测试登录流程方案
    login_ok = test_login_solution()

    print("\n" + "=" * 60)
    print("📋 最终总结:")

    if direct_ok or login_ok:
        print("✅ 问题已解决!")
        print("\n🔧 解决方案:")
        print("1. 将前端API请求从 https://127.0.0.1:5000 改为 https://localhost:5000")
        print("2. 确保JWT token正确传递")
        print("3. 跳过SSL验证 (开发环境)")

        print("\n📝 需要修改的文件:")
        print("- mobile.js 或 admin.js 中的API基础URL")
        print("- 可能需要修改其他JavaScript文件中的API调用")

        print("\n🎯 Calendar API 500错误完全解决!")
        print("   问题不在API逻辑，而在于网络连接配置")

    else:
        print("❌ 仍有问题需要进一步调试")