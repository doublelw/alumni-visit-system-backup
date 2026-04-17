#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接测试审批API
"""

import requests
import json

# 配置
BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/api/auth/login'
APPROVE_URL = f'{BASE_URL}/api/visits/applications/3/approve'

def login_as_user(username, password):
    """用户登录"""
    response = requests.post(LOGIN_URL, json={
        'username': username,
        'password': password
    })

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] {username} 登录成功")
        return data['access_token']
    else:
        print(f"[ERROR] {username} 登录失败: {response.text}")
        return None

def test_approval(token):
    """测试审批API"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    data = {
        'approve': True,
        'note': '直接测试审批通过'
    }

    print("[INFO] 测试审批申请ID: 3")
    response = requests.post(APPROVE_URL, headers=headers, json=data)

    print(f"[INFO] 状态码: {response.status_code}")
    print(f"[INFO] 响应: {response.text}")

    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 审批成功: {result['message']}")
        return True
    else:
        print(f"[ERROR] 审批失败")
        return False

def main():
    """主函数"""
    print("=== 直接测试审批API ===\n")

    # 1. 以教师身份登录
    print("1. 教师登录...")
    teacher_token = login_as_user('teacher01', '123456')
    if not teacher_token:
        return

    # 2. 测试审批
    print("\n2. 测试审批...")
    success = test_approval(teacher_token)

    if success:
        print("\n[OK] 审批API测试成功")
    else:
        print("\n[ERROR] 审批API测试失败")

if __name__ == '__main__':
    main()