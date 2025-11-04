#!/usr/bin/env python3
"""
直接在数据库中创建测试学生
"""
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from werkzeug.security import generate_password_hash
from datetime import datetime, date, time

def create_test_student():
    app = create_app('development')

    with app.app_context():
        print("=== 创建测试学生用户 ===")

        # 检查是否已存在
        existing_student = User.query.filter_by(username='test_student').first()
        if existing_student:
            print(f"学生已存在: {existing_student.real_name} (ID: {existing_student.id})")
            return existing_student

        # 创建学生用户
        student = User(
            username='test_student',
            real_name='测试学生',
            email='student@test.com',
            phone='13800000001',
            user_type='student',
            status='active',
            student_id='STU001',
            class_id='CLASS001',
            grade='高三',
            uuid='student-uuid-001'
        )
        student.set_password('student123')

        db.session.add(student)
        db.session.commit()

        print(f"创建学生成功: {student.real_name} (ID: {student.id})")
        return student

def create_test_application(student):
    app = create_app('development')

    with app.app_context():
        print("\n=== 创建测试出校申请 ===")

        # 检查是否已有申请
        existing_app = StudentExitApplication.query.filter_by(student_id=student.id).first()
        if existing_app:
            print(f"申请已存在: ID {existing_app.id}, 状态: {existing_app.application_status}")
            return existing_app

        # 创建出校申请
        application = StudentExitApplication(
            student_id=student.id,
            applicant_id=student.id,  # 申请人就是学生自己
            exit_date=date(2025, 11, 5),
            exit_time_start=time(14, 0),
            exit_time_end=time(18, 0),
            exit_reason='回家复习',
            destination='家里',
            emergency_contact='紧急联系人',
            emergency_phone='13800000002',
            application_status='pending',
            parent_approval_status='pending',
            teacher_approval_status='pending'
        )

        db.session.add(application)
        db.session.commit()

        print(f"创建申请成功: ID {application.id}, 状态: {application.application_status}")
        return application

def test_api_endpoints():
    import requests

    print("\n=== 测试API端点 ===")

    # 1. 学生登录
    login_data = {
        "username": "test_student",
        "password": "student123"
    }

    response = requests.post('http://127.0.0.1:5000/api/auth/login', json=login_data)
    print(f"学生登录状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        user = data.get('user')
        print(f"学生登录成功: {user['real_name']} ({user['user_type']})")

        # 2. 获取学生列表
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get('http://127.0.0.1:5000/api/student-exit/students', headers=headers)
        print(f"获取学生列表状态码: {response.status_code}")

        if response.status_code == 200:
            students = response.json().get('students', [])
            print(f"找到 {len(students)} 个学生")

        # 3. 获取申请列表
        response = requests.get('http://127.0.0.1:5000/api/student-exit/applications', headers=headers)
        print(f"获取申请列表状态码: {response.status_code}")

        if response.status_code == 200:
            applications = response.json().get('applications', [])
            print(f"找到 {len(applications)} 个申请")
            for app in applications:
                print(f"  - ID: {app['id']}, 状态: {app['application_status']}, 日期: {app['exit_date']}")

        return token
    else:
        print(f"学生登录失败: {response.text}")
        return None

def main():
    print("开始创建测试数据并测试\n")

    try:
        # 1. 创建测试学生
        student = create_test_student()

        # 2. 创建测试申请
        application = create_test_application(student)

        # 3. 测试API
        token = test_api_endpoints()

        print(f"\n测试完成!")
        print(f"学生账号: test_student / student123")
        print(f"申请ID: {application.id}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()