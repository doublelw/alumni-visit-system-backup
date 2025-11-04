#!/usr/bin/env python3
"""
检查学生出校申请数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.student_exit_application import StudentExitApplication

def check_student_exit_applications():
    app = create_app()
    with app.app_context():
        count = StudentExitApplication.query.count()
        print(f'学生出校申请总数: {count}')

        if count > 0:
            applications = StudentExitApplication.query.limit(5).all()
            for app in applications:
                student_name = app.student.real_name if app.student else '未知'
                print(f'- ID: {app.id}, 学生: {student_name}, 原因: {app.exit_reason}, 状态: {app.application_status}')
        else:
            print('数据库中没有学生出校申请记录')

if __name__ == '__main__':
    check_student_exit_applications()