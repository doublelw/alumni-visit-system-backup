#!/usr/bin/env python3
"""
创建测试学生出校申请数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.student_exit_application import StudentExitApplication
from app.models.user import User
from datetime import datetime, date, time

def create_test_student_exit_applications():
    app = create_app()
    with app.app_context():
        # 获取学生用户
        student = User.query.filter_by(username='student001').first()
        if not student:
            print('未找到测试学生账号 student001')
            return

        print(f'为学生 {student.real_name} 创建测试出校申请...')

        # 创建测试申请
        test_applications = [
            {
                'exit_date': date.today(),
                'exit_time_start': time(14, 0),  # 14:00
                'exit_time_end': time(20, 0),    # 20:00
                'exit_reason': '回家处理家庭事务',
                'destination': '家里',
                'transport_method': '地铁',
                'emergency_contact': '张父',
                'emergency_phone': '13800000007',
                'application_status': 'pending'
            },
            {
                'exit_date': date(2025, 10, 30),
                'exit_time_start': time(9, 0),   # 09:00
                'exit_time_end': time(18, 0),    # 18:00
                'exit_reason': '去医院看病',
                'destination': '市中心医院',
                'transport_method': '家长接送',
                'emergency_contact': '张父',
                'emergency_phone': '13800000007',
                'application_status': 'approved'
            }
        ]

        for app_data in test_applications:
            # 检查是否已存在相似的申请
            existing = StudentExitApplication.query.filter_by(
                student_id=student.id,
                exit_date=app_data['exit_date'],
                exit_time_start=app_data['exit_time_start']
            ).first()

            if existing:
                print(f'已存在相同的申请记录 (日期: {app_data["exit_date"]})，跳过创建')
                continue

            application = StudentExitApplication(
                student_id=student.id,
                applicant_id=student.id,  # 学生自己申请，所以applicant_id和student_id相同
                exit_date=app_data['exit_date'],
                exit_time_start=app_data['exit_time_start'],
                exit_time_end=app_data['exit_time_end'],
                exit_reason=app_data['exit_reason'],
                destination=app_data['destination'],
                transport_method=app_data['transport_method'],
                emergency_contact=app_data['emergency_contact'],
                emergency_phone=app_data['emergency_phone'],
                application_status=app_data['application_status'],
                created_at=datetime.now()
            )

            db.session.add(application)
            print(f'创建申请: {app_data["exit_reason"]} ({app_data["exit_date"]})')

        db.session.commit()
        print('测试学生出校申请创建完成!')

        # 显示创建的申请
        count = StudentExitApplication.query.count()
        print(f'\n当前数据库中总共有 {count} 个学生出校申请')

        applications = StudentExitApplication.query.all()
        for app in applications:
            student_name = app.student.real_name if app.student else '未知'
            print(f'- {student_name}: {app.exit_reason} [{app.application_status}]')

if __name__ == '__main__':
    create_test_student_exit_applications()