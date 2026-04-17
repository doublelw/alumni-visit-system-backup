#!/usr/bin/env python3
"""
测试API接口
"""

import sys
import os
import requests
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from flask_jwt_extended import create_access_token

def get_admin_token():
    """获取管理员token"""
    app = create_app()

    with app.app_context():
        # 查找admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found")
            return None

        # 创建token
        token = create_access_token(identity=admin_user.id)
        return token

def test_api(api_url, token):
    """测试API"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        print(f"\nTesting API: {api_url}")
        response = requests.get(api_url, headers=headers, verify=False)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
        else:
            print(f"Error Response: {response.text}")

    except Exception as e:
        print(f"Request failed: {str(e)}")

def main():
    print("=== API Testing ===")

    # 获取token
    token = get_admin_token()
    if not token:
        print("Failed to get admin token")
        return

    print(f"Admin token: {token[:50]}...")

    # 测试各个API
    apis_to_test = [
        "https://127.0.0.1:5000/api/calendar/events?status=published&per_page=5&sort_by=start_date&order=asc",
        "https://127.0.0.1:5000/api/visits/applications?page=1&per_page=20",
        "https://127.0.0.1:5000/api/visits/records?page=1&per_page=20",
        "https://127.0.0.1:5000/api/admin/statistics",
        "https://127.0.0.1:5000/api/admin/dashboard"
    ]

    for api_url in apis_to_test:
        test_api(api_url, token)

if __name__ == '__main__':
    main()