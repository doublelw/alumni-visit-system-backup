#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试visit-applications API
"""

import requests
import json

# 配置
BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/api/auth/login'
VISIT_APPS_URL = f'{BASE_URL}/api/visits/applications'

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

def test_visit_api(token):
    """测试visit-applications API"""
    headers = {'Authorization': f'Bearer {token}'}

    print("[INFO] 测试无状态参数:")
    response = requests.get(VISIT_APPS_URL, headers=headers)
    print(f"[INFO] 状态码: {response.status_code}")
    print(f"[INFO] 响应: {response.text}")

    if response.status_code == 200:
        data = response.json()
        apps = data.get('applications', [])
        print(f"[INFO] 找到 {len(apps)} 个申请")

        print("\n[INFO] 测试pending状态:")
        response = requests.get(f'{VISIT_APPS_URL}?status=pending', headers=headers)
        print(f"[INFO] 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            apps = data.get('applications', [])
            print(f"[INFO] 找到 {len(apps)} 个pending申请")
            for app in apps:
                print(f"  - ID: {app['id']}, 申请人: {app.get('applicant', {}).get('real_name', 'N/A')}, 目标: {app['target_person']}")
        else:
            print(f"[ERROR] 获取pending申请失败: {response.text}")

def main():
    """主函数"""
    print("=== 测试visit-applications API ===\n")

    # 1. teacher01登录
    print("1. teacher01登录...")
    teacher_token = login_as_user('teacher01', '123456')
    if not teacher_token:
        return

    # 2. 测试API
    print("\n2. 测试API...")
    test_visit_api(teacher_token)

if __name__ == '__main__':
    main()
