#!/usr/bin/env python3
"""
检查数据库表结构和数据
"""
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication

def check_database():
    app = create_app('development')

    with app.app_context():
        print("=== 数据库表结构检查 ===")

        # 检查所有表
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"数据库中的表: {tables}")

        # 检查用户表结构
        print("\n=== 用户表结构 ===")
        if 'user' in tables:
            columns = inspector.get_columns('user')
            for col in columns:
                print(f"  - {col['name']}: {col['type']} {'(主键)' if col['primary_key'] else ''}")

        # 检查学生出校申请表结构
        print("\n=== 学生出校申请表结构 ===")
        if 'student_exit_application' in tables:
            columns = inspector.get_columns('student_exit_application')
            for col in columns:
                print(f"  - {col['name']}: {col['type']} {'(主键)' if col['primary_key'] else ''}")

        # 检查现有用户数据
        print("\n=== 现有用户数据 ===")
        users = User.query.all()
        print(f"总用户数: {len(users)}")

        students = []
        for user in users:
            print(f"  - ID: {user.id}, 用户名: {user.username}, 姓名: {user.real_name}, 类型: {user.user_type}, 状态: {user.status}")
            if user.user_type == 'student':
                students.append(user)

        print(f"\n学生用户数: {len(students)}")
        for student in students:
            print(f"  - ID: {student.id}, 姓名: {student.real_name}, 学号: {student.student_id}, 班级: {student.class_id}")

        # 检查出校申请数据
        print("\n=== 出校申请数据 ===")
        applications = StudentExitApplication.query.all()
        print(f"总申请数: {len(applications)}")

        for app in applications:
            student = User.query.get(app.student_id) if app.student_id else None
            print(f"  - ID: {app.id}, 学生ID: {app.student_id}, 学生姓名: {student.real_name if student else '未知'}, 状态: {app.application_status}, 日期: {app.exit_date}")

if __name__ == "__main__":
    check_database()