#!/usr/bin/env python3
"""
测试前端API调用，模拟前端获取最近申请的过程
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import requests
import json

def test_frontend_api_calls():
    base_url = "http://localhost:5000"

    # 1. 先登录获取token
    login_data = {
        "username": "student001",
        "password": "test123456"
    }

    try:
        print("正在登录...")
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"登录状态: {login_response.status_code}")

        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('access_token')
            print(f"获取到token: {token[:20]}...")

            # 2. 测试访问申请API
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            print(f"\n=== 测试访问申请API ===")
            visit_response = requests.get(f"{base_url}/api/visits/applications?per_page=3", headers=headers)
            print(f"访问申请API状态: {visit_response.status_code}")
            if visit_response.status_code == 200:
                visit_data = visit_response.json()
                print(f"访问申请数量: {len(visit_data.get('applications', []))}")
                for app in visit_data.get('applications', []):
                    print(f"- {app.get('visit_purpose', 'N/A')} ({app.get('application_date', 'N/A')})")
            else:
                print(f"访问申请API失败: {visit_response.text}")

            # 3. 测试学生出校申请API
            print(f"\n=== 测试学生出校申请API ===")
            student_exit_response = requests.get(f"{base_url}/api/student-exit/applications/recent", headers=headers)
            print(f"学生出校申请API状态: {student_exit_response.status_code}")
            if student_exit_response.status_code == 200:
                student_exit_data = student_exit_response.json()
                print(f"学生出校申请数量: {len(student_exit_data.get('applications', []))}")
                for app in student_exit_data.get('applications', []):
                    print(f"- {app.get('reason', 'N/A')} (ID: {app.get('id', 'N/A')}, 状态: {app.get('status', 'N/A')})")
            else:
                print(f"学生出校申请API失败: {student_exit_response.text}")

            # 4. 模拟前端合并数据的过程
            print(f"\n=== 模拟前端数据合并 ===")
            all_applications = []

            # 添加访问申请
            if visit_response.status_code == 200:
                visit_data = visit_response.json()
                visit_apps = visit_data.get('applications', [])
                visit_apps_mapped = [{
                    'application_type': 'visit',
                    'application_status': app.get('application_status') or app.get('status'),
                    'visit_date': app.get('visit_date') or app.get('application_date'),
                    'visit_purpose': app.get('visit_purpose'),
                    'visit_time': app.get('visit_time'),
                    'id': app.get('id'),
                    'purpose': app.get('visit_purpose')  # 映射字段
                } for app in visit_apps]
                all_applications.extend(visit_apps_mapped)
                print(f"访问申请映射后: {len(visit_apps_mapped)} 个")

            # 添加学生出校申请
            if student_exit_response.status_code == 200:
                student_exit_data = student_exit_response.json()
                student_apps = student_exit_data.get('applications', [])
                student_apps_mapped = [{
                    'application_type': 'student_exit',
                    'application_status': app.get('status'),
                    'visit_date': app.get('exit_date'),  # 映射字段
                    'visit_purpose': app.get('reason'),   # 映射字段
                    'visit_time': app.get('exit_time'),   # 映射字段
                    'id': app.get('id'),
                    'purpose': app.get('reason'),         # 映射字段
                    'applicant_name': app.get('student_name') or app.get('applicant_name')
                } for app in student_apps]
                all_applications.extend(student_apps_mapped)
                print(f"学生出校申请映射后: {len(student_apps_mapped)} 个")

            print(f"\n合并后总申请数: {len(all_applications)}")
            print("所有申请:")
            for i, app in enumerate(all_applications, 1):
                app_type = "学生出校" if app.get('application_type') == 'student_exit' else "访问申请"
                print(f"{i}. [{app_type}] {app.get('purpose', 'N/A')} - {app.get('visit_date', 'N/A')} - 状态: {app.get('application_status', 'N/A')}")

        else:
            print(f"登录失败: {login_response.text}")

    except Exception as e:
        print(f"测试出错: {e}")

if __name__ == '__main__':
    test_frontend_api_calls()