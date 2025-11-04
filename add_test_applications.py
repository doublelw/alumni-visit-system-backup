#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加测试申请数据
"""

import sys, os
import uuid
from datetime import datetime, date, time
sys.path.append('backend')
from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication

app = create_app('development')
with app.app_context():
    print("=== 添加测试申请数据 ===")

    # 获取现有用户
    student = User.query.filter_by(username='zhang_xiaoming').first()
    teacher = User.query.filter_by(username='li_laoshi').first()
    parent = User.query.filter_by(username='zhang_fumu').first()

    if not student or not teacher or not parent:
        print("❌ 缺少必要的用户，请先运行导入脚本")
        exit(1)

    print(f"找到用户:")
    print(f"  - 学生: {student.real_name} (ID: {student.id})")
    print(f"  - 教师: {teacher.real_name} (ID: {teacher.id})")
    print(f"  - 家长: {parent.real_name} (ID: {parent.id})")

    # 清理现有申请
    existing_apps = StudentExitApplication.query.all()
    print(f"\n删除 {len(existing_apps)} 个现有申请...")
    for app_data in existing_apps:
        db.session.delete(app_data)
    db.session.commit()

    # 创建测试申请
    print("\n创建测试申请...")

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

    # 验证数据
    applications = StudentExitApplication.query.all()
    print(f"\n=== 数据验证 ===")
    print(f"总申请数: {len(applications)}")

    for app in applications:
        print(f"申请ID {app.id}: {app.exit_reason} - {app.application_status}")

    print("\n🎉 测试数据添加完成！")
    print("\n测试账号:")
    print("- 学生: zhang_xiaoming / student123")
    print("- 教师: li_laoshi / teacher123")
    print("- 家长: zhang_fumu / parent123")
    print("- 管理员: admin / admin123")
    print("\n测试流程:")
    print("1. 家长登录 → 查看待知晓申请 → 点击'知晓'")
    print("2. 教师登录 → 查看待审批申请 → 点击'通过/拒绝'")
    print("3. 学生登录 → 查看申请状态 → 提交新申请")