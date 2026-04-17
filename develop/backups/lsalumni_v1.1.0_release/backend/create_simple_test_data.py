#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建简单测试数据脚本
"""

import sys
import os
from datetime import datetime, timedelta, date, time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath('.'))))

from app import create_app, db
from app.models import User, AlumniProfile, VisitApplication, Vehicle

def main():
    """主函数"""
    print("开始创建测试数据...")

    app = create_app()
    with app.app_context():
        # 创建教师用户
        print("创建教师用户...")
        teacher1 = User.query.filter_by(username='teacher001').first()
        if not teacher1:
            teacher1 = User(
                username='teacher001',
                real_name='张老师',
                email='zhang@school.edu.cn',
                phone='13810001001',
                user_type='teacher',
                status='active'
            )
            teacher1.set_password('teacher123')
            db.session.add(teacher1)

        teacher2 = User.query.filter_by(username='teacher002').first()
        if not teacher2:
            teacher2 = User(
                username='teacher002',
                real_name='李老师',
                email='li@school.edu.cn',
                phone='13810001002',
                user_type='teacher',
                status='active'
            )
            teacher2.set_password('teacher123')
            db.session.add(teacher2)

        # 创建保安用户
        print("创建保安用户...")
        security1 = User.query.filter_by(username='security001').first()
        if not security1:
            security1 = User(
                username='security001',
                real_name='保安小王',
                email='security1@school.edu.cn',
                phone='13820002001',
                user_type='security',
                status='active'
            )
            security1.set_password('security123')
            db.session.add(security1)

        # 创建校友用户
        print("创建校友用户...")
        alumni1 = User.query.filter_by(username='alumni001').first()
        if not alumni1:
            alumni1 = User(
                username='alumni001',
                real_name='王明',
                email='wangming@alumni.edu.cn',
                phone='13830003001',
                user_type='alumni',
                status='active'
            )
            alumni1.set_password('Alumni123456')
            db.session.add(alumni1)
            db.session.flush()

            # 创建校友档案
            alumni_profile = AlumniProfile(
                user_id=alumni1.id,
                student_id='2020001',
                graduation_year=2020,
                class_name='计算机科学1班',
                department='计算机学院',
                major='计算机科学与技术',
                id_card='110101199001011234',
                class_teacher='张老师',
                current_city='北京市',
                work_unit='腾讯科技',
                position='软件工程师',
                approval_status='approved'
            )
            db.session.add(alumni_profile)

        alumni2 = User.query.filter_by(username='alumni002').first()
        if not alumni2:
            alumni2 = User(
                username='alumni002',
                real_name='李红',
                email='lihong@alumni.edu.cn',
                phone='13830003002',
                user_type='alumni',
                status='active'
            )
            alumni2.set_password('Alumni123456')
            db.session.add(alumni2)
            db.session.flush()

            # 创建校友档案
            alumni_profile2 = AlumniProfile(
                user_id=alumni2.id,
                student_id='2020002',
                graduation_year=2020,
                class_name='计算机科学2班',
                department='计算机学院',
                major='软件工程',
                id_card='110101199002022345',
                class_teacher='李老师',
                current_city='上海市',
                work_unit='阿里巴巴',
                position='产品经理',
                approval_status='approved'
            )
            db.session.add(alumni_profile2)

        db.session.commit()
        print("用户创建完成")

        # 创建访问申请
        print("创建访问申请...")
        alumni_users = User.query.filter_by(user_type='alumni', status='active').all()
        teacher_users = User.query.filter_by(user_type='teacher', status='active').all()

        if alumni_users and teacher_users:
            # 待审核的申请
            app1 = VisitApplication(
                applicant_id=alumni_users[0].id,
                visit_date=date.today() + timedelta(days=1),
                visit_time_start=time(9, 0),
                visit_time_end=time(17, 0),
                visit_purpose='拜访老师',
                target_person='张老师',
                target_department='计算机学院',
                application_status='pending'
            )
            db.session.add(app1)

            # 已通过的申请
            app2 = VisitApplication(
                applicant_id=alumni_users[1].id,
                visit_date=date.today() + timedelta(days=2),
                visit_time_start=time(14, 0),
                visit_time_end=time(18, 0),
                visit_purpose='学术交流',
                target_person='李老师',
                target_department='计算机学院',
                application_status='approved',
                approved_by=teacher_users[0].id,
                approval_time=datetime.now(),
                approval_note='已通过的测试申请'
            )
            db.session.add(app2)

            # 已完成的申请
            app3 = VisitApplication(
                applicant_id=alumni_users[0].id,
                visit_date=date.today() - timedelta(days=1),
                visit_time_start=time(10, 0),
                visit_time_end=time(16, 0),
                visit_purpose='校园参观',
                target_person='李老师',
                target_department='计算机学院',
                application_status='completed',
                approved_by=teacher_users[1].id,
                approval_time=datetime.now() - timedelta(days=1),
                approval_note='已完成的测试申请'
            )
            db.session.add(app3)

            db.session.commit()
            print("访问申请创建完成")

        # 创建车辆信息
        print("创建车辆信息...")
        if alumni_users:
            vehicle1 = Vehicle.query.filter_by(license_plate='京A12345').first()
            if not vehicle1:
                vehicle1 = Vehicle(
                    user_id=alumni_users[0].id,
                    license_plate='京A12345',
                    vehicle_type='轿车',
                    vehicle_color='白色',
                    vehicle_brand='大众',
                    owner_name='王明',
                    owner_relation='本人',
                    registration_status='approved'
                )
                db.session.add(vehicle1)

            vehicle2 = Vehicle.query.filter_by(license_plate='京B67890').first()
            if not vehicle2:
                vehicle2 = Vehicle(
                    user_id=alumni_users[1].id,
                    license_plate='京B67890',
                    vehicle_type='SUV',
                    vehicle_color='黑色',
                    vehicle_brand='奥迪',
                    owner_name='李红',
                    owner_relation='本人',
                    registration_status='approved'
                )
                db.session.add(vehicle2)

            db.session.commit()
            print("车辆信息创建完成")

        print("\n测试数据创建完成！")
        print("\n测试账户信息:")
        print("管理员: admin / admin123")
        print("教师: teacher001 / teacher123")
        print("教师: teacher002 / teacher123")
        print("保安: security001 / security123")
        print("校友: alumni001 / Alumni123456")
        print("校友: alumni002 / Alumni123456")

if __name__ == '__main__':
    main()