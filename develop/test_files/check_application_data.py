#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查申请数据的具体内容
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

def check_application_data(token):
    """检查申请数据"""
    headers = {'Authorization': f'Bearer {token}'}

    print("[INFO] 获取申请数据...")
    response = requests.get(f'{VISIT_APPS_URL}?status=pending', headers=headers)

    if response.status_code == 200:
        data = response.json()
        apps = data.get('applications', [])
        print(f"[INFO] 找到 {len(apps)} 个待审核申请")

        for i, app in enumerate(apps[:3]):  # 只显示前3个
            print(f"\n[INFO] ===== 申请 {i+1} =====")
            print(f"[INFO] ID: {app.get('id')}")
            print(f"[INFO] 申请人: {app.get('applicant', {}).get('real_name', 'N/A')}")
            print(f"[INFO] 拜访对象 (target_person): '{app.get('target_person', 'MISSING')}'")
            print(f"[INFO] 访问事由 (visit_purpose): '{app.get('visit_purpose', 'MISSING')}'")
            print(f"[INFO] 来访电话 (visitor_phone): '{app.get('visitor_phone', 'MISSING')}'")
            print(f"[INFO] 访问日期 (visit_date): '{app.get('visit_date', 'MISSING')}'")
            print(f"[INFO] 时间开始 (visit_time_start): '{app.get('visit_time_start', 'MISSING')}'")
            print(f"[INFO] 时间结束 (visit_time_end): '{app.get('visit_time_end', 'MISSING')}'")
            print(f"[INFO] 完整数据:")
            print(json.dumps(app, indent=2, ensure_ascii=False))
    else:
        print(f"[ERROR] 获取申请失败: {response.text}")

def main():
    """主函数"""
    print("=== 检查申请数据 ===\n")

    # 1. teacher01登录
    print("1. teacher01登录...")
    teacher_token = login_as_user('teacher01', '123456')
    if not teacher_token:
        return

    # 2. 检查数据
    print("\n2. 检查申请数据...")
    check_application_data(teacher_token)

if __name__ == '__main__':
    main()