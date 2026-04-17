#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
校友入校登记系统 - 批量创建测试账户
功能: 创建教师、学生、家长测试账户
使用: python create_test_accounts.py
"""

import os
import sys

# 添加后端路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app import create_app, db
from app.models.user import User
from datetime import datetime

def create_test_accounts():
    """创建测试账户"""
    app = create_app()

    with app.app_context():
        print("="*70)
        print("[Start] Creating test accounts...")
        print("="*70)
        print()

        # ========== 创建教师账户 ==========
        print("[1/3] Creating teacher accounts...")
        print("-" * 70)

        teachers = [
            {
                'username': '13600136001',
                'real_name': '张老师',
                'email': 'zhang@school.edu',
                'phone': '13600136001',
                'password': '1234',
                'department': '教务处',
                'employee_id': 'T001',
                'is_class_teacher': True,
                'is_visitable': True
            },
            {
                'username': '13600136002',
                'real_name': '李老师',
                'email': 'li@school.edu',
                'phone': '13600136002',
                'password': '1234',
                'department': '教务处',
                'employee_id': 'T002',
                'is_class_teacher': True,
                'is_visitable': True
            },
            {
                'username': '13600136003',
                'real_name': '王老师',
                'email': 'wang@school.edu',
                'phone': '13600136003',
                'password': '1234',
                'department': '高一年级',
                'employee_id': 'T003',
                'is_class_teacher': True,
                'is_visitable': True
            }
        ]

        created_teachers = 0
        for teacher_data in teachers:
            existing_user = User.query.filter_by(username=teacher_data['username']).first()
            if existing_user:
                existing_user.real_name = teacher_data['real_name']
                existing_user.email = teacher_data['email']
                existing_user.phone = teacher_data['phone']
                existing_user.user_type = 'teacher'
                existing_user.employee_id = teacher_data.get('employee_id', '')
                existing_user.is_class_teacher = teacher_data.get('is_class_teacher', False)
                existing_user.is_visitable = teacher_data.get('is_visitable', False)
                existing_user.status = 'active'
                print(f"  [Updated] Teacher: {teacher_data['real_name']} ({teacher_data['username']})")
            else:
                teacher = User(
                    username=teacher_data['username'],
                    real_name=teacher_data['real_name'],
                    email=teacher_data['email'],
                    phone=teacher_data['phone'],
                    user_type='teacher',
                    status='active',
                    employee_id=teacher_data.get('employee_id', ''),
                    is_class_teacher=teacher_data.get('is_class_teacher', False),
                    is_visitable=teacher_data.get('is_visitable', False),
                    created_at=datetime.now()
                )
                teacher.set_password(teacher_data['password'])
                db.session.add(teacher)
                print(f"  [Created] Teacher: {teacher_data['real_name']} ({teacher_data['username']})")
                created_teachers += 1

        print()

        # ========== 创建学生账户 ==========
        print("[2/3] Creating student accounts...")
        print("-" * 70)

        students = [
            {
                'username': 's2024001',
                'real_name': '张三',
                'email': 'zhangsan@school.edu',
                'phone': '13800138001',
                'password': '1234',
                'student_id': '2024001',
                'class_id': '高一1班',
                'grade': '高一'
            },
            {
                'username': 's2024002',
                'real_name': '李四',
                'email': 'lisi@school.edu',
                'phone': '13800138002',
                'password': '1234',
                'student_id': '2024002',
                'class_id': '高一1班',
                'grade': '高一'
            },
            {
                'username': 's2024003',
                'real_name': '王五',
                'email': 'wangwu@school.edu',
                'phone': '13800138003',
                'password': '1234',
                'student_id': '2024003',
                'class_id': '高一2班',
                'grade': '高一'
            },
            {
                'username': 's2024004',
                'real_name': '赵六',
                'email': 'zhaoliu@school.edu',
                'phone': '13800138004',
                'password': '1234',
                'student_id': '2024004',
                'class_id': '高一2班',
                'grade': '高一'
            },
            {
                'username': 's2024005',
                'real_name': '孙七',
                'email': 'sunqi@school.edu',
                'phone': '13800138005',
                'password': '1234',
                'student_id': '2024005',
                'class_id': '高二1班',
                'grade': '高二'
            }
        ]

        created_students = 0
        for student_data in students:
            existing_user = User.query.filter_by(username=student_data['username']).first()
            if existing_user:
                existing_user.real_name = student_data['real_name']
                existing_user.email = student_data['email']
                existing_user.phone = student_data['phone']
                existing_user.user_type = 'student'
                existing_user.student_id = student_data.get('student_id', '')
                existing_user.class_id = student_data.get('class_id', '')
                existing_user.grade = student_data.get('grade', '')
                existing_user.status = 'active'
                print(f"  [Updated] Student: {student_data['real_name']} ({student_data['username']})")
            else:
                student = User(
                    username=student_data['username'],
                    real_name=student_data['real_name'],
                    email=student_data['email'],
                    phone=student_data['phone'],
                    user_type='student',
                    status='active',
                    student_id=student_data.get('student_id', ''),
                    class_id=student_data.get('class_id', ''),
                    grade=student_data.get('grade', ''),
                    created_at=datetime.now()
                )
                student.set_password(student_data['password'])
                db.session.add(student)
                print(f"  [Created] Student: {student_data['real_name']} ({student_data['username']})")
                created_students += 1

        print()

        # ========== 创建家长账户 ==========
        print("[3/3] Creating parent accounts...")
        print("-" * 70)

        parents = [
            {
                'username': 'p13800138001',
                'real_name': '张父',
                'email': 'zhangfu@parent.com',
                'phone': '13900139001',
                'password': '1234'
            },
            {
                'username': 'p13800138002',
                'real_name': '李母',
                'email': 'limu@parent.com',
                'phone': '13900139002',
                'password': '1234'
            },
            {
                'username': 'p13800138003',
                'real_name': '王父',
                'email': 'wangfu@parent.com',
                'phone': '13900139003',
                'password': '1234'
            }
        ]

        created_parents = 0
        for parent_data in parents:
            existing_user = User.query.filter_by(username=parent_data['username']).first()
            if existing_user:
                existing_user.real_name = parent_data['real_name']
                existing_user.email = parent_data['email']
                existing_user.phone = parent_data['phone']
                existing_user.user_type = 'parent'
                existing_user.status = 'active'
                print(f"  [Updated] Parent: {parent_data['real_name']} ({parent_data['username']})")
            else:
                parent = User(
                    username=parent_data['username'],
                    real_name=parent_data['real_name'],
                    email=parent_data['email'],
                    phone=parent_data['phone'],
                    user_type='parent',
                    status='active',
                    created_at=datetime.now()
                )
                parent.set_password(parent_data['password'])
                db.session.add(parent)
                print(f"  [Created] Parent: {parent_data['real_name']} ({parent_data['username']})")
                created_parents += 1

        # 提交更改
        db.session.commit()

        print()
        print("="*70)
        print("[Complete] Account creation completed!")
        print(f"  Teachers: {created_teachers} new, {len(teachers) - created_teachers} updated")
        print(f"  Students: {created_students} new, {len(students) - created_students} updated")
        print(f"  Parents: {created_parents} new, {len(parents) - created_parents} updated")
        print()
        print("[INFO] All accounts use default password: 1234")
        print("[WARNING] Please change passwords after first login!")
        print("="*70)
        print()

        # 打印账户列表
        print("="*70)
        print("TEST ACCOUNT LIST")
        print("="*70)
        print()

        print("TEACHERS (Teacher Portal: /teacher-wechat)")
        print("-" * 70)
        for teacher in teachers:
            print(f"  Name: {teacher['real_name']}")
            print(f"  Username/Phone: {teacher['username']}")
            print(f"  Password: {teacher['password']}")
            print()

        print("STUDENTS (Student Portal)")
        print("-" * 70)
        for student in students:
            print(f"  Name: {student['real_name']}")
            print(f"  Username: {student['username']}")
            print(f"  Password: {student['password']}")
            print(f"  Class: {student['class_id']}")
            print()

        print("PARENTS (Parent Portal: /parent-simple)")
        print("-" * 70)
        for parent in parents:
            print(f"  Name: {parent['real_name']}")
            print(f"  Username: {parent['username']}")
            print(f"  Password: {parent['password']}")
            print(f"  Phone: {parent['phone']}")
            print()

        print("="*70)
        print("Login Information:")
        print("  Teacher: http://localhost:5000/teacher-wechat")
        print("  Parent:  http://localhost:5000/parent-simple")
        print("  Visitor: http://localhost:5000/visitor-verify")
        print("="*70)

if __name__ == '__main__':
    try:
        create_test_accounts()
    except Exception as e:
        print(f"[ERROR] Failed to create accounts: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
