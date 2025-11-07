#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建测试访问申请
"""

import requests
import json
from datetime import datetime, timedelta

# 配置
BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/api/auth/login'
CREATE_VISIT_URL = f'{BASE_URL}/api/visits/applications'

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

def create_visit_application(token):
    """创建访问申请"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # 设置访问时间为明天
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    data = {
        'visit_date': tomorrow,
        'visit_time_start': '09:00',
        'visit_time_end': '11:00',
        'target_person': '王老师',
        'target_person_id': 25,
        'visit_purpose': '家访交流学生学习情况',
        'notes': '测试创建的访问申请'
    }

    print(f"[INFO] 创建访问申请，日期: {tomorrow}")
    response = requests.post(CREATE_VISIT_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 访问申请创建成功，申请ID: {result.get('application', {}).get('id')}")
        return True
    else:
        print(f"[ERROR] 创建访问申请失败: {response.text}")
        return False

def main():
    """主函数"""
    print("=== 创建测试访问申请 ===\n")

    # 1. 以家长身份登录
    print("1. 家长登录...")
    parent_token = login_as_user('parent01', '123456')
    if not parent_token:
        return

    # 2. 创建访问申请
    print("\n2. 创建访问申请...")
    success = create_visit_application(parent_token)

    if success:
        print("\n[OK] 测试申请创建完成")
    else:
        print("\n[ERROR] 测试申请创建失败")

if __name__ == '__main__':
    main()