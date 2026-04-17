#!/usr/bin/env python3
"""
简单的学生出校申请提交测试
"""

import requests
import json

def test_simple_submit():
    base_url = "http://localhost:5000"

    # 1. 登录
    login_response = requests.post(f"{base_url}/api/auth/login", json={
        "username": "student001",
        "password": "test123456"
    })

    if login_response.status_code != 200:
        print(f"登录失败: {login_response.status_code} - {login_response.text}")
        return

    token = login_response.json()['access_token']
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"登录成功，Token: {token[:50]}...")

    # 2. 测试简单的申请提交
    application_data = {
        "student_id": 6,
        "exit_date": "2025-11-04",
        "exit_time_start": "14:00",
        "exit_time_end": "18:00",
        "exit_reason": "测试申请",
        "destination": "测试目的地",
        "transport_method": "步行",
        "emergency_contact": "测试联系人",
        "emergency_phone": "13800138000"
    }

    print("提交申请数据:")
    print(json.dumps(application_data, indent=2, ensure_ascii=False))

    submit_response = requests.post(
        f"{base_url}/api/student-exit/applications",
        headers=headers,
        json=application_data
    )

    print(f"\n提交响应状态码: {submit_response.status_code}")
    print(f"提交响应内容: {submit_response.text}")

    if submit_response.status_code == 201:
        print("✅ 申请提交成功!")
    elif submit_response.status_code == 500:
        print("❌ 服务器内部错误")
    elif submit_response.status_code == 403:
        print("❌ 权限不足")
    elif submit_response.status_code == 400:
        print("❌ 请求参数错误")
    else:
        print(f"❌ 其他错误: {submit_response.status_code}")

if __name__ == "__main__":
    test_simple_submit()