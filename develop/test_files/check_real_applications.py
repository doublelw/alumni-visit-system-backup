#!/usr/bin/env python3
"""
检查真实提交的学生出校申请
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.student_exit_application import StudentExitApplication
from app.models.user import User
from datetime import datetime

def check_real_applications():
    app = create_app()
    with app.app_context():
        # 获取张小明用户
        student = User.query.filter_by(username='student001').first()
        if not student:
            print('未找到学生张小明')
            return

        print(f'学生: {student.real_name} (ID: {student.id})')

        # 查看该学生的所有出校申请
        applications = StudentExitApplication.query.filter_by(student_id=student.id).order_by(StudentExitApplication.created_at.desc()).all()

        print(f'\n总共找到 {len(applications)} 个出校申请:')

        for i, app in enumerate(applications, 1):
            print(f'{i}. 申请ID: {app.id}')
            print(f'   创建时间: {app.created_at}')
            print(f'   出校日期: {app.exit_date}')
            print(f'   出校时间: {app.exit_time_start} - {app.exit_time_end}')
            print(f'   出校原因: {app.exit_reason}')
            print(f'   目的地: {app.destination}')
            print(f'   申请状态: {app.application_status}')
            print(f'   申请人ID: {app.applicant_id}')
            print(f'   学生ID: {app.student_id}')
            print('---')

        # 检查最近1小时内提交的申请
        from datetime import datetime, timedelta
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_apps = StudentExitApplication.query.filter(
            StudentExitApplication.student_id == student.id,
            StudentExitApplication.created_at >= one_hour_ago
        ).all()

        print(f'\n最近1小时内的申请: {len(recent_apps)} 个')
        for app in recent_apps:
            print(f'- {app.exit_reason} (提交时间: {app.created_at})')

if __name__ == '__main__':
    check_real_applications()