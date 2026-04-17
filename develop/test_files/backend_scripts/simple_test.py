#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试角色权限系统
"""

import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:5000"

def login(username="admin", password="admin123"):
    """登录获取token"""
    login_data = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f"Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Login request failed: {str(e)}")
        return None

def test_roles_api():
    """测试角色管理API"""
    print("=== Testing Roles API ===")

    token = login()
    if not token:
        return

    headers = {'Authorization': f'Bearer {token}'}

    # 测试获取角色列表
    try:
        response = requests.get(f"{BASE_URL}/api/roles", headers=headers)
        if response.status_code == 200:
            roles = response.json()['data']['roles']
            print(f"+ Got roles list: {len(roles)} roles")
            for role in roles:
                print(f"  - {role['display_name']}: {role['description']}")
        else:
            print(f"- Failed to get roles: {response.status_code}")
    except Exception as e:
        print(f"- Roles request failed: {str(e)}")

    # 测试获取角色统计
    try:
        response = requests.get(f"{BASE_URL}/api/roles/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()['data']
            print(f"+ Got role statistics:")
            print(f"  - Total roles: {stats['total_roles']}")
            print(f"  - Active roles: {stats['active_roles']}")
            print(f"  - Total assignments: {stats['total_assignments']}")
            print(f"  - Active assignments: {stats['active_assignments']}")

            print("  User count by role:")
            for role_stat in stats['role_stats']:
                print(f"    - {role_stat['role']['display_name']}: {role_stat['user_count']} users")
        else:
            print(f"- Failed to get role stats: {response.status_code}")
    except Exception as e:
        print(f"- Role stats request failed: {str(e)}")

def test_permission_system():
    """测试权限系统"""
    print("\n=== Testing Permission System ===")

    token = login()
    if not token:
        return

    headers = {'Authorization': f'Bearer {token}'}

    # 获取访问申请列表
    try:
        response = requests.get(f"{BASE_URL}/api/visits/applications", headers=headers)
        if response.status_code == 200:
            applications = response.json()['applications']
            if applications:
                app_id = applications[0]['id']
                print(f"+ Found application: {app_id}")

                # 测试权限检查
                response = requests.get(f"{BASE_URL}/api/visits/applications/{app_id}/permissions", headers=headers)
                if response.status_code == 200:
                    permissions = response.json()
                    print(f"+ Permission check successful:")
                    print(f"  - Can approve: {permissions['can_approve']}")
                    print(f"  - Approval role: {permissions['approval_role']}")
                    print(f"  - User roles count: {len(permissions['user_roles'])}")
                    for role in permissions['user_roles']:
                        print(f"    - {role['display_name']}: {role['permissions']}")
                else:
                    print(f"- Permission check failed: {response.status_code}")
            else:
                print("+ No applications found, creating test application...")
                create_test_application(headers)
        else:
            print(f"- Failed to get applications: {response.status_code}")
    except Exception as e:
        print(f"- Applications request failed: {str(e)}")

def create_test_application(headers):
    """创建测试访问申请"""
    application_data = {
        "visit_date": "2025-10-25",
        "visit_time_start": "10:00",
        "visit_time_end": "12:00",
        "visit_purpose": "校友活动参观",
        "target_person": "张老师",
        "target_work_id": "EMP000001"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/visits/applications", json=application_data, headers=headers)
        if response.status_code == 201:
            application = response.json()['application']
            print(f"+ Created test application: {application['id']}")
        else:
            print(f"- Failed to create application: {response.status_code}")
    except Exception as e:
        print(f"- Create application failed: {str(e)}")

if __name__ == '__main__':
    print("Starting role permission system test...")

    # 测试角色API
    test_roles_api()

    # 测试权限系统
    test_permission_system()

    print("\n=== Test Complete ===")