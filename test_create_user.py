#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试管理员创建用户API
"""

import requests
import json

# 1. 管理员登录获取token
login_url = "http://127.0.0.1:5000/api/auth/login"
login_data = {
    "username": "admin",
    "password": "admin123"
}

print("=== 管理员登录 ===")
response = requests.post(login_url, json=login_data)
if response.status_code == 200:
    token = response.json()['access_token']
    print(f"登录成功，获取token: {token[:20]}...")
else:
    print(f"登录失败: {response.text}")
    exit(1)

# 2. 创建新用户
create_url = "http://127.0.0.1:5000/api/admin/users"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

user_data = {
    "username": "test_teacher_new",
    "password": "test123",
    "real_name": "Test Teacher",
    "user_type": "teacher",
    "email": "test_new@school.edu.cn",
    "phone": "13800000099",
    "employee_id": "T999",
    "class_id": "Class 3-2",
    "is_class_teacher": True
}

print("\n=== 创建测试用户 ===")
print(f"请求数据: {json.dumps(user_data, indent=2)}")

response = requests.post(create_url, headers=headers, json=user_data)
print(f"响应状态: {response.status_code}")
print(f"响应内容: {response.text}")

if response.status_code == 201:
    print("✅ 用户创建成功！")
    user_info = response.json()['user']
    print(f"用户ID: {user_info['id']}")
    print(f"用户名: {user_info['username']}")
    print(f"用户类型: {user_info['user_type']}")
else:
    print("❌ 用户创建失败")