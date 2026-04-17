#!/usr/bin/env python3
"""
测试角色权限系统的功能
"""

import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:5000"

def test_roles_api():
    """测试角色管理API"""
    print("=== 测试角色管理API ===")

    # 登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            print("+ 管理员登录成功")
        else:
            print(f"- 登录失败: {response.status_code}")
            return
    except Exception as e:
        print(f"- 登录请求失败: {str(e)}")
        return

    # 测试获取角色列表
    try:
        response = requests.get(f"{BASE_URL}/api/roles", headers=headers)
        if response.status_code == 200:
            roles = response.json()['data']['roles']
            print(f"✓ 获取角色列表成功，共 {len(roles)} 个角色")
            for role in roles:
                print(f"  - {role['display_name']}: {role['description']}")
        else:
            print(f"✗ 获取角色列表失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"✗ 角色列表请求失败: {str(e)}")

    # 测试获取角色统计
    try:
        response = requests.get(f"{BASE_URL}/api/roles/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()['data']
            print(f"✓ 获取角色统计成功:")
            print(f"  - 总角色数: {stats['total_roles']}")
            print(f"  - 活跃角色数: {stats['active_roles']}")
            print(f"  - 总分配数: {stats['total_assignments']}")
            print(f"  - 活跃分配数: {stats['active_assignments']}")

            print("  各角色用户数:")
            for role_stat in stats['role_stats']:
                print(f"    - {role_stat['role']['display_name']}: {role_stat['user_count']} 人")
        else:
            print(f"✗ 获取角色统计失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 角色统计请求失败: {str(e)}")

def test_permission_system():
    """测试权限系统"""
    print("\n=== 测试权限系统 ===")

    # 登录管理员
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            admin_token = response.json()['access_token']
            admin_headers = {'Authorization': f'Bearer {admin_token}'}
            print("✓ 管理员登录成功")
        else:
            print(f"✗ 管理员登录失败: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 管理员登录请求失败: {str(e)}")
        return

    # 创建一个测试访问申请
    application_data = {
        "visit_date": "2025-10-25",
        "visit_time_start": "10:00",
        "visit_time_end": "12:00",
        "visit_purpose": "校友活动参观",
        "target_person": "张老师",
        "target_work_id": "EMP000001"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/visits/applications",
                               json=application_data, headers=admin_headers)
        if response.status_code == 201:
            application = response.json()['application']
            application_id = application['id']
            print(f"✓ 创建测试访问申请成功，ID: {application_id}")
        else:
            print(f"✗ 创建访问申请失败: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 创建访问申请请求失败: {str(e)}")
        return

    # 测试权限检查API
    try:
        response = requests.get(f"{BASE_URL}/api/visits/applications/{application_id}/permissions",
                              headers=admin_headers)
        if response.status_code == 200:
            permissions = response.json()
            print(f"✓ 获取权限信息成功:")
            print(f"  - 可审批: {permissions['can_approve']}")
            print(f"  - 审批角色: {permissions['approval_role']}")
            print(f"  - 用户角色数: {len(permissions['user_roles'])}")
            for role in permissions['user_roles']:
                print(f"    - {role['display_name']}: {role['permissions']}")
        else:
            print(f"✗ 获取权限信息失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 权限检查请求失败: {str(e)}")

    # 测试不同权限级别的审批
    test_approval_scenarios(application_id, admin_headers)

def test_approval_scenarios(application_id, admin_headers):
    """测试不同审批场景"""
    print("\n=== 测试审批场景 ===")

    scenarios = [
        {
            "name": "校友活动申请",
            "purpose": "校友活动聚会",
            "expected_role": "校友活动组织者"
        },
        {
            "name": "社团活动申请",
            "purpose": "社团招新活动",
            "expected_role": "社团管理员"
        },
        {
            "name": "校园活动申请",
            "purpose": "校园开放日活动",
            "expected_role": "活动管理员"
        },
        {
            "name": "普通教师拜访",
            "purpose": "拜访老师请教问题",
            "expected_role": "教师或访问审批人"
        }
    ]

    for scenario in scenarios:
        print(f"\n测试场景: {scenario['name']}")

        # 更新访问申请的访问目的
        update_data = {
            "visit_purpose": scenario['purpose']
        }

        try:
            response = requests.put(f"{BASE_URL}/api/visits/applications/{application_id}",
                                  json=update_data, headers=admin_headers)
            if response.status_code == 200:
                print(f"  ✓ 更新访问目的: {scenario['purpose']}")
            else:
                print(f"  ✗ 更新访问目的失败: {response.status_code}")
                continue
        except Exception as e:
            print(f"  ✗ 更新请求失败: {str(e)}")
            continue

        # 检查权限
        try:
            response = requests.get(f"{BASE_URL}/api/visits/applications/{application_id}/permissions",
                                  headers=admin_headers)
            if response.status_code == 200:
                permissions = response.json()
                print(f"  ✓ 权限检查 - 可审批: {permissions['can_approve']}")
                print(f"  ✓ 审批角色: {permissions['approval_role']}")
            else:
                print(f"  ✗ 权限检查失败: {response.status_code}")
        except Exception as e:
            print(f"  ✗ 权限检查失败: {str(e)}")

if __name__ == '__main__':
    print("开始测试角色权限系统...")

    # 测试角色API
    test_roles_api()

    # 测试权限系统
    test_permission_system()

    print("\n=== 测试完成 ===")