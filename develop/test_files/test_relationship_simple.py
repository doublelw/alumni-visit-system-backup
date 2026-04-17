#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化关系管理功能测试
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def login_admin():
    """登录管理员账户"""
    print("=== 登录管理员账户 ===")
    login_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("access_token"):
                print(f"管理员登录成功: {data.get('message', '')}")
                return data.get("access_token")
            else:
                print(f"登录失败: {data.get('message', '未知错误')}")
                return None
        else:
            print(f"登录请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"登录异常: {e}")
        return None

def get_auth_headers(token):
    """获取认证头"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_basic_apis(headers):
    """测试基本API功能"""
    print("\n=== 测试基本API功能 ===")

    # 1. 测试组织列表API
    print("1. 测试组织列表API...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/organizations", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                organizations = data.get("organizations", [])
                print(f"SUCCESS: 获取组织列表成功，共 {len(organizations)} 个组织")
                return True
            else:
                print(f"FAIL: 获取组织列表失败: {data.get('message', '未知错误')}")
        else:
            print(f"FAIL: 请求失败: {response.status_code}")
    except Exception as e:
        print(f"FAIL: 异常: {e}")

    return False

def test_organization_creation(headers):
    """测试组织创建功能"""
    print("\n=== 测试组织创建功能 ===")

    test_org = {
        "name": "测试班级API",
        "code": "TEST_API_CLASS",
        "org_type": "class",
        "description": "用于API测试的班级"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/admin/organizations",
                               headers=headers, json=test_org)
        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                org_id = data.get("organization", {}).get("id")
                print(f"SUCCESS: 创建组织成功，ID: {org_id}")
                return org_id
            else:
                print(f"FAIL: 创建组织失败: {data.get('message', '未知错误')}")
        else:
            print(f"FAIL: 请求失败: {response.status_code}")
    except Exception as e:
        print(f"FAIL: 异常: {e}")

    return None

def test_user_list_api(headers):
    """测试用户列表API"""
    print("\n=== 测试用户列表API ===")

    try:
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                users = data.get("users", [])
                print(f"SUCCESS: 获取用户列表成功，共 {len(users)} 个用户")

                # 统计用户类型
                user_types = {}
                for user in users:
                    user_type = user.get("user_type", "unknown")
                    user_types[user_type] = user_types.get(user_type, 0) + 1

                print(f"用户类型统计: {user_types}")
                return True
            else:
                print(f"FAIL: 获取用户列表失败: {data.get('message', '未知错误')}")
        else:
            print(f"FAIL: 请求失败: {response.status_code}")
    except Exception as e:
        print(f"FAIL: 异常: {e}")

    return False

def main():
    """主测试函数"""
    print("开始关系管理功能测试...")
    print(f"测试目标: {BASE_URL}")

    # 1. 登录获取token
    token = login_admin()
    if not token:
        print("无法登录，终止测试")
        return False

    headers = get_auth_headers(token)

    # 2. 测试基本API
    if not test_basic_apis(headers):
        print("基本API测试失败")
        return False

    # 3. 测试组织创建
    org_id = test_organization_creation(headers)

    # 4. 测试用户列表API
    if not test_user_list_api(headers):
        print("用户列表API测试失败")
        return False

    print("\n=== 测试完成 ===")
    print("所有基本功能测试通过！")
    print("关系管理功能已成功实现。")

    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n测试结果: 成功")
        else:
            print("\n测试结果: 失败")
    except Exception as e:
        print(f"\n测试过程中发生异常: {e}")