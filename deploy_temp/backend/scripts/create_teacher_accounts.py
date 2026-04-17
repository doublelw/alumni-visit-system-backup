#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
校友入校登记系统 - 创建教师账户脚本
功能: 批量创建教师用户账户
使用: python create_teacher_accounts.py
"""

import os
import sys

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from datetime import datetime

def create_teacher_accounts():
    """创建教师账户"""
    app = create_app()

    with app.app_context():
        print("[开始] 创建教师账户...")

        # 教师列表（用户名使用手机号）
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
            },
            {
                'username': '13600136004',
                'real_name': '赵老师',
                'email': 'zhao@school.edu',
                'phone': '13600136004',
                'password': '1234',
                'department': '高一年级',
                'employee_id': 'T004',
                'is_class_teacher': True,
                'is_visitable': True
            },
            {
                'username': '13600136005',
                'real_name': '刘老师',
                'email': 'liu@school.edu',
                'phone': '13600136005',
                'password': '1234',
                'department': '高二年级',
                'employee_id': 'T005',
                'is_class_teacher': True,
                'is_visitable': True
            }
        ]

        created_count = 0
        updated_count = 0

        for teacher_data in teachers:
            # 检查用户是否已存在
            existing_user = User.query.filter_by(
                username=teacher_data['username']
            ).first()

            if existing_user:
                # 更新现有用户
                existing_user.real_name = teacher_data['real_name']
                existing_user.email = teacher_data['email']
                existing_user.phone = teacher_data['phone']
                existing_user.user_type = 'teacher'
                existing_user.employee_id = teacher_data.get('employee_id', '')
                existing_user.is_class_teacher = teacher_data.get('is_class_teacher', False)
                existing_user.is_visitable = teacher_data.get('is_visitable', False)
                existing_user.status = 'active'
                print(f"  [更新] 教师: {teacher_data['real_name']} ({teacher_data['username']})")
                updated_count += 1
            else:
                # 创建新用户
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
                print(f"  [创建] 教师: {teacher_data['real_name']} ({teacher_data['username']})")
                created_count += 1

        # 提交更改
        db.session.commit()

        print(f"\n[完成] 创建了 {created_count} 个新教师，更新了 {updated_count} 个教师")
        print("\n[信息] 所有教师账户默认密码: 1234")
        print("[提示] 请提醒教师在首次登录后修改密码！")

def print_teacher_accounts():
    """打印所有教师账户信息"""
    app = create_app()

    with app.app_context():
        teachers = User.query.filter_by(user_type='teacher').all()

        print("\n" + "="*70)
        print("[教师账户列表]")
        print("="*70)

        for teacher in teachers:
            status_icon = "[激活]" if teacher.status == 'active' else "[未激活]"
            print(f"\n{status_icon} {teacher.real_name}")
            print(f"   用户名: {teacher.username}")
            print(f"   手机号: {teacher.phone}")
            print(f"   邮箱: {teacher.email}")
            if teacher.employee_id:
                print(f"   工号: {teacher.employee_id}")
            print(f"   班主任: {'是' if teacher.is_class_teacher else '否'}")
            print(f"   可拜访: {'是' if teacher.is_visitable else '否'}")

        print("\n" + "="*70)
        print(f"总共 {len(teachers)} 个教师账户")
        print("="*70)

if __name__ == '__main__':
    print("="*70)
    print("校友入校登记系统 - 教师账户创建工具")
    print("="*70)

    try:
        create_teacher_accounts()
        print_teacher_accounts()

        print("\n[完成] 教师账户创建完成！")
        print("\n[登录信息（教师端）]:")
        print("   页面: http://localhost:5000/teacher-wechat")
        print("   用户名/手机号: 13600136001 ~ 13600136005")
        print("   密码: 1234")
        print("   [注意] 用户名就是手机号，可以直接用手机号登录！")

    except Exception as e:
        print(f"[错误] 创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
