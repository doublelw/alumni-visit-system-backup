#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试审批功能脚本
"""

import requests
import json

# 配置
BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/api/auth/login'
VISIT_APPS_URL = f'{BASE_URL}/api/visit-applications'
APPROVE_URL_TEMPLATE = f'{BASE_URL}/api/visits/applications/{{}}/approve'

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
        return apps
    else:
        print(f"[ERROR] 获取申请失败: {response.text}")
        return []

def approve_application(token, app_id, approve=True, note=''):
    """审批申请"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    data = {
        'approve': approve,
        'note': note
    }

    url = APPROVE_URL_TEMPLATE.format(app_id)
    print(f"[INFO] 正在审批申请 {app_id} (通过: {approve})")

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 审批成功: {result['message']}")
        return True
    else:
        print(f"[ERROR] 审批失败: {response.text}")
        return False

def main():
    """主函数"""
    print("=== 测试审批功能 ===\n")

    # 1. 以家长身份登录并创建申请
    print("1. 家长登录...")
    parent_token = login_as_user('parent01', '123456')
    if not parent_token:
        return

    # 3. 以教师身份登录并审批
    print("\n3. 教师登录并审批...")
    teacher_token = login_as_user('teacher01', '123456')
    if not teacher_token:
        return

    # 2. 获取待审批申请（使用教师权限）
    print("\n2. 获取待审批申请...")
    pending_apps = get_pending_applications(teacher_token)
    if not pending_apps:
        print("[ERROR] 没有找到待审批申请")
        return

    app_id = pending_apps[0]['id']

    # 4. 审批申请
    print("\n4. 执行审批...")
    success = approve_application(teacher_token, app_id, approve=True, note='测试审批通过')

    if success:
        print("\n[OK] 审批测试完成")

        # 5. 验证审批结果
        print("\n5. 验证审批结果...")
        updated_apps = get_pending_applications(parent_token)
        approved_count = len([app for app in updated_apps if app.get('application_status') == 'approved'])
        print(f"[INFO] 已通过申请数量: {approved_count}")
    else:
        print("\n[ERROR] 审批测试失败")

if __name__ == '__main__':
    main()