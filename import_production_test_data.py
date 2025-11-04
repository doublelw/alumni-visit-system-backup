#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入正式测试数据
完整的用户关系和数据流程测试
"""

import sys, os
import uuid
sys.path.append('backend')
from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from datetime import datetime, date, time

app = create_app('development')
with app.app_context():
    print("=== 导入正式测试数据 ===")

    # 1. 创建核心用户
    print("1. 创建核心用户...")

    # 学生
    student = User(
        uuid=str(uuid.uuid4()),
        username='zhang_xiaoming',
        real_name='张小明',
        user_type='student',
        email='zhang_xiaoming@student.edu.cn',
        phone='13800000001',
        student_id='2021001',
        grade='高三',
        class_id='高三1班',
        status='active'
    )
    student.set_password('student123')
    db.session.add(student)

    # 班主任
    teacher = User(
        uuid=str(uuid.uuid4()),
        username='li_laoshi',
        real_name='李老师',
        user_type='teacher',
        email='li_laoshi@school.edu.cn',
        phone='13800000002',
        employee_id='T001',
        class_id='高三1班',
        is_class_teacher=True,
        status='active'
    )
    teacher.set_password('teacher123')
    db.session.add(teacher)

    # 家长
    parent = User(
        uuid=str(uuid.uuid4()),
        username='zhang_fumu',
        real_name='张父',
        user_type='parent',
        email='zhang_fumu@parent.com',
        phone='13800000003',
        status='active'
    )
    parent.set_password('parent123')
    db.session.add(parent)

    db.session.flush()  # 获取用户ID

    # 2. 建立关系
    print("2. 建立用户关系...")
    student.student_parent_id = parent.id

    db.session.commit()

    print(f"   - 学生: {student.real_name} (ID: {student.id})")
    print(f"   - 教师: {teacher.real_name} (ID: {teacher.id})")
    print(f"   - 家长: {parent.real_name} (ID: {parent.id})")
    print(f"   - 关系: 学生家长ID = {student.student_parent_id}")

    # 3. 创建学生出校申请
    print("3. 创建学生出校申请...")

    # 申请1: 待家长知晓
    application1 = StudentExitApplication(
        student_id=student.id,
        applicant_id=student.id,
        exit_date=date(2025, 11, 3),
        exit_time_start=time(16, 0),
        exit_time_end=time(18, 0),
        exit_reason='去图书馆学习',
        destination='市图书馆',
        application_status='pending',
        parent_approval_status='pending',
        teacher_approval_status='pending'
    )
    db.session.add(application1)

    # 申请2: 待教师审批（家长已知晓）
    application2 = StudentExitApplication(
        student_id=student.id,
        applicant_id=student.id,
        exit_date=date(2025, 11, 4),
        exit_time_start=time(15, 30),
        exit_time_end=time(17, 30),
        exit_reason='去看医生',
        destination='市中心医院',
        application_status='pending',
        parent_approval_status='approved',
        parent_approval_time=datetime.now(),
        parent_approved_by=parent.id,
        parent_approval_note='已确认，注意安全',
        teacher_approval_status='pending'
    )
    db.session.add(application2)

    # 申请3: 已完成的全流程申请
    application3 = StudentExitApplication(
        student_id=student.id,
        applicant_id=student.id,
        exit_date=date(2025, 11, 2),
        exit_time_start=time(14, 0),
        exit_time_end=time(16, 0),
        exit_reason='参加课外活动',
        destination='青少年活动中心',
        application_status='approved',
        parent_approval_status='approved',
        parent_approval_time=datetime.now(),
        parent_approved_by=parent.id,
        parent_approval_note='同意参加',
        teacher_approval_status='approved',
        teacher_approval_time=datetime.now(),
        teacher_approved_by=teacher.id,
        teacher_approval_note='同意参加，注意安全'
    )
    db.session.add(application3)

    db.session.commit()

    print(f"   - 申请1: 待家长知晓 (状态: {application1.application_status})")
    print(f"   - 申请2: 待教师审批 (状态: {application2.application_status})")
    print(f"   - 申请3: 已完成全流程 (状态: {application3.application_status})")

    # 4. 验证数据
    print("\n4. 数据验证...")

    users = User.query.all()
    applications = StudentExitApplication.query.all()

    print(f"   - 总用户数: {len(users)}")
    print(f"   - 总申请数: {len(applications)}")

    for user in users:
        if user.username != 'admin':
            print(f"   - {user.user_type}: {user.real_name} (用户名: {user.username})")
            if user.user_type == 'student':
                print(f"     班级: {user.class_id}, 学号: {user.student_id}")
                print(f"     家长ID: {user.student_parent_id}")

    print("\n=== 导入完成 ===")
    print("测试账号:")
    print("- 学生: zhang_xiaoming / student123")
    print("- 教师: li_laoshi / teacher123")
    print("- 家长: zhang_fumu / parent123")
    print("- 管理员: admin / admin123")
    print("\n测试流程:")
    print("1. 家长登录 → 查看待知晓申请 → 点击'知晓'")
    print("2. 教师登录 → 查看待审批申请 → 点击'通过/拒绝'")
    print("3. 学生登录 → 查看申请状态 → 提交新申请")