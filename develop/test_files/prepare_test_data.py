#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
准备端到端测试数据
"""

import sys
sys.path.insert(0, 'D:\\Project\\校友入校登记\\backend')

from app import create_app, db
from app.models.user import User

def check_test_data():
    """检查和准备测试数据"""
    app = create_app()

    with app.app_context():
        print("="*80)
        print("检查现有测试数据")
        print("="*80)
        print()

        # 检查家长用户
        print("[1] 检查家长用户")
        parents = User.query.filter(
            User.user_type == 'parent',
            User.status == 'active'
        ).limit(3).all()

        if parents:
            print(f"  找到 {len(parents)} 个家长用户:")
            for p in parents:
                print(f"    - {p.real_name} | 手机: {p.phone} | 微信密码: {p.wechat_password}")
                if p.parent_students:
                    student = p.parent_students
                    print(f"      关联学生: {student.real_name} | 学号: {student.student_id}")
        else:
            print("  [!] 没有找到家长用户")
        print()

        # 检查学生用户
        print("[2] 检查学生用户")
        students = User.query.filter(
            User.user_type == 'student',
            User.status == 'active',
            User.student_id.isnot(None),
            User.student_id != ''
        ).limit(3).all()

        if students:
            print(f"  找到 {len(students)} 个学生用户:")
            for s in students:
                print(f"    - {s.real_name} | 学号: {s.student_id} | 手机: {s.phone}")
        else:
            print("  [!] 没有找到有学号的学生用户")
        print()

        # 检查校友用户
        print("[3] 检查校友用户")
        alumni = User.query.filter(
            User.user_type == 'alumni',
            User.status == 'active'
        ).limit(3).all()

        if alumni:
            print(f"  找到 {len(alumni)} 个校友用户:")
            for a in alumni:
                print(f"    - {a.real_name} | 手机: {a.phone} | 微信密码: {a.wechat_password}")
        else:
            print("  [!] 没有找到校友用户")
        print()

        # 检查老师用户
        print("[4] 检查老师用户")
        teachers = User.query.filter(
            User.user_type == 'teacher',
            User.status == 'active'
        ).limit(3).all()

        if teachers:
            print(f"  找到 {len(teachers)} 个老师用户:")
            for t in teachers:
                print(f"    - {t.real_name} | 手机: {t.phone}")
        else:
            print("  [!] 没有找到老师用户")
        print()

        print("="*80)
        print("推荐的测试数据配置")
        print("="*80)
        print()

        if parents and parents[0].parent_students:
            parent = parents[0]
            student = parent.parent_students
            print(f"家长申请学生请假:")
            print(f"  家长手机: {parent.phone}")
            print(f"  家长微信密码: {parent.wechat_password}")
            print(f"  学生姓名: {student.real_name}")
            print(f"  学生学号: {student.student_id}")
            print()

        if alumni:
            a = alumni[0]
            print(f"校友申请入校:")
            print(f"  校友手机: {a.phone}")
            print(f"  校友微信密码: {a.wechat_password}")
            print()

        if students:
            s = students[0]
            print(f"老师直接创建出校码:")
            print(f"  学生学号: {s.student_id}")
            print()

if __name__ == '__main__':
    check_test_data()
