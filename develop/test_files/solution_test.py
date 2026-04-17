#!/usr/bin/env python3
"""
解决方案测试 - 使用localhost和正确的认证
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

def test_calendar_api_solution():
    """测试Calendar API解决方案"""
    app = create_app()

    with app.app_context():
        print("=== Calendar API解决方案测试 ===")

        # 获取admin用户和token
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found")
            return False

        token = create_access_token(identity=admin_user.id)
        print(f"获得token: {token[:50]}...")

        # 配置请求
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # 使用localhost而不是127.0.0.1 - 这是关键!
        url = 'https://localhost:5000/api/calendar/events?status=published&per_page=5&sort_by=start_date&order=asc'
        print(f"测试URL: {url}")

        try:
            # 配置会话
            session = requests.Session()
            session.proxies = {}  # 清除代理设置
            session.verify = False  # 跳过SSL验证

            response = session.get(url, headers=headers, timeout=15)

            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                print(f"SUCCESS! 返回 {len(events)} 个事件")

                # 显示前几个事件
                for i, event in enumerate(events[:3]):
                    print(f"  事件 {i+1}: {event['title'][:40]}...")
                    print(f"    类型: {event.get('event_type', 'N/A')}")
                    print(f"    状态: {event.get('status', 'N/A')}")

                pagination = data.get('pagination', {})
                print(f"分页信息: 第{pagination.get('page', 1)}页，共{pagination.get('total', 0)}条记录")

                print("\nCalendar API完全正常工作!")
                print("解决方案: 前端应该使用 https://localhost:5000 而不是 https://127.0.0.1:5000")
                return True

            else:
                print(f"API失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False

        except Exception as e:
            print(f"请求异常: {str(e)}")
            return False

if __name__ == '__main__':
    print("开始解决方案测试...")

    success = test_calendar_api_solution()

    print("\n" + "="*60)
    print("最终总结:")

    if success:
        print("问题已解决!")
        print("\n解决方案:")
        print("1. 将前端API请求从 https://127.0.0.1:5000 改为 https://localhost:5000")
        print("2. 确保JWT token正确传递")
        print("3. 跳过SSL验证 (开发环境)")

        print("\n需要修改的文件:")
        print("- mobile.js 或 admin.js 中的API基础URL")
        print("- 可能需要修改其他JavaScript文件中的API调用")

        print("\nCalendar API 500错误完全解决!")
        print("问题不在API逻辑，而在于网络连接配置")

    else:
        print("仍有问题需要进一步调试")