#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试访问申请数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app import db
from datetime import datetime, date, timedelta

def create_test_applications():
    """创建测试访问申请"""
    app = create_app()

    with app.app_context():
        try:
            # 导入模型
            from app.models.user import User
            from app.models.visit_application import VisitApplication

            # 查找校友用户
            alumni_user = User.query.filter_by(user_type='alumni').first()
            if not alumni_user:
                print("未找到校友用户，请先注册一个校友账号")
                return

            # 检查是否已存在测试申请
            existing_count = VisitApplication.query.filter_by(applicant_id=alumni_user.id).count()
            if existing_count >= 3:
                print(f"测试申请数据已存在（{existing_count}条），跳过创建")
                return

            # 创建测试申请
            tomorrow = date.today() + timedelta(days=1)
            test_applications = [
                {
                    'visit_date': tomorrow,
                    'visit_time_start': datetime.strptime('09:00', '%H:%M').time(),
                    'visit_time_end': datetime.strptime('10:00', '%H:%M').time(),
                    'visit_purpose': '学术交流',
                    'target_person': '张伟',
                    'target_department': '计算机科学与技术学院',
                    'target_work_id': 'EMP001'
                },
                {
                    'visit_date': tomorrow,
                    'visit_time_start': datetime.strptime('14:00', '%H:%M').time(),
                    'visit_time_end': datetime.strptime('15:30', '%H:%M').time(),
                    'visit_purpose': '拜访老师',
                    'target_person': '李娜',
                    'target_department': '软件学院',
                    'target_work_id': 'EMP002'
                },
                {
                    'visit_date': tomorrow + timedelta(days=1),
                    'visit_time_start': datetime.strptime('10:00', '%H:%M').time(),
                    'visit_time_end': datetime.strptime('11:00', '%H:%M').time(),
                    'visit_purpose': '参观校园',
                    'target_person': '王强',
                    'target_department': '信息工程学院',
                    'target_work_id': 'EMP003'
                }
            ]

            for app_data in test_applications:
                application = VisitApplication(
                    applicant_id=alumni_user.id,
                    **app_data
                )
                db.session.add(application)

            db.session.commit()
            print(f"成功创建 {len(test_applications)} 条测试访问申请")
            print(f"申请人: {alumni_user.real_name} ({alumni_user.username})")
            print("现在教师登录后可以在首页看到待审核的申请")

        except Exception as e:
            db.session.rollback()
            print(f"创建测试申请失败: {e}")

if __name__ == '__main__':
    create_test_applications()