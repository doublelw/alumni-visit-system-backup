#!/usr/bin/env python3
"""
测试学生出校申请完整流程
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# 第一步：登录获取token
def login():
    print("=== 1. 登录系统 ===")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
    print(f"登录状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        user = data.get('user')
        print(f"登录成功! 用户: {user['real_name']} ({user['user_type']})")
        return token, user
    else:
        print(f"登录失败: {response.text}")
        return None, None

# 第二步：检查学生用户
def check_students(token):
    print("\n=== 2. 检查学生用户 ===")
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(f'{BASE_URL}/api/student-exit/students', headers=headers)
    print(f"获取学生列表状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        students = data.get('students', [])
        print(f"找到 {len(students)} 个学生:")
        for student in students:
            print(f"  - ID: {student['id']}, 姓名: {student['real_name']}, 学号: {student.get('student_id', 'N/A')}")
        return students
    else:
        print(f"获取学生列表失败: {response.text}")
        return []

# 第三步：创建测试学生（如果需要）
def create_student(token):
    print("\n=== 3. 创建测试学生 ===")
    headers = {'Authorization': f'Bearer {token}'}

    student_data = {
        "username": "test_student",
        "password": "student123",
        "realName": "测试学生",
        "email": "student@test.com",
        "phone": "13800000001",
        "idCard": "110101200001011234",  # 添加身份证号
        "userType": "student",
        "studentId": "STU001",
        "className": "高三(1)班",
        "grade": "高三",
        # 添加工作信息（虽然是学生但API要求）
        "currentCity": "北京",
        "workUnit": "学校",
        "position": "学生",
        "classTeacher": "张老师",
        "graduationYear": "2026",
        "division": "理科",
        "major": "综合"
    }

    response = requests.post(f'{BASE_URL}/api/auth/register', json=student_data)
    print(f"创建学生状态码: {response.status_code}")
    print(f"创建学生响应: {response.text}")

    if response.status_code == 201:
        data = response.json()
        if data.get('success'):
            print("学生创建成功")
            return data.get('user')
        else:
            print(f"❌ 学生创建失败: {data.get('message')}")
            return None
    else:
        print(f"❌ 创建请求失败: {response.text}")
        return None

# 第四步：学生登录
def student_login():
    print("\n=== 4. 学生登录 ===")
    login_data = {
        "username": "test_student",
        "password": "student123"
    }

    response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
    print(f"学生登录状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        user = data.get('user')
        print(f"✅ 学生登录成功! 用户: {user['real_name']} ({user['user_type']})")
        return token, user
    else:
        print(f"❌ 学生登录失败: {response.text}")
        return None, None

# 第五步：提交学生出校申请
def submit_exit_application(token, student_id):
    print("\n=== 5. 提交学生出校申请 ===")
    headers = {'Authorization': f'Bearer {token}'}

    application_data = {
        "student_id": student_id,
        "exit_date": "2025-11-05",
        "exit_time_start": "14:00",
        "exit_time_end": "18:00",
        "exit_reason": "回家复习",
        "destination": "家里",
        "parent_contact": "13800000002",
        "notes": "提前回家复习备考"
    }

    response = requests.post(f'{BASE_URL}/api/student-exit/applications', json=application_data, headers=headers)
    print(f"提交申请状态码: {response.status_code}")
    print(f"提交申请响应: {response.text}")

    if response.status_code == 201:
        data = response.json()
        if data.get('success'):
            print("✅ 出校申请提交成功")
            return data.get('application')
        else:
            print(f"❌ 申请提交失败: {data.get('message')}")
            return None
    else:
        print(f"❌ 提交请求失败: {response.text}")
        return None

# 第六步：获取申请列表
def get_applications(token):
    print("\n=== 6. 获取申请列表 ===")
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(f'{BASE_URL}/api/student-exit/applications', headers=headers)
    print(f"获取申请列表状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        applications = data.get('applications', [])
        print(f"找到 {len(applications)} 个申请:")
        for app in applications:
            print(f"  - ID: {app['id']}, 学生: {app.get('student_name', 'N/A')}, 状态: {app.get('application_status', 'N/A')}, 日期: {app.get('exit_date', 'N/A')}")
        return applications
    else:
        print(f"获取申请列表失败: {response.text}")
        return []

# 主流程
def main():
    print("开始测试学生出校申请完整流程\n")

    # 1. 管理员登录
    admin_token, admin_user = login()
    if not admin_token:
        print("❌ 无法登录，终止测试")
        return

    # 2. 检查现有学生
    students = check_students(admin_token)

    # 3. 如果没有学生，创建一个
    if not students:
        print("没有找到学生，创建测试学生...")
        student_user = create_student(admin_token)
        if student_user:
            students = check_students(admin_token)

    if not students:
        print("❌ 无法创建或找到学生，终止测试")
        return

    # 选择第一个学生进行测试
    test_student = students[0]
    print(f"\n选择测试学生: {test_student['real_name']} (ID: {test_student['id']})")

    # 4. 学生登录
    student_token, student_user = student_login()
    if not student_token:
        print("❌ 学生无法登录，使用管理员token提交申请")
        student_token = admin_token

    # 5. 提交申请
    application = submit_exit_application(student_token, test_student['id'])

    # 6. 获取申请列表
    applications = get_applications(student_token)

    print("\n测试完成!")
    if applications:
        print(f"成功! 共有 {len(applications)} 个申请")
    else:
        print("没有找到申请")

if __name__ == "__main__":
    main()