#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试统计数据API
"""

import requests
import json

# 配置
BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/api/auth/login'

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

def test_statistics_api(token):
    """测试统计数据API"""
    headers = {'Authorization': f'Bearer {token}'}

    print("[INFO] 测试访客申请统计数据...")

    # 测试待审核申请
    print("\n1. 测试访客待审核申请...")
    response = requests.get(f'{BASE_URL}/api/visits/applications?status=pending&per_page=1', headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"[INFO] 访客待审核响应结构:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
        print(f"[INFO] pagination.total: {data.get('pagination', {}).get('total', 'MISSING')}")
        print(f"[INFO] 直接total: {data.get('total', 'MISSING')}")
    else:
        print(f"[ERROR] 访客待审核请求失败: {response.text}")

    # 测试学生出校申请
    print("\n2. 测试学生出校待审核申请...")
    response = requests.get(f'{BASE_URL}/api/student-exit/applications?status=pending&per_page=1', headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"[INFO] 学生出校待审核响应结构:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
        print(f"[INFO] pagination.total: {data.get('pagination', {}).get('total', 'MISSING')}")
        print(f"[INFO] 直接total: {data.get('total', 'MISSING')}")
    else:
        print(f"[ERROR] 学生出校待审核请求失败: {response.text}")

def main():
    """主函数"""
    print("=== 测试统计数据API ===\n")

    # 1. teacher01登录
    print("1. teacher01登录...")
    teacher_token = login_as_user('teacher01', '123456')
    if not teacher_token:
        return

    # 2. 测试统计数据API
    print("\n2. 测试统计数据API...")
    test_statistics_api(teacher_token)

if __name__ == '__main__':
    main()
