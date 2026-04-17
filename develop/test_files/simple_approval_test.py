#!/usr/bin/env python3
"""
简单测试学生出校申请审批API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from datetime import datetime

def simple_test():
    """简单测试"""
    try:
        app = create_app()
        with app.app_context():
            print("=== 检查学生出校申请数据 ===")

            # 查找所有申请
            all_applications = StudentExitApplication.query.all()
            print(f"总共找到 {len(all_applications)} 个申请")

            for app in all_applications:
                print(f"\n申请 ID: {app.id}")
                print(f"  学生ID: {app.student_id}")
                print(f"  申请人ID: {app.applicant_id}")
                print(f"  申请状态: {app.application_status}")
                print(f"  家长审批: {app.parent_approval_status}")
                print(f"  老师审批: {app.teacher_approval_status}")
                print(f"  出校日期: {app.exit_date}")
                print(f"  出校原因: {app.exit_reason}")

                # 获取学生和申请人信息
                student = User.query.get(app.student_id) if app.student_id else None
                applicant = User.query.get(app.applicant_id) if app.applicant_id else None

                print(f"  学生姓名: {student.real_name if student else '未知'}")
                print(f"  申请人姓名: {applicant.real_name if applicant else '未知'}")
                print(f"  申请人类型: {applicant.user_type if applicant else '未知'}")

            # 查找用户
            admin = User.query.filter_by(username='admin').first()
            li_laoshi = User.query.filter_by(username='li_laoshi').first()
            zhang_xiaoming = User.query.filter_by(username='zhang_xiaoming').first()

            print(f"\n=== 用户信息 ===")
            if admin:
                print(f"管理员: {admin.real_name} (ID: {admin.id}, 类型: {admin.user_type})")
            if li_laoshi:
                print(f"李老师: {li_laoshi.real_name} (ID: {li_laoshi.id}, 类型: {li_laoshi.user_type})")
            if zhang_xiaoming:
                print(f"张小明: {zhang_xiaoming.real_name} (ID: {zhang_xiaoming.id}, 类型: {zhang_xiaoming.user_type})")

            # 如果没有待审批的申请，创建一个
            pending_apps = [app for app in all_applications if app.application_status == 'pending']
            if not pending_apps and zhang_xiaoming:
                print(f"\n=== 创建测试申请 ===")
                new_app = StudentExitApplication(
                    student_id=zhang_xiaoming.id,
                    applicant_id=zhang_xiaoming.id,
                    exit_date=datetime.now().date(),
                    exit_time_start=datetime.now().time(),
                    exit_time_end=datetime.now().time(),
                    exit_reason="测试请假申请",
                    destination="图书馆",
                    parent_approval_status='pending',
                    teacher_approval_status='pending',
                    application_status='pending'
                )
                db.session.add(new_app)
                db.session.commit()
                print(f"创建了新的测试申请，ID: {new_app.id}")

            print(f"\n=== 测试完成 ===")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()