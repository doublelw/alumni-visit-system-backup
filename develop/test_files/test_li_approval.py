#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试李老师的审批功能
"""

import requests
import json

# 配置
BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/api/auth/login'
VISIT_APPS_URL = f'{BASE_URL}/api/visit-applications'
APPROVE_URL = f'{BASE_URL}/api/visits/applications/4/approve'

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

def get_pending_applications(token):
    """获取待审批申请"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{VISIT_APPS_URL}?status=pending', headers=headers)

    if response.status_code == 200:
        data = response.json()
        apps = data.get('applications', [])
        print(f"[INFO] 找到 {len(apps)} 个待审批申请")
        for app in apps:
            print(f"  - ID: {app['id']}, 申请人: {app['applicant_name']}, 目标: {app['target_person']}")
            print(f"    can_approve: {app.get('can_approve', 'N/A')}")
        return apps
    else:
        print(f"[ERROR] 获取申请失败: {response.text}")
        return []

def test_approval(token):
    """测试审批API"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    data = {
        'approve': True,
        'note': '李老师测试审批通过'
    }

    print("[INFO] 测试审批申请ID: 4")
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
    print("=== 测试李老师审批功能 ===\n")

    # 1. teacher01登录
    print("1. teacher01登录...")
    li_token = login_as_user('teacher01', '123456')
    if not li_token:
        return

    # 2. 获取待审批申请
    print("\n2. 获取待审批申请...")
    pending_apps = get_pending_applications(li_token)
    if not pending_apps:
        print("[ERROR] 没有找到待审批申请")
        return

    # 3. 测试审批
    print("\n3. 测试审批...")
    success = test_approval(li_token)

    if success:
        print("\n[OK] 李老师审批测试成功")
    else:
        print("\n[ERROR] 李老师审批测试失败")

if __name__ == '__main__':
    main()