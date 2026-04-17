#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试Calendar API 500错误 - 简化版本
"""

import sys
import os
import requests
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from flask_jwt_extended import create_access_token

def test_calendar_error():
    """测试Calendar API错误"""
    app = create_app()

    with app.app_context():
        print("=== 调试Calendar API 500错误 ===")

        # 1. 获取admin token
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found")
            return False

        token = create_access_token(identity=admin_user.id)
        print(f"Got token: {token[:50]}...")

        # 2. 测试前端完全相同的请求
        url = 'https://127.0.0.1:5000/api/calendar/events'
        params = {
            'status': 'published',
            'per_page': '5',
            'sort_by': 'start_date',
            'order': 'asc'
        }

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        full_url = f"{url}?{query_string}"

        print(f"Request URL: {full_url}")
        print(f"Headers: {headers}")

        try:
            print("Sending request...")
            response = requests.get(full_url, headers=headers, verify=False, timeout=10)

            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS! Found {len(data.get('events', []))} events")
                return True
            else:
                print(f"FAILED! Status: {response.status_code}")
                print(f"Response Text: {response.text}")

                # 尝试从响应中提取更多信息
                try:
                    error_json = response.json()
                    print(f"Error JSON: {error_json}")
                except:
                    pass

                return False

        except Exception as e:
            print(f"Request Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def check_flask_logs():
    """检查Flask日志"""
    print("\n=== 检查Flask应用状态 ===")

    # 这里我们尝试调用一个简单的健康检查端点
    try:
        app = create_app()
        with app.app_context():
            # 检查数据库连接
            from app.models.school_calendar import SchoolCalendar

            count = SchoolCalendar.query.count()
            print(f"Database connection OK, total events: {count}")

            # 检查published状态的事件
            published_count = SchoolCalendar.query.filter_by(status='published').count()
            print(f"Published events: {published_count}")

            return True

    except Exception as e:
        print(f"Flask app check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Starting Calendar API debug...")

    # 检查Flask应用状态
    flask_ok = check_flask_logs()

    # 测试API
    if flask_ok:
        api_ok = test_calendar_error()

        print(f"\nResults:")
        print(f"Flask App: {'OK' if flask_ok else 'FAIL'}")
        print(f"API Request: {'OK' if api_ok else 'FAIL'}")

        if not api_ok:
            print("\nThe 500 error is confirmed.")
            print("Next step: Check Flask server logs for detailed error information.")
    else:
        print("Flask app has issues, fix these first.")