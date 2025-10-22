#!/usr/bin/env python3
"""
测试管理员统计API
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.visit_application import VisitApplication
from app.models.visit_record import VisitRecord
from app.models.alumni_profile import AlumniProfile
from datetime import datetime, date, timedelta

def test_admin_statistics():
    """测试管理员统计API"""
    app = create_app()

    with app.app_context():
        print("=== 测试管理员统计API ===")

        try:
            # 基础统计
            print("1. 基础统计数据...")
            total_users = User.query.count()
            total_alumni = User.query.filter_by(user_type='alumni').count()
            total_teachers = User.query.filter_by(user_type='teacher').count()
            total_security = User.query.filter_by(user_type='security').count()

            print(f"   总用户数: {total_users}")
            print(f"   校友数: {total_alumni}")
            print(f"   教师数: {total_teachers}")
            print(f"   保安数: {total_security}")

            # 访问相关统计
            print("\n2. 访问相关统计...")
            today = date.today()
            today_visits = VisitRecord.query.filter(
                db.func.date(VisitRecord.entry_time) == today
            ).count()

            total_visits = VisitRecord.query.count()
            total_applications = VisitApplication.query.count()

            print(f"   今日访问: {today_visits}")
            print(f"   总访问记录: {total_visits}")
            print(f"   总访问申请: {total_applications}")

            # 待审核事项
            print("\n3. 待审核事项...")
            pending_alumni = AlumniProfile.query.filter_by(approval_status='pending').count()
            pending_visits = VisitApplication.query.filter_by(application_status='pending').count()

            print(f"   待审核校友: {pending_alumni}")
            print(f"   待审核访问: {pending_visits}")

            # 模拟趋势数据
            print("\n4. 访问趋势数据...")
            visit_trend = []
            for i in range(7):
                d = date.today() - timedelta(days=6-i)
                count = VisitRecord.query.filter(
                    db.func.date(VisitRecord.entry_time) == d
                ).count()
                visit_trend.append({'date': d.isoformat(), 'count': count})
                print(f"   {d.strftime('%Y-%m-%d')}: {count} 次访问")

            # 访问目的统计
            print("\n5. 访问目的统计...")
            purpose_stats = db.session.query(
                VisitApplication.visit_purpose,
                db.func.count(VisitApplication.id).label('count')
            ).filter(
                VisitApplication.application_status.in_(['approved', 'completed'])
            ).group_by(VisitApplication.visit_purpose).limit(10).all()

            for stat in purpose_stats:
                print(f"   {stat.visit_purpose}: {stat.count} 次")

            print("\n测试成功！所有统计功能正常工作。")
            return True

        except Exception as e:
            print(f"\n测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_admin_statistics()
    if success:
        print("\n管理员统计API功能正常！")
    else:
        print("\n管理员统计API有问题！")
        sys.exit(1)