#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试学生出校申请详情API
"""

import requests
import json

# 配置
BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/api/auth/login'
STUDENT_EXIT_DETAIL_URL = f'{BASE_URL}/api/student-exit/applications/7'  # 使用ID=7的申请

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

def test_student_exit_detail(token):
    """测试学生出校申请详情"""
    headers = {'Authorization': f'Bearer {token}'}

    print("[INFO] 获取学生出校申请详情...")
    # 先获取申请列表，找到一个有效的ID
    list_url = 'http://127.0.0.1:5000/api/student-exit/applications?status=rejected'
    list_response = requests.get(list_url, headers=headers)

    if list_response.status_code == 200:
        list_data = list_response.json()
        if list_data.get('applications') and len(list_data['applications']) > 0:
            app_id = list_data['applications'][0]['id']
            detail_url = f'http://127.0.0.1:5000/api/student-exit/applications/{app_id}'
            print(f"[INFO] 使用申请ID: {app_id}")
            response = requests.get(detail_url, headers=headers)
        else:
            print("[ERROR] 没有找到申请")
            return
    else:
        print(f"[ERROR] 获取申请列表失败: {list_response.text}")
        return

    if response.status_code == 200:
        data = response.json()
        print(f"[INFO] API响应成功")
        print(f"[INFO] 完整响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        if 'application' in data:
            app = data['application']
            print(f"\n[INFO] ===== 申请数据 =====")
            print(f"[INFO] ID: {app.get('id')}")
            print(f"[INFO] applicant_name: '{app.get('applicant_name', 'MISSING')}'")
            print(f"[INFO] student_name: '{app.get('student_name', 'MISSING')}'")
            print(f"[INFO] exit_date: '{app.get('exit_date', 'MISSING')}'")
            print(f"[INFO] application_type: '{app.get('application_type', 'MISSING')}'")
            print(f"[INFO] class_name: '{app.get('class_name', 'MISSING')}'")

            # 检查applicant对象
            if 'applicant' in app:
                applicant = app['applicant']
                print(f"[INFO] applicant对象: {applicant}")
                if applicant and 'real_name' in applicant:
                    print(f"[INFO] applicant.real_name: '{applicant['real_name']}'")
    else:
        print(f"[ERROR] 获取申请详情失败: {response.text}")

def main():
    """主函数"""
    print("=== 测试学生出校申请详情API ===\n")

    # 1. teacher01登录
    print("1. teacher01登录...")
    teacher_token = login_as_user('teacher01', '123456')
    if not teacher_token:
        return

    # 2. 测试详情API
    print("\n2. 测试详情API...")
    test_student_exit_detail(teacher_token)

if __name__ == '__main__':
    main()