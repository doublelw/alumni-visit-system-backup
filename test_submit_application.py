#!/usr/bin/env python3
"""
测试提交学生出校申请
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

import requests
import json
from datetime import datetime, date, time

def test_submit_application():
    base_url = "http://localhost:5000"

    # 1. 登录获取token
    login_data = {
        "username": "student001",
        "password": "test123456"
    }

    try:
        print("正在登录...")
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)

        if login_response.status_code != 200:
            print(f"登录失败: {login_response.text}")
            return

        token_data = login_response.json()
        token = token_data.get("access_token")
        print(f"登录成功，获取到token")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 2. 获取学生信息
        print("获取学生信息...")
        student_response = requests.get(f"{base_url}/api/student-exit/students", headers=headers)

        if student_response.status_code != 200:
            print(f"获取学生信息失败: {student_response.text}")
            return

        student_data = student_response.json()
        if not student_data.get("success") or not student_data.get("students"):
            print("没有找到学生信息")
            return

        students = student_data["students"]
        student = students[0]  # 使用第一个学生
        print(f"找到学生: {student["name"]} (ID: {student["id"]})")

        # 3. 提交新的学生出校申请 (11月4号)
        print("提交新的学生出校申请...")

        application_data = {
            "student_id": student["id"],
            "exit_date": "2025-11-04",
            "exit_time_start": "14:00",
            "exit_time_end": "18:00",
            "exit_reason": "测试提交 - 11月4日下午出校办事",
            "destination": "市区",
            "transport_method": "地铁",
            "emergency_contact": "紧急联系人",
            "emergency_phone": "13800138000"
        }

        submit_response = requests.post(
            f"{base_url}/api/student-exit/applications",
            headers=headers,
            json=application_data
        )

        print(f"提交状态码: {submit_response.status_code}")
        print(f"提交响应: {submit_response.text}")

        if submit_response.status_code == 200:
            result = submit_response.json()
            if result.get("message"):
                print(f"✅ 申请提交成功: {result["message"]}")
                if "application_id" in result:
                    print(f"申请ID: {result["application_id"]}")
            else:
                print("❌ 申请提交失败")
        else:
            print(f"❌ 申请提交失败: {submit_response.status_code}")
            try:
                error_data = submit_response.json()
                print(f"错误信息: {error_data.get("error", "未知错误")}")
            except:
                print(f"错误响应: {submit_response.text}")

        # 4. 验证申请是否保存
        print("\n验证申请是否保存到数据库...")
        recent_response = requests.get(f"{base_url}/api/student-exit/applications/recent", headers=headers)

        if recent_response.status_code == 200:
            recent_data = recent_response.json()
            if recent_data.get("success") and recent_data.get("applications"):
                applications = recent_data["applications"]
                print(f"当前数据库中有 {len(applications)} 个申请:")
                for i, app in enumerate(applications, 1):
                    print(f"  {i}. ID:{app["id"]} - {app["reason"]} - {app["exit_date"]} - 状态:{app["application_status"]}")

                # 检查是否有我们刚提交的申请
                new_app = next((app for app in applications if app["exit_date"] == "2025-11-04"), None)
                if new_app:
                    print("✅ 新申请已成功保存到数据库")
                else:
                    print("❌ 新申请未在数据库中找到")
            else:
                print("没有找到任何申请")
        else:
            print(f"获取最近申请失败: {recent_response.status_code}")

    except Exception as e:
        print(f"测试过程出错: {e}")

if __name__ == "__main__":
    test_submit_application()
