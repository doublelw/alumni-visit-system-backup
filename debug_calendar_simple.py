#!/usr/bin/env python3
"""
调试Calendar API - 简化版本
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

def test_calendar_http():
    """测试Calendar API HTTP请求"""
    app = create_app()

    with app.app_context():
        print("=== 测试Calendar API HTTP请求 ===")

        # 获取admin token
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found")
            return False

        token = create_access_token(identity=admin_user.id)
        print(f"Got admin token: {token[:50]}...")

        # 模拟JavaScript请求
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

        url = 'https://127.0.0.1:5000/api/calendar/events'
        full_url = f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

        print(f"Request URL: {full_url}")

        try:
            print("Sending request...")
            response = requests.get(full_url, headers=headers, verify=False, timeout=10)

            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS! Response: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
                return True
            else:
                print(f"FAILED! Status: {response.status_code}")
                print(f"Error Response: {response.text}")
                return False

        except Exception as e:
            print(f"Request Error: {str(e)}")
            return False

def test_calendar_direct():
    """直接测试Calendar API逻辑"""
    app = create_app()

    with app.app_context():
        print("\n=== 直接测试Calendar API逻辑 ===")

        try:
            from app.models.school_calendar import SchoolCalendar

            # 模拟API查询
            query = SchoolCalendar.query.filter_by(status='published')
            query = query.order_by(SchoolCalendar.start_date.asc())

            pagination = query.paginate(page=1, per_page=5, error_out=False)

            print(f"Query Success: {pagination.total} total records")

            # 测试to_dict
            events_list = []
            for event in pagination.items:
                event_dict = event.to_dict()
                events_list.append(event_dict)
                print(f"Event: {event_dict['title']} - {event_dict['event_type']}")

            print(f"All events converted: {len(events_list)}")
            return True

        except Exception as e:
            print(f"Direct test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("Starting Calendar API debug...")

    direct_success = test_calendar_direct()
    http_success = test_calendar_http()

    print(f"\nResults:")
    print(f"Direct API logic: {'PASS' if direct_success else 'FAIL'}")
    print(f"HTTP request: {'PASS' if http_success else 'FAIL'}")

    if direct_success and not http_success:
        print("\nConclusion: API logic works, but HTTP request fails")
    elif not direct_success:
        print("\nConclusion: API logic itself has problems")
    else:
        print("\nConclusion: Calendar API works perfectly!")