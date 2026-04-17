#!/usr/bin/env python3
"""
清空学生出校申请数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.student_exit_application import StudentExitApplication

def clear_student_exit_applications():
    app = create_app()
    with app.app_context():
        # 查询所有学生出校申请
        applications = StudentExitApplication.query.all()
        print(f"找到 {len(applications)} 个学生出校申请:")

        for app in applications:
            print(f"  - ID: {app.id}, 学生: {app.student_id if app.student else '未知'}, 原因: {app.exit_reason}, 日期: {app.exit_date}")

        if applications:
            # 删除所有申请
            StudentExitApplication.query.delete()
            db.session.commit()
            print(f"已删除所有 {len(applications)} 个学生出校申请")
        else:
            print("没有找到学生出校申请")

        # 验证删除结果
        remaining = StudentExitApplication.query.count()
        print(f"剩余申请数量: {remaining}")

if __name__ == '__main__':
    clear_student_exit_applications()