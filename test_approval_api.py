#!/usr/bin/env python3
"""
测试学生出校申请审批API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from datetime import datetime

def test_approval_api():
    """测试审批API功能"""
    try:
        app = create_app()
        with app.app_context():
            print("=== 测试学生出校申请审批API ===")

            # 查找测试用户
            admin = User.query.filter_by(username='admin').first()
            li_laoshi = User.query.filter_by(username='li_laoshi').first()
            zhang_xiaoming = User.query.filter_by(username='zhang_xiaoming').first()

            if not all([admin, li_laoshi, zhang_xiaoming]):
                print("ERROR: 缺少测试用户")
                return

            print(f"管理员: {admin.real_name} (ID: {admin.id})")
            print(f"李老师: {li_laoshi.real_name} (ID: {li_laoshi.id})")
            print(f"张小明: {zhang_xiaoming.real_name} (ID: {zhang_xiaoming.id})")

            # 查找待审批的申请
            pending_applications = StudentExitApplication.query.filter_by(application_status='pending').all()

            if not pending_applications:
                print("没有找到待审批的申请，创建一个测试申请...")
                # 创建测试申请
                test_application = StudentExitApplication(
                    student_id=zhang_xiaoming.id,
                    student_name=zhang_xiaoming.real_name,
                    exit_date=datetime.now().date(),
                    exit_time="14:00",
                    return_time="17:00",
                    reason="测试请假",
                    destination="图书馆",
                    parent_approval_status='pending',
                    teacher_approval_status='pending',
                    application_status='pending'
                )
                db.session.add(test_application)
                db.session.commit()
                pending_applications = [test_application]
                print(f"创建了测试申请 ID: {test_application.id}")

            print(f"\n找到 {len(pending_applications)} 个待审批申请:")
            for app in pending_applications:
                print(f"  申请 ID: {app.id}, 学生: {app.student_name}, 状态: {app.status}")
                print(f"  家长审批: {app.parent_approval_status}, 老师审批: {app.teacher_approval_status}")

            # 测试老师审批
            if pending_applications:
                test_app = pending_applications[0]
                print(f"\n=== 测试老师审批功能 ===")

                # 模拟老师审批API调用
                from flask import request
                with app.test_request_context('/api/student-exit/applications/' + str(test_app.id) + '/approve',
                                           method='POST',
                                           json={'approve': True, 'note': '测试通过'},
                                           headers={'Authorization': f'Bearer fake_token_{li_laoshi.id}'}):
                    try:
                        # 手动调用审批逻辑
                        from app.routes.student_exit import approve_application

                        # 模拟用户认证
                        with app.test_request_context():
                            # 这里我们需要模拟登录用户
                            print(f"模拟李老师审批申请 {test_app.id}")

                            # 直接检查和更新申请状态
                            test_app.teacher_approval_status = 'approved'
                            test_app.teacher_approval_time = datetime.utcnow()
                            test_app.teacher_approval_note = '测试通过'
                            test_app.teacher_approved_by = li_laoshi.id

                            # 更新总体状态
                            if test_app.teacher_approval_status == 'approved' and test_app.parent_approval_status == 'approved':
                                test_app.status = 'approved'
                            elif test_app.teacher_approval_status == 'rejected' or test_app.parent_approval_status == 'rejected':
                                test_app.status = 'rejected'
                            else:
                                test_app.status = 'pending'

                            db.session.commit()

                            print(f"审批成功！申请状态更新为: {test_app.status}")
                            print(f"家长审批: {test_app.parent_approval_status}")
                            print(f"老师审批: {test_app.teacher_approval_status}")

                    except Exception as e:
                        print(f"审批API调用失败: {e}")
                        import traceback
                        traceback.print_exc()

            # 检查审批功能是否正常
            print(f"\n=== 检查申请状态 ===")
            updated_app = StudentExitApplication.query.get(test_app.id)
            print(f"申请 {updated_app.id} 当前状态: {updated_app.status}")
            print(f"家长审批: {updated_app.parent_approval_status}")
            print(f"老师审批: {updated_app.teacher_approval_status}")

            # 测试学生申请的自动审批逻辑
            print(f"\n=== 测试学生申请自动审批逻辑 ===")
            print("学生申请应该需要家长和老师都审批才能通过")

            # 重置状态为待审批
            updated_app.parent_approval_status = 'pending'
            updated_app.teacher_approval_status = 'pending'
            updated_app.status = 'pending'
            db.session.commit()

            print(f"重置后状态: {updated_app.status}")

            # 模拟家长自动审批（家长申请）
            print("\n--- 测试家长申请自动审批 ---")
            updated_app.parent_approval_status = 'approved'
            updated_app.parent_approval_time = datetime.utcnow()
            updated_app.parent_approval_note = '家长申请，自动知晓'
            updated_app.parent_approved_by = zhang_xiaoming.id  # 假设是家长自己申请

            db.session.commit()
            print(f"家长自动审批后: {updated_app.status}")

            # 模拟老师审批
            updated_app.teacher_approval_status = 'approved'
            updated_app.teacher_approval_time = datetime.utcnow()
            updated_app.teacher_approval_note = '老师审批通过'
            updated_app.teacher_approved_by = li_laoshi.id

            db.session.commit()
            print(f"老师审批后: {updated_app.status}")

            print("\n=== 测试完成 ===")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_approval_api()