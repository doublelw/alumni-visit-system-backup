#!/usr/bin/env python3
import requests
import json
import time

# 1. 管理员登录获取token
login_url = "http://127.0.0.1:5000/api/auth/login"
login_data = {
    "username": "admin",
    "password": "admin123"
}

print("=== Admin Login ===")
response = requests.post(login_url, json=login_data)
if response.status_code == 200:
    token = response.json()['access_token']
    print(f"Login successful, got token: {token[:20]}...")
else:
    print(f"Login failed: {response.text}")
    exit(1)

# 2. Create new user
create_url = "http://127.0.0.1:5000/api/admin/users"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

user_data = {
    "username": "test_user_fix_" + str(int(time.time())),
    "password": "test123",
    "real_name": "Test User Fixed",
    "user_type": "teacher",
    "email": f"test_fixed_{int(time.time())}@school.edu.cn",
    "phone": f"138{int(time.time()) % 100000000:08d}",
    "employee_id": f"T{int(time.time()) % 10000:04d}"
}

print("\n=== Creating Test User ===")
print(f"Request data: {json.dumps(user_data, indent=2)}")

response = requests.post(create_url, headers=headers, json=user_data)
print(f"Response status: {response.status_code}")
print(f"Response content: {response.text}")

if response.status_code == 201:
    print("User created successfully!")
    user_info = response.json()['user']
    print(f"User ID: {user_info['id']}")
    print(f"Username: {user_info['username']}")
    print(f"User type: {user_info['user_type']}")
else:
    print("User creation failed")