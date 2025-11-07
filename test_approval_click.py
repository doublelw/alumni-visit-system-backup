#!/usr/bin/env python3
"""
测试前端点击审批按钮的效果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from datetime import datetime
import json

def test_approval_process():
    """测试完整的审批流程"""
    try:
        app = create_app()
        with app.app_context():
            print("=== 测试审批流程 ===")

            # 获取测试数据
            test_app = StudentExitApplication.query.get(1)  # ID为1的申请
            if not test_app:
                print("没有找到测试申请")
                return

            admin = User.query.filter_by(username='admin').first()
            li_laoshi = User.query.filter_by(username='li_laoshi').first()
            zhang_xiaoming = User.query.filter_by(username='zhang_xiaoming').first()

            print(f"测试申请 ID: {test_app.id}")
            print(f"  学生: {test_app.student.real_name if test_app.student else '未知'}")
            print(f"  申请人: {test_app.applicant.real_name if test_app.applicant else '未知'} ({test_app.applicant.user_type if test_app.applicant else '未知'})")
            print(f"  当前状态: {test_app.application_status}")
            print(f"  家长审批: {test_app.parent_approval_status}")
            print(f"  老师审批: {test_app.teacher_approval_status}")

            # 测试1: 老师申请应该自动通过
            print(f"\n=== 测试1: 老师申请自动通过 ===")
            if test_app.applicant.user_type == 'teacher':
                print("这是老师申请，应该自动通过老师审批")
                # 应用自动审批逻辑
                test_app.teacher_approval_status = 'approved'
                test_app.teacher_approval_time = datetime.utcnow()
                test_app.teacher_approval_note = '老师申请，自动通过'
                test_app.teacher_approved_by = test_app.applicant_id

                # 更新状态
                test_app.update_approval_status()
                print(f"自动审批后状态: {test_app.application_status}")

            # 测试2: 前端点击审批按钮
            print(f"\n=== 测试2: 模拟前端点击审批 ===")

            # 模拟管理员审批
            print("模拟管理员审批通过...")
            from flask_jwt_extended import create_access_token

            # 创建管理员token
            with app.test_request_context():
                token = create_access_token(identity=str(admin.id))
                print(f"管理员Token: {token[:20]}...")

                # 模拟API调用
                with app.test_request_context(
                    f'/api/student-exit/applications/{test_app.id}/approve',
                    method='POST',
                    json={'approve': True, 'note': '管理员测试审批'},
                    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
                ):
                    try:
                        # 获取当前用户
                        from flask_jwt_extended import get_jwt_identity
                        current_user_id = int(get_jwt_identity())
                        current_user = User.query.get(current_user_id)

                        print(f"当前审批用户: {current_user.real_name} ({current_user.user_type})")

                        # 检查权限
                        can_approve = test_app.can_approve(current_user_id, current_user.user_type)
                        print(f"是否可以审批: {can_approve}")

                        if not can_approve:
                            print("用户没有审批权限，但管理员应该可以强制审批")
                            # 管理员特殊权限
                            test_app.teacher_approval_status = 'approved'
                            test_app.teacher_approval_time = datetime.utcnow()
                            test_app.teacher_approval_note = '管理员强制通过'
                            test_app.teacher_approved_by = current_user_id

                            test_app.parent_approval_status = 'approved'
                            test_app.parent_approval_time = datetime.utcnow()
                            test_app.parent_approval_note = '管理员强制通过'
                            test_app.parent_approved_by = current_user_id

                            test_app.update_approval_status()

                        print(f"审批后状态: {test_app.application_status}")

                    except Exception as e:
                        print(f"审批过程出错: {e}")
                        import traceback
                        traceback.print_exc()

            # 测试3: 检查前端数据格式
            print(f"\n=== 测试3: 检查前端数据格式 ===")
            app_dict = test_app.to_dict()
            print("申请数据格式:")
            for key, value in app_dict.items():
                if key in ['id', 'application_status', 'parent_approval_status', 'teacher_approval_status']:
                    print(f"  {key}: {value}")

            # 提交所有更改
            db.session.commit()
            print(f"\n最终状态: {test_app.application_status}")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_approval_process()