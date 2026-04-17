#!/usr/bin/env python3
"""
简单API测试 - 先创建用户再测试
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash
import requests
import json

def create_test_user():
    """创建测试用户"""
    app = create_app()
    with app.app_context():
        # 检查是否已存在测试用户
        test_user = User.query.filter_by(username='test_alumni').first()
        if test_user:
            print("Test user already exists")
            return True

        # 创建测试用户
        test_user = User(
            username='test_alumni',
            email='test@example.com',
            real_name='Test User',
            phone='1234567890',
            user_type='alumni',
            status='active'
        )
        test_user.set_password('test123')

        db.session.add(test_user)
        db.session.commit()
        print("Test user created successfully")
        return True

def test_api():
    """测试API"""
    base_url = "http://127.0.0.1:5001"

    print("=== 创建测试用户 ===")
    create_test_user()

    print("\n=== 测试登录 ===")
    login_data = {
        "username": "test_alumni",
        "password": "test123"
    }

    try:
        response = requests.post(f"{base_url}/api/auth/login",
                               json=login_data,
                               timeout=5,
                               proxies={'http': None, 'https': None})
        print(f"Login status: {response.status_code}")

        if response.status_code == 200:
            login_result = response.json()
            access_token = login_result.get('access_token')
            print("Login successful!")

            print("\n=== 测试访问申请API ===")
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(f"{base_url}/api/visits/applications?per_page=3",
                                  headers=headers,
                                  timeout=5,
                                  proxies={'http': None, 'https': None})

            print(f"Visit applications API status: {response.status_code}")

            if response.status_code == 200:
                applications_data = response.json()
                print("SUCCESS: Visit applications API works!")
                print(f"Data: {json.dumps(applications_data, indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"FAILED: Visit applications API returned {response.status_code}")
                print(f"Response: {response.text}")
                return False

        else:
            print(f"Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"Request exception: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")