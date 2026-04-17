#!/usr/bin/env python3
"""
调试学生出校申请API
"""
import sys
import os
import traceback

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from datetime import datetime, date, time

def debug_student_exit():
    app = create_app('development')

    with app.app_context():
        print("=== 调试学生出校申请创建 ===")

        # 获取学生用户
        student = User.query.filter_by(username='test_student').first()
        if not student:
            print("❌ 学生用户不存在")
            return

        print(f"✅ 找到学生: {student.real_name} (ID: {student.id})")

        # 模拟申请数据
        application_data = {
            'student_id': student.id,
            'exit_date': '2025-11-05',
            'exit_time_start': '14:00',
            'exit_time_end': '18:00',
            'exit_reason': '回家复习',
            'destination': '家里',
            'transport_method': '步行',
            'parent_contact': '13800000002',
            'notes': '提前回家复习备考'
        }

        print(f"申请数据: {application_data}")

        try:
            # 创建申请记录
            application = StudentExitApplication(
                student_id=application_data['student_id'],
                applicant_id=student.id,  # 申请人就是学生自己
                exit_date=datetime.strptime(application_data['exit_date'], '%Y-%m-%d').date(),
                exit_time_start=datetime.strptime(application_data['exit_time_start'], '%H:%M').time(),
                exit_time_end=datetime.strptime(application_data['exit_time_end'], '%H:%M').time(),
                exit_reason=application_data['exit_reason'],
                destination=application_data.get('destination', ''),
                transport_method=application_data.get('transport_method', ''),
                emergency_contact=application_data.get('parent_contact', ''),
                emergency_phone=application_data.get('parent_contact', '')
            )

            print(f"✅ 申请对象创建成功: ID {application.id}")

            # 保存到数据库
            db.session.add(application)
            print("✅ 已添加到session")

            db.session.commit()
            print(f"✅ 数据库提交成功! 申请ID: {application.id}")

            # 验证数据是否正确保存
            saved_app = StudentExitApplication.query.get(application.id)
            if saved_app:
                print(f"✅ 验证成功: 申请状态 {saved_app.application_status}")
                print(f"   - 学生ID: {saved_app.student_id}")
                print(f"   - 出校日期: {saved_app.exit_date}")
                print(f"   - 出校原因: {saved_app.exit_reason}")
            else:
                print("❌ 验证失败: 数据未保存")

        except Exception as e:
            print(f"❌ 创建申请失败: {str(e)}")
            print("详细错误:")
            traceback.print_exc()
            db.session.rollback()

if __name__ == "__main__":
    debug_student_exit()