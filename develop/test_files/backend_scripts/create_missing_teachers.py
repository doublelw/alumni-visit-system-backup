#!/usr/bin/env python
"""
创建缺失的教师用户 EMP005-EMP010
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app import create_app, db
from app.models.user import User
from app.models.organization import Organization

def create_missing_teachers():
    """创建缺失的教师用户"""

    teacher_data = [
        {
            'username': 'teacher004',
            'employee_id': 'EMP000005',
            'real_name': '赵老师',
            'email': 'teacher004@school.edu.cn',
            'phone': '13800138105',
            'password': 'teacher123'
        },
        {
            'username': 'teacher005',
            'employee_id': 'EMP000006',
            'real_name': '钱老师',
            'email': 'teacher005@school.edu.cn',
            'phone': '13800138106',
            'password': 'teacher123'
        },
        {
            'username': 'teacher006',
            'employee_id': 'EMP000007',
            'real_name': '孙老师',
            'email': 'teacher006@school.edu.cn',
            'phone': '13800138107',
            'password': 'teacher123'
        },
        {
            'username': 'teacher007',
            'employee_id': 'EMP000008',
            'real_name': '李老师',
            'email': 'teacher007@school.edu.cn',
            'phone': '13800138108',
            'password': 'teacher123'
        },
        {
            'username': 'teacher008',
            'employee_id': 'EMP000009',
            'real_name': '周老师',
            'email': 'teacher008@school.edu.cn',
            'phone': '13800138109',
            'password': 'teacher123'
        },
        {
            'username': 'teacher009',
            'employee_id': 'EMP000010',
            'real_name': '吴老师',
            'email': 'teacher009@school.edu.cn',
            'phone': '13800138110',
            'password': 'teacher123'
        },
        {
            'username': 'teacher010',
            'employee_id': 'EMP000011',
            'real_name': '郑老师',
            'email': 'teacher010@school.edu.cn',
            'phone': '13800138111',
            'password': 'teacher123'
        }
    ]

    app = create_app()
    with app.app_context():
        print("开始创建缺失的教师用户...")

        # 获取主校区组织
        main_campus = Organization.query.filter_by(code='MAIN_CAMPUS').first()
        if not main_campus:
            print("未找到主校区组织，跳过创建")
            return

        created_count = 0
        for teacher_info in teacher_data:
            # 检查用户是否已存在
            existing_user = User.query.filter_by(employee_id=teacher_info['employee_id']).first()
            if existing_user:
                print(f"用户 {teacher_info['employee_id']} 已存在，跳过")
                continue

            # 创建新用户
            user = User(
                username=teacher_info['username'],
                employee_id=teacher_info['employee_id'],
                real_name=teacher_info['real_name'],
                email=teacher_info['email'],
                phone=teacher_info['phone'],
                user_type='teacher',
                status='active',
                organization_id=main_campus.id
            )

            # 设置密码
            user.set_password(teacher_info['password'])

            db.session.add(user)
            created_count += 1
            print(f"创建教师: {teacher_info['employee_id']} - {teacher_info['real_name']}")

        try:
            db.session.commit()
            print(f"\n成功创建 {created_count} 个教师用户")
        except Exception as e:
            db.session.rollback()
            print(f"\n创建失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return

        # 显示最终统计
        teacher_count = User.query.filter_by(user_type='teacher').count()
        total_users = User.query.count()

        print(f"\n=== 最终统计 ===")
        print(f"教师总数: {teacher_count}")
        print(f"用户总数: {total_users}")

        print(f"\n=== 所有教师用户 ===")
        teachers = User.query.filter_by(user_type='teacher').all()
        for teacher in teachers:
            print(f"  {teacher.employee_id}: {teacher.real_name} ({teacher.username})")

if __name__ == '__main__':
    try:
        create_missing_teachers()
        print("\n[SUCCESS] 教师用户创建完成！")
    except Exception as e:
        print(f"\n[FATAL] 脚本执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)