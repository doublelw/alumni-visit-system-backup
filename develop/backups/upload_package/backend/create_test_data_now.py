#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试数据脚本
"""

import sys
import os
from datetime import datetime, timedelta, date, time
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath('.'))))

from app import create_app, db
from app.models import User, AlumniProfile, VisitApplication, Vehicle, FaceData

def create_test_users():
    """创建测试用户"""
    app = create_app()
    with app.app_context():
        print("👥 创建测试用户...")

        # 创建教师用户
        teacher_users = [
            {
                'username': 'teacher001',
                'password': 'teacher123',
                'real_name': '张老师',
                'email': 'zhang@school.edu.cn',
                'phone': '13810001001',
                'user_type': 'teacher'
            },
            {
                'username': 'teacher002',
                'password': 'teacher123',
                'real_name': '李老师',
                'email': 'li@school.edu.cn',
                'phone': '13810001002',
                'user_type': 'teacher'
            }
        ]

        # 创建保安用户
        security_users = [
            {
                'username': 'security001',
                'password': 'security123',
                'real_name': '保安小王',
                'email': 'security1@school.edu.cn',
                'phone': '13820002001',
                'user_type': 'security'
            },
            {
                'username': 'security002',
                'password': 'security123',
                'real_name': '保安小李',
                'email': 'security2@school.edu.cn',
                'phone': '13820002002',
                'user_type': 'security'
            }
        ]

        # 创建校友用户
        alumni_users = [
            {
                'username': 'alumni001',
                'password': 'Alumni123456',
                'real_name': '王明',
                'email': 'wangming@alumni.edu.cn',
                'phone': '13830003001',
                'student_id': '2020001',
                'graduation_year': 2020,
                'class_name': '计算机科学1班',
                'department': '计算机学院',
                'major': '计算机科学与技术',
                'id_card': '110101199001011234',
                'class_teacher': '张老师',
                'current_city': '北京市',
                'work_unit': '腾讯科技',
                'position': '软件工程师'
            },
            {
                'username': 'alumni002',
                'password': 'Alumni123456',
                'real_name': '李红',
                'email': 'lihong@alumni.edu.cn',
                'phone': '13830003002',
                'student_id': '2020002',
                'graduation_year': 2020,
                'class_name': '计算机科学2班',
                'department': '计算机学院',
                'major': '软件工程',
                'id_card': '110101199002022345',
                'class_teacher': '李老师',
                'current_city': '上海市',
                'work_unit': '阿里巴巴',
                'position': '产品经理'
            },
            {
                'username': 'alumni003',
                'password': 'Alumni123456',
                'real_name': '张伟',
                'email': 'zhangwei@alumni.edu.cn',
                'phone': '13830003003',
                'student_id': '2019001',
                'graduation_year': 2019,
                'class_name': '电子工程1班',
                'department': '信息学院',
                'major': '电子信息工程',
                'id_card': '110101199003033456',
                'class_teacher': '王教授',
                'current_city': '深圳市',
                'work_unit': '华为技术',
                'position': '硬件工程师'
            }
        ]

        # 合并所有用户
        all_users = teacher_users + security_users + alumni_users
        created_count = 0

        for user_data in all_users:
            # 检查用户是否已存在
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if existing_user:
                print(f"  ⚠️  用户 {user_data['username']} 已存在，跳过")
                continue

            # 创建用户
            user = User(
                username=user_data['username'],
                real_name=user_data['real_name'],
                email=user_data['email'],
                phone=user_data['phone'],
                user_type=user_data['user_type'],
                status='active'
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            db.session.flush()  # 获取用户ID

            # 如果是校友，创建校友档案
            if user_data['user_type'] == 'alumni':
                alumni_profile = AlumniProfile(
                    user_id=user.id,
                    student_id=user_data['student_id'],
                    graduation_year=user_data['graduation_year'],
                    class_name=user_data['class_name'],
                    department=user_data['department'],
                    major=user_data['major'],
                    id_card=user_data['id_card'],
                    class_teacher=user_data['class_teacher'],
                    current_city=user_data['current_city'],
                    work_unit=user_data['work_unit'],
                    position=user_data['position'],
                    approval_status='approved'
                )
                db.session.add(alumni_profile)

            created_count += 1
            print(f"  ✅ 创建用户: {user_data['username']} ({user_data['real_name']})")

        db.session.commit()
        print(f"👥 用户创建完成，共创建 {created_count} 个用户")

def create_test_visit_applications():
    """创建测试访问申请"""
    app = create_app()
    with app.app_context():
        print("\n📅 创建测试访问申请...")

        # 获取校友用户
        alumni_users = User.query.filter_by(user_type='alumni', status='active').all()
        if not alumni_users:
            print("  ❌ 没有找到校友用户，请先创建校友账户")
            return

        # 获取教师用户
        teacher_users = User.query.filter_by(user_type='teacher', status='active').all()

        # 创建不同状态的访问申请
        visit_applications = []

        for i, alumni in enumerate(alumni_users[:3]):  # 只为前3个校友创建申请
            # 申请1: 待审核
            visit_applications.append({
                'applicant_id': alumni.id,
                'visit_date': date.today() + timedelta(days=i+1),
                'visit_time_start': '09:00',
                'visit_time_end': '17:00',
                'visit_purpose': '拜访老师',
                'target_person': '张老师' if i == 0 else '李老师',
                'target_department': '计算机学院',
                'visitor_name': alumni.real_name,
                'visitor_phone': alumni.phone,
                'visitor_email': alumni.email,
                'visitor_id_card': alumni.alumni_profile.id_card if alumni.alumni_profile else '',
                'companions': [],
                'has_vehicle': False,
                'application_status': 'pending',
                'notes': f'测试申请 {i+1}'
            })

            # 申请2: 已通过
            visit_applications.append({
                'applicant_id': alumni.id,
                'visit_date': date.today() + timedelta(days=i+2),
                'visit_time_start': '14:00',
                'visit_time_end': '18:00',
                'visit_purpose': '学术交流',
                'target_person': '王教授' if i == 1 else '张教授',
                'target_department': '信息学院',
                'visitor_name': alumni.real_name,
                'visitor_phone': alumni.phone,
                'visitor_email': alumni.email,
                'visitor_id_card': alumni.alumni_profile.id_card if alumni.alumni_profile else '',
                'companions': [{'name': '同事A', 'phone': '1380000000' + str(i)}],
                'has_vehicle': True,
                'vehicle_info': {
                    'plate_number': f'京A{i+1}2345',
                    'vehicle_type': '轿车',
                    'vehicle_color': '白色',
                    'vehicle_brand': '大众'
                },
                'application_status': 'approved',
                'approved_by': teacher_users[0].id if teacher_users else None,
                'approval_time': datetime.utcnow(),
                'notes': f'已通过的测试申请 {i+1}'
            })

            # 申请3: 已完成
            if i < 2:  # 只为前2个创建已完成申请
                visit_applications.append({
                    'applicant_id': alumni.id,
                    'visit_date': date.today() - timedelta(days=i+1),
                    'visit_time_start': '10:00',
                    'visit_time_end': '16:00',
                    'visit_purpose': '校园参观',
                    'target_person': '李老师',
                    'target_department': '计算机学院',
                    'visitor_name': alumni.real_name,
                    'visitor_phone': alumni.phone,
                    'visitor_email': alumni.email,
                    'visitor_id_card': alumni.alumni_profile.id_card if alumni.alumni_profile else '',
                    'companions': [],
                    'has_vehicle': False,
                    'application_status': 'completed',
                    'approved_by': teacher_users[1].id if len(teacher_users) > 1 else teacher_users[0].id,
                    'approval_time': datetime.utcnow() - timedelta(days=i+1),
                    'notes': f'已完成的测试申请 {i+1}'
                })

        # 保存访问申请
        created_count = 0
        for app_data in visit_applications:
            # 检查是否已有类似的申请
            existing_app = VisitApplication.query.filter_by(
                applicant_id=app_data['applicant_id'],
                visit_date=app_data['visit_date'],
                visit_time_start=app_data['visit_time_start']
            ).first()

            if existing_app:
                print(f"  ⚠️  类似申请已存在，跳过")
                continue

            application = VisitApplication(**app_data)
            db.session.add(application)
            created_count += 1
            print(f"  ✅ 创建访问申请: {app_data['visitor_name']} - {app_data['visit_purpose']}")

        db.session.commit()
        print(f"📅 访问申请创建完成，共创建 {created_count} 个申请")

def create_test_vehicles():
    """创建测试车辆信息"""
    app = create_app()
    with app.app_context():
        print("\n🚗 创建测试车辆信息...")

        # 获取校友用户
        alumni_users = User.query.filter_by(user_type='alumni', status='active').all()

        vehicles_data = [
            {
                'plate_number': '京A12345',
                'vehicle_type': '轿车',
                'vehicle_color': '白色',
                'vehicle_brand': '大众',
                'owner_name': '王明',
                'owner_relation': '本人',
                'status': 'approved'
            },
            {
                'plate_number': '京B67890',
                'vehicle_type': 'SUV',
                'vehicle_color': '黑色',
                'vehicle_brand': '奥迪',
                'owner_name': '李红',
                'owner_relation': '本人',
                'status': 'approved'
            },
            {
                'plate_number': '京C11111',
                'vehicle_type': '轿车',
                'vehicle_color': '银色',
                'vehicle_brand': '宝马',
                'owner_name': '张伟',
                'owner_relation': '本人',
                'status': 'pending'
            }
        ]

        created_count = 0
        for i, vehicle_data in enumerate(vehicles_data):
            # 检查车辆是否已存在
            existing_vehicle = Vehicle.query.filter_by(plate_number=vehicle_data['plate_number']).first()
            if existing_vehicle:
                print(f"  ⚠️  车辆 {vehicle_data['plate_number']} 已存在，跳过")
                continue

            # 关联到校友用户
            if i < len(alumni_users):
                vehicle = Vehicle(
                    user_id=alumni_users[i].id,
                    **vehicle_data
                )
                db.session.add(vehicle)
                created_count += 1
                print(f"  ✅ 创建车辆: {vehicle_data['plate_number']} - {vehicle_data['owner_name']}")

        db.session.commit()
        print(f"🚗 车辆信息创建完成，共创建 {created_count} 个车辆")


def main():
    """主函数"""
    print("🚀 开始创建测试数据")
    print("=" * 50)

    try:
        create_test_users()
        create_test_visit_applications()
        create_test_vehicles()

        print("\n" + "=" * 50)
        print("🎉 所有测试数据创建完成！")
        print("\n📋 测试账户信息:")
        print("管理员: admin / admin123")
        print("教师: teacher001 / teacher123")
        print("教师: teacher002 / teacher123")
        print("保安: security001 / security123")
        print("保安: security002 / security123")
        print("校友: alumni001 / Alumni123456")
        print("校友: alumni002 / Alumni123456")
        print("校友: alumni003 / Alumni123456")

    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()