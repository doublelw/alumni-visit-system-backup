#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试教师创建学生出校码API
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_teacher_login():
    """测试教师登录"""
    print("\n" + "="*80)
    print("步骤1: 测试教师登录")
    print("="*80)

    url = f"{BASE_URL}/api/wechat/teacher/login"
    data = {
        "phone": "13800000001",
        "password": "1234"
    }

    print(f"URL: {url}")
    print(f"数据: {json.dumps(data, ensure_ascii=False)}")

    response = requests.post(url, json=data)
    print(f"\n状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            return result['data']['token']
    return None

def test_create_student_code(token):
    """测试创建学生出校码"""
    print("\n" + "="*80)
    print("步骤2: 测试创建学生出校码")
    print("="*80)

    url = f"{BASE_URL}/api/wechat/teacher/create-student-code"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "student_name": "王明",
        "student_id": "2024001",
        "visit_purpose": "return",
        "note": "测试"
    }

    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    print(f"数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

    response = requests.post(url, headers=headers, json=data)
    print(f"\n状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    return response.status_code == 200

def main():
    print("="*80)
    print("教师创建学生出校码 API 测试")
    print("="*80)

    # 步骤1: 登录
    token = test_teacher_login()
    if not token:
        print("\n❌ 登录失败，无法继续测试")
        return

    # 步骤2: 创建学生码
    success = test_create_student_code(token)
    if success:
        print("\n✅ 创建学生码成功")
    else:
        print("\n❌ 创建学生码失败")

if __name__ == '__main__':
    main()
