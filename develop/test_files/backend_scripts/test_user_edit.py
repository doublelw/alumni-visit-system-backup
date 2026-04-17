#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户编辑API
"""

import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:5000"

def login():
    """登录获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f"Login failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Login request failed: {str(e)}")
        return None

def test_user_edit_api():
    """测试用户编辑API"""
    print("=== 测试用户编辑API ===")

    token = login()
    if not token:
        return

    headers = {'Authorization': f'Bearer {token}'}

    # 测试获取用户列表
    try:
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        if response.status_code == 200:
            users = response.json()['users']
            if users:
                test_user = users[0]
                user_id = test_user['id']
                print(f"+ 获取用户列表成功，测试用户ID: {user_id}")

                # 测试获取单个用户信息
                response = requests.get(f"{BASE_URL}/api/admin/users/{user_id}", headers=headers)
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"+ 获取用户信息成功: {user_data['user']['real_name']}")

                    # 测试更新用户信息
                    update_data = {
                        "real_name": f"测试用户_{user_id}",
                        "phone": f"1380000{user_id:04d}",
                        "user_type": test_user['user_type'],
                        "status": test_user['status']
                    }

                    response = requests.put(
                        f"{BASE_URL}/api/admin/users/{user_id}",
                        json=update_data,
                        headers=headers
                    )

                    if response.status_code == 200:
                        print("+ 更新用户信息成功")
                    else:
                        print(f"- 更新用户信息失败: {response.status_code}")
                        print(response.text)
                else:
                    print(f"- 获取用户信息失败: {response.status_code}")
            else:
                print("- 没有找到测试用户")
        else:
            print(f"- 获取用户列表失败: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"- API请求失败: {str(e)}")

def test_roles_api():
    """测试角色API"""
    print("\n=== 测试角色API ===")

    token = login()
    if not token:
        return

    headers = {'Authorization': f'Bearer {token}'}

    # 测试获取用户列表
    try:
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        if response.status_code == 200:
            users = response.json()['users']
            if users:
                test_user = users[0]
                user_id = test_user['id']
                print(f"+ 测试用户ID: {user_id}")

                # 测试获取用户角色
                response = requests.get(f"{BASE_URL}/api/roles/user/{user_id}", headers=headers)
                if response.status_code == 200:
                    roles_data = response.json()
                    print(f"+ 获取用户角色成功，角色数量: {len(roles_data['data']['roles'])}")
                else:
                    print(f"- 获取用户角色失败: {response.status_code}")
                    print(response.text)

                # 测试获取所有角色
                response = requests.get(f"{BASE_URL}/api/roles", headers=headers)
                if response.status_code == 200:
                    all_roles = response.json()['data']['roles']
                    print(f"+ 获取所有角色成功，总角色数量: {len(all_roles)}")

                    if all_roles:
                        # 测试分配角色
                        test_role = all_roles[0]
                        assign_data = {
                            "user_id": user_id,
                            "role_id": test_role['id']
                        }

                        response = requests.post(
                            f"{BASE_URL}/api/roles/assign",
                            json=assign_data,
                            headers=headers
                        )

                        if response.status_code == 201:
                            print(f"+ 分配角色成功: {test_role['display_name']}")
                        else:
                            print(f"- 分配角色失败: {response.status_code}")
                            print(response.text)
                else:
                    print(f"- 获取所有角色失败: {response.status_code}")
            else:
                print("- 没有找到测试用户")
        else:
            print(f"- 获取用户列表失败: {response.status_code}")

    except Exception as e:
        print(f"- 角色API请求失败: {str(e)}")

if __name__ == '__main__':
    test_user_edit_api()
    test_roles_api()
    print("\n=== 测试完成 ===")