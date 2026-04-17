#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试数据脚本
用于系统演示和测试
"""

import sys
import os
import random
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app import db
from werkzeug.security import generate_password_hash

def create_test_alumni_data():
    """创建测试校友数据"""
    app = create_app()

    with app.app_context():
        try:
            from app.models.user import User
            from app.models.alumni_profile import AlumniProfile

            # 创建多个测试校友
            alumni_data = [
                {
                    'username': 'alumni001',
                    'real_name': '张三',
                    'email': 'zhangsan@example.com',
                    'phone': '13800138101',
                    'student_id': '202001001',
                    'id_card': '110101200001010001',
                    'graduation_year': 2020,
                    'class_name': '高三1班',
                    'division': '高中部',
                    'major': '理科',
                    'contact_teacher': '李老师',
                    'contact_teacher_phone': '13900139001',
                    'emergency_contact': '张父',
                    'emergency_phone': '13800138001',
                    'approval_status': 'approved',
                    'approved_by': 2,  # 管理员ID
                    'approval_time': datetime.now() - timedelta(days=30)
                },
                {
                    'username': 'alumni002',
                    'real_name': '李四',
                    'email': 'lisi@example.com',
                    'phone': '13800138102',
                    'student_id': '202001002',
                    'id_card': '110101200001010002',
                    'graduation_year': 2020,
                    'class_name': '高三2班',
                    'division': '高中部',
                    'major': '理科',
                    'contact_teacher': '王老师',
                    'contact_teacher_phone': '13900139002',
                    'emergency_contact': '李母',
                    'emergency_phone': '13800138002',
                    'approval_status': 'approved',
                    'approved_by': 2,
                    'approval_time': datetime.now() - timedelta(days=25)
                },
                {
                    'username': 'alumni003',
                    'real_name': '王五',
                    'email': 'wangwu@example.com',
                    'phone': '13800138103',
                    'student_id': '201901003',
                    'id_card': '110101200001010003',
                    'graduation_year': 2019,
                    'class_name': '初三1班',
                    'division': '初中部',
                    'major': '综合',
                    'contact_teacher': '张老师',
                    'contact_teacher_phone': '13900139003',
                    'emergency_contact': '王父',
                    'emergency_phone': '13800138003',
                    'approval_status': 'approved',
                    'approved_by': 2,
                    'approval_time': datetime.now() - timedelta(days=20)
                },
                {
                    'username': 'alumni004',
                    'real_name': '赵六',
                    'email': 'zhaoliu@example.com',
                    'phone': '13800138104',
                    'student_id': '202001004',
                    'id_card': '110101200001010004',
                    'graduation_year': 2020,
                    'class_name': '国际部12年级1班',
                    'division': '国际部',
                    'major': 'IB课程',
                    'contact_teacher': '陈老师',
                    'contact_teacher_phone': '13900139004',
                    'emergency_contact': '赵母',
                    'emergency_phone': '13800138004',
                    'approval_status': 'pending',
                    'approved_by': None,
                    'approval_time': None
                },
                {
                    'username': 'alumni005',
                    'real_name': '钱七',
                    'email': 'qianqi@example.com',
                    'phone': '13800138105',
                    'student_id': '201801005',
                    'id_card': '110101200001010005',
                    'graduation_year': 2018,
                    'class_name': '新疆部高三1班',
                    'division': '新疆部',
                    'major': '文科',
                    'contact_teacher': '刘老师',
                    'contact_teacher_phone': '13900139005',
                    'emergency_contact': '钱父',
                    'emergency_phone': '13800138005',
                    'approval_status': 'rejected',
                    'approved_by': 2,
                    'approval_time': datetime.now() - timedelta(days=15),
                    'approval_note': '信息不完整，请重新提交'
                },
                {
                    'username': 'alumni006',
                    'real_name': '孙八',
                    'email': 'sunba@example.com',
                    'phone': '13800138106',
                    'student_id': '201701006',
                    'id_card': '110101200001010006',
                    'graduation_year': 2017,
                    'class_name': '北校区初三1班',
                    'division': '北校区',
                    'major': '综合',
                    'contact_teacher': '赵老师',
                    'contact_teacher_phone': '13900139006',
                    'emergency_contact': '孙母',
                    'emergency_phone': '13800138006',
                    'approval_status': 'approved',
                    'approved_by': 2,
                    'approval_time': datetime.now() - timedelta(days=10)
                }
            ]

            created_count = 0
            for alumni_info in alumni_data:
                # 检查用户是否已存在
                existing_user = User.query.filter_by(username=alumni_info['username']).first()
                if existing_user:
                    print(f"用户 {alumni_info['username']} 已存在，跳过创建")
                    continue

                # 创建用户账户
                user = User(
                    username=alumni_info['username'],
                    real_name=alumni_info['real_name'],
                    email=alumni_info['email'],
                    phone=alumni_info['phone'],
                    user_type='alumni',
                    status='active',
                    password_hash=generate_password_hash('12345678')
                )
                db.session.add(user)
                db.session.flush()  # 获取用户ID

                # 创建校友档案
                alumni_profile = AlumniProfile(
                    user_id=user.id,
                    student_id=alumni_info['student_id'],
                    id_card=alumni_info['id_card'],
                    graduation_year=alumni_info['graduation_year'],
                    class_name=alumni_info['class_name'],
                    division=alumni_info['division'],
                    major=alumni_info['major'],
                    contact_teacher=alumni_info['contact_teacher'],
                    contact_teacher_phone=alumni_info['contact_teacher_phone'],
                    emergency_contact=alumni_info['emergency_contact'],
                    emergency_phone=alumni_info['emergency_phone'],
                    approval_status=alumni_info['approval_status'],
                    approved_by=alumni_info['approved_by'],
                    approval_time=alumni_info['approval_time'],
                    approval_note=alumni_info.get('approval_note', '')
                )
                db.session.add(alumni_profile)
                created_count += 1

            db.session.commit()
            print(f"成功创建 {created_count} 个测试校友用户")

        except Exception as e:
            db.session.rollback()
            print(f"创建测试校友数据失败: {e}")

def create_test_visit_applications():
    """创建测试访问申请数据"""
    app = create_app()

    with app.app_context():
        try:
            from app.models.user import User
            from app.models.visit_application import VisitApplication

            # 获取校友用户
            alumni_users = User.query.filter_by(user_type='alumni').limit(5).all()
            if not alumni_users:
                print("没有找到校友用户，请先运行创建校友测试数据")
                return

            # 创建测试访问申请
            applications_data = [
                {
                    'applicant_id': alumni_users[0].id,
                    'visit_date': datetime.now().date() + timedelta(days=1),
                    'visit_time_start': datetime.strptime('09:00', '%H:%M').time(),
                    'visit_time_end': datetime.strptime('17:00', '%H:%M').time(),
                    'visit_purpose': '拜访老师',
                    'target_person': '张教授',
                    'application_status': 'approved',
                    'approved_by': 2,
                    'approval_time': datetime.now() - timedelta(hours=2)
                },
                {
                    'applicant_id': alumni_users[1].id,
                    'visit_date': datetime.now().date() + timedelta(days=2),
                    'visit_time_start': datetime.strptime('10:00', '%H:%M').time(),
                    'visit_time_end': datetime.strptime('16:00', '%H:%M').time(),
                    'visit_purpose': '学术交流',
                    'target_person': '李教授',
                    'application_status': 'pending'
                },
                {
                    'applicant_id': alumni_users[2].id,
                    'visit_date': datetime.now().date() + timedelta(days=3),
                    'visit_time_start': datetime.strptime('14:00', '%H:%M').time(),
                    'visit_time_end': datetime.strptime('18:00', '%H:%M').time(),
                    'visit_purpose': '参观校园',
                    'target_person': '招生办',
                    'application_status': 'approved',
                    'approved_by': 2,
                    'approval_time': datetime.now() - timedelta(hours=1)
                },
                {
                    'applicant_id': alumni_users[3].id,
                    'visit_date': datetime.now().date() + timedelta(days=4),
                    'visit_time_start': datetime.strptime('13:00', '%H:%M').time(),
                    'visit_time_end': datetime.now().time(),
                    'visit_purpose': '参加活动',
                    'target_person': '学生处',
                    'application_status': 'rejected',
                    'approved_by': 2,
                    'approval_time': datetime.now() - timedelta(minutes=30),
                    'approval_note': '活动已取消'
                },
                {
                    'applicant_id': alumni_users[4].id,
                    'visit_date': datetime.now().date() + timedelta(days=5),
                    'visit_time_start': datetime.strptime('15:00', '%H:%M').time(),
                    'visit_time_end': datetime.strptime('17:00', '%H:%M').time(),
                    'visit_purpose': '图书馆查阅资料',
                    'target_person': '图书馆',
                    'application_status': 'pending'
                }
            ]

            created_count = 0
            for app_info in applications_data:
                # 检查是否已存在相似的申请
                existing = VisitApplication.query.filter_by(
                    applicant_id=app_info['applicant_id'],
                    visit_date=app_info['visit_date']
                ).first()
                if existing:
                    print(f"该用户在 {app_info['visit_date']} 已有访问申请，跳过")
                    continue

                application = VisitApplication(
                    applicant_id=app_info['applicant_id'],
                    visit_date=app_info['visit_date'],
                    visit_time_start=app_info['visit_time_start'],
                    visit_time_end=app_info['visit_time_end'],
                    visit_purpose=app_info['visit_purpose'],
                    target_person=app_info['target_person'],
                    application_status=app_info['application_status'],
                    approved_by=app_info.get('approved_by'),
                    approval_time=app_info.get('approval_time'),
                    approval_note=app_info.get('approval_note', '')
                )
                db.session.add(application)
                created_count += 1

            db.session.commit()
            print(f"成功创建 {created_count} 个测试访问申请")

        except Exception as e:
            db.session.rollback()
            print(f"创建测试访问申请失败: {e}")

def create_test_vehicle_data():
    """创建测试车辆数据"""
    app = create_app()

    with app.app_context():
        try:
            from app.models.user import User
            from app.models.vehicle import Vehicle

            # 获取校友用户
            alumni_users = User.query.filter_by(user_type='alumni').limit(3).all()
            if not alumni_users:
                print("没有找到校友用户，请先运行创建校友测试数据")
                return

            # 创建测试车辆数据
            vehicles_data = [
                {
                    'user_id': alumni_users[0].id,
                    'license_plate': '京A12345',
                    'vehicle_type': '轿车',
                    'vehicle_brand': '丰田',
                    'vehicle_model': '凯美瑞',
                    'vehicle_color': '白色',
                    'owner_name': alumni_users[0].real_name,
                    'owner_relation': '本人',
                    'registration_status': 'approved',
                    'approved_by': 2,
                    'approval_time': datetime.now() - timedelta(days=5)
                },
                {
                    'user_id': alumni_users[1].id,
                    'license_plate': '京B67890',
                    'vehicle_type': 'SUV',
                    'vehicle_brand': '本田',
                    'vehicle_model': 'CR-V',
                    'vehicle_color': '黑色',
                    'owner_name': alumni_users[1].real_name,
                    'owner_relation': '本人',
                    'registration_status': 'pending'
                },
                {
                    'user_id': alumni_users[2].id,
                    'license_plate': '京C11223',
                    'vehicle_type': '电动车',
                    'vehicle_brand': '比亚迪',
                    'vehicle_model': '汉EV',
                    'vehicle_color': '蓝色',
                    'owner_name': alumni_users[2].real_name,
                    'owner_relation': '家人',
                    'registration_status': 'rejected',
                    'approved_by': 2,
                    'approval_time': datetime.now() - timedelta(days=3),
                    'approval_note': '车辆信息不符合要求'
                }
            ]

            created_count = 0
            for vehicle_info in vehicles_data:
                # 检查是否已存在
                existing = Vehicle.query.filter_by(license_plate=vehicle_info['license_plate']).first()
                if existing:
                    print(f"车牌 {vehicle_info['license_plate']} 已存在，跳过创建")
                    continue

                vehicle = Vehicle(
                    user_id=vehicle_info['user_id'],
                    license_plate=vehicle_info['license_plate'],
                    vehicle_type=vehicle_info['vehicle_type'],
                    vehicle_brand=vehicle_info['vehicle_brand'],
                    vehicle_model=vehicle_info['vehicle_model'],
                    vehicle_color=vehicle_info['vehicle_color'],
                    owner_name=vehicle_info['owner_name'],
                    owner_relation=vehicle_info['owner_relation'],
                    registration_status=vehicle_info['registration_status'],
                    approved_by=vehicle_info.get('approved_by'),
                    approval_time=vehicle_info.get('approval_time'),
                    approval_note=vehicle_info.get('approval_note', '')
                )
                db.session.add(vehicle)
                created_count += 1

            db.session.commit()
            print(f"成功创建 {created_count} 个测试车辆")

        except Exception as e:
            db.session.rollback()
            print(f"创建测试车辆数据失败: {e}")

def create_test_visit_records():
    """创建测试访问记录"""
    app = create_app()

    with app.app_context():
        try:
            from app.models.user import User
            from app.models.visit_application import VisitApplication
            from app.models.visit_record import VisitRecord

            # 获取已批准的访问申请
            approved_applications = VisitApplication.query.filter_by(application_status='approved').limit(3).all()

            if not approved_applications:
                print("没有找到已批准的访问申请，请先创建访问申请测试数据")
                return

            # 创建测试保安账户
            security_user = User.query.filter_by(user_type='security').first()
            if not security_user:
                security_user = User(
                    username='security001',
                    real_name='保安员1号',
                    email='security1@university.edu.cn',
                    phone='13800139999',
                    user_type='security',
                    status='active',
                    password_hash=generate_password_hash('security123')
                )
                db.session.add(security_user)
                db.session.flush()

            # 创建测试访问记录
            for i, app in enumerate(approved_applications):
                # 创建访问记录
                record = VisitRecord(
                    user_id=app.applicant_id,
                    visit_application_id=app.id,
                    entry_time=datetime.now() - timedelta(hours=i*2, minutes=random.randint(0, 59)),
                    exit_time=datetime.now() - timedelta(hours=i*2-1, minutes=random.randint(0, 59)),
                    verification_method=random.choice(['face', 'qr_code', 'manual']),
                    gate_name=f'Gate {i+1}',
                    security_guard_id=security_user.id,
                    notes='测试访问记录'
                )
                db.session.add(record)

            db.session.commit()
            print(f"成功创建 {len(approved_applications)} 个测试访问记录")

        except Exception as e:
            db.session.rollback()
            print(f"创建测试访问记录失败: {e}")

def create_test_teacher_data():
    """创建测试教师数据"""
    app = create_app()

    with app.app_context():
        try:
            from app.models.user import User

            # 创建测试教师
            teachers_data = [
                {
                    'username': 'teacher001',
                    'real_name': '张教授',
                    'email': 'zhang.prof@university.edu.cn',
                    'phone': '13800138001',
                    'user_type': 'teacher',
                    'status': 'active'
                },
                {
                    'username': 'teacher002',
                    'real_name': '李教授',
                    'email': 'li.prof@university.edu.cn',
                    'phone': '13800138002',
                    'user_type': 'teacher',
                    'status': 'active'
                },
                {
                    'username': 'teacher003',
                    'real_name': '王教授',
                    'email': 'wang.prof@university.edu.cn',
                    'phone': '13800138003',
                    'user_type': 'teacher',
                    'status': 'active'
                }
            ]

            created_count = 0
            for teacher_info in teachers_data:
                # 检查是否已存在
                existing_user = User.query.filter_by(username=teacher_info['username']).first()
                if existing_user:
                    print(f"教师 {teacher_info['username']} 已存在，跳过创建")
                    continue

                teacher = User(
                    username=teacher_info['username'],
                    real_name=teacher_info['real_name'],
                    email=teacher_info['email'],
                    phone=teacher_info['phone'],
                    user_type=teacher_info['user_type'],
                    status=teacher_info['status'],
                    password_hash=generate_password_hash('teacher123')
                )
                db.session.add(teacher)
                created_count += 1

            db.session.commit()
            print(f"成功创建 {created_count} 个测试教师账户")

        except Exception as e:
            db.session.rollback()
            print(f"创建测试教师数据失败: {e}")

def main():
    """主函数：创建所有测试数据"""
    print("Creating test data...")
    print("=" * 50)

    print("\n1. Creating test teacher data...")
    create_test_teacher_data()

    print("\n2. Creating test alumni data...")
    create_test_alumni_data()

    print("\n3. Creating test visit application data...")
    create_test_visit_applications()

    print("\n4. Creating test vehicle data...")
    create_test_vehicle_data()

    print("\n5. Creating test visit records...")
    create_test_visit_records()

    print("\n" + "=" * 50)
    print("All test data created successfully!")
    print("\nTest data summary:")
    print("- Admin: admin (admin123)")
    print("- Teachers: 3 accounts (teacher123)")
    print("- Alumni: 6 accounts (12345678)")
    print("- Security: 1 account (security123)")
    print("- Visit applications: 5")
    print("- Vehicle records: 3")
    print("- Visit records: 3")
    print("\nLogin information:")
    print("- Admin: admin / admin123")
    print("- Teacher: teacher001 / teacher123")
    print("- Alumni: alumni001 / 12345678")
    print("- Security: security001 / security123")

if __name__ == '__main__':
    main()