#!/usr/bin/env python3
"""
调试API，检查学生出校申请数据流
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.student_exit_application import StudentExitApplication
from app.models.user import User
from datetime import datetime, timedelta

def debug_applications_api():
    app = create_app()
    with app.app_context():
        print("=== 调试学生出校申请API ===\n")

        # 1. 检查数据库中的所有学生出校申请
        all_applications = StudentExitApplication.query.order_by(StudentExitApplication.created_at.desc()).all()
        print(f"1. 数据库中的所有学生出校申请: {len(all_applications)} 个")

        for i, app in enumerate(all_applications, 1):
            student_name = app.student.real_name if app.student else '未知'
            print(f"   {i}. ID: {app.id}")
            print(f"      学生: {student_name} (ID: {app.student_id})")
            print(f"      状态: {app.application_status}")
            print(f"      创建时间: {app.created_at}")
            print(f"      出校日期: {app.exit_date}")
            print(f"      出校开始时间: {app.exit_time_start}")
            print(f"      出校结束时间: {app.exit_time_end}")
            print(f"      原因: {app.exit_reason}")
            print("---")

        # 2. 检查学生用户
        student_user = User.query.filter_by(username='student001').first()
        if student_user:
            print(f"\n2. 找到学生用户: {student_user.real_name} (ID: {student_user.id})")

            # 检查该学生的申请
            student_applications = StudentExitApplication.query.filter_by(student_id=student_user.id).all()
            print(f"   该学生的申请数量: {len(student_applications)}")

            for app in student_applications:
                print(f"   - 申请ID: {app.id}, 状态: {app.application_status}, 创建时间: {app.created_at}")
                print(f"     原因: {app.exit_reason}")
        else:
            print("\n2. 未找到学生用户 'student001'")

        # 3. 检查最近提交的申请（最近30分钟）
        now = datetime.now()
        thirty_minutes_ago = now - timedelta(minutes=30)
        recent_applications = StudentExitApplication.query.filter(
            StudentExitApplication.created_at >= thirty_minutes_ago
        ).order_by(StudentExitApplication.created_at.desc()).all()

        print(f"\n3. 最近30分钟内的申请: {len(recent_applications)} 个")
        for app in recent_applications:
            time_diff = now - app.created_at
            print(f"   - ID: {app.id}, 创建于: {time_diff.total_seconds():.0f} 秒前")

        # 4. 模拟API请求
        print(f"\n4. 模拟前端API调用...")

        # 模拟 /api/student-exit/applications/recent (以student001用户身份)
        student_user = User.query.filter_by(username='student001').first()
        if student_user:
            recent_api_apps = StudentExitApplication.query.filter_by(
                student_id=student_user.id
            ).order_by(StudentExitApplication.created_at.desc()).limit(5).all()

            print(f"   API会返回给student001的最近申请: {len(recent_api_apps)} 个")
            for app in recent_api_apps:
                student_name = app.student.real_name if app.student else '未知'
                print(f"   - ID: {app.id}, 状态: {app.application_status}, 学生: {student_name}")

            # 5. 检查字段映射
            print(f"\n5. 检查API字段映射...")
            if recent_api_apps:
                app = recent_api_apps[0]
                student_name = app.student.real_name if app.student else '未知'
                print(f"   示例申请对象:")
                print(f"   - id: {app.id}")
                print(f"   - student_id: {app.student_id}")
                print(f"   - student.real_name: {student_name}")
                print(f"   - application_status: {app.application_status}")
                print(f"   - exit_date: {app.exit_date}")
                print(f"   - exit_time_start: {app.exit_time_start}")
                print(f"   - exit_reason: {app.exit_reason}")
                print(f"   - created_at: {app.created_at}")

                # 模拟API响应的映射（和实际API一致）
                api_mapping = {
                    'id': app.id,
                    'applicant_name': student_name,
                    'student_name': student_name,
                    'reason': app.exit_reason,
                    'exit_date': app.exit_date.isoformat() if app.exit_date else None,
                    'exit_time': app.exit_time_start.strftime('%H:%M') if app.exit_time_start else None,
                    'status': app.application_status,
                    'application_status': app.application_status,
                    'created_at': app.created_at.isoformat() if app.created_at else None,
                    'application_date': app.created_at.isoformat() if app.created_at else None
                }

                print(f"   映射后的API响应:")
                for key, value in api_mapping.items():
                    print(f"   - {key}: {value}")
        else:
            print("   未找到student001用户，无法模拟API调用")

if __name__ == '__main__':
    debug_applications_api()