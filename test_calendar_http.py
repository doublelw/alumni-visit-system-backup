#!/usr/bin/env python3
"""
测试Calendar API - 使用HTTP而不是HTTPS
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

        # 使用HTTP而不是HTTPS
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

        # 尝试HTTP
        http_url = 'http://127.0.0.1:5000/api/calendar/events'
        full_http_url = f"{http_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

        print(f"HTTP Request URL: {full_http_url}")

        try:
            print("Sending HTTP request...")
            response = requests.get(full_http_url, headers=headers, timeout=10)

            print(f"HTTP Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"HTTP SUCCESS! Found {len(data.get('events', []))} events")
                print(f"Response preview: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
                return True
            else:
                print(f"HTTP FAILED! Status: {response.status_code}")
                print(f"Error Response: {response.text}")
                return False

        except requests.exceptions.ConnectionError as e:
            print(f"HTTP Connection Error: {str(e)}")
            print("Flask server may not be running on HTTP port")
            return False
        except Exception as e:
            print(f"HTTP Error: {str(e)}")
            return False

        # 尝试HTTPS，但不验证证书
        print(f"\n=== 测试HTTPS (不验证证书) ===")
        https_url = 'https://127.0.0.1:5000/api/calendar/events'
        full_https_url = f"{https_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

        try:
            print("Sending HTTPS request (no verify)...")
            response = requests.get(full_https_url, headers=headers, verify=False, timeout=10)

            print(f"HTTPS Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"HTTPS SUCCESS! Found {len(data.get('events', []))} events")
                return True
            else:
                print(f"HTTPS FAILED! Status: {response.status_code}")
                print(f"Error Response: {response.text}")
                return False

        except Exception as e:
            print(f"HTTPS Error: {str(e)}")
            return False

if __name__ == '__main__':
    print("Testing Calendar API with HTTP/HTTPS...")

    success = test_calendar_http()

    if success:
        print("\nCalendar API is working!")
        print("The issue was invalid enum values in the database.")
    else:
        print("\nCalendar API still has connection issues.")