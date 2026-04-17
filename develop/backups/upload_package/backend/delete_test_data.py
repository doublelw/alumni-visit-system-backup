#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除测试数据脚本
用于清理系统演示和测试数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app import db

def delete_test_data():
    """删除所有测试数据"""
    app = create_app()

    with app.app_context():
        try:
            from app.models.user import User
            from app.models.alumni_profile import AlumniProfile
            from app.models.visit_application import VisitApplication
            from app.models.vehicle import Vehicle
            from app.models.visit_record import VisitRecord

            deleted_count = 0

            # 删除测试访问记录
            visit_records = VisitRecord.query.filter(VisitRecord.notes.like('%测试%')).all()
            for record in visit_records:
                db.session.delete(record)
                deleted_count += 1
            print(f"Deleted {len(visit_records)} test visit records")

            # 删除测试访问申请
            test_applicants = User.query.filter(User.username.like('%alumni%')).all()
            applicant_ids = [u.id for u in test_applicants]
            if applicant_ids:
                applications = VisitApplication.query.filter(VisitApplication.applicant_id.in_(applicant_ids)).all()
                for app in applications:
                    db.session.delete(app)
                    deleted_count += 1
                print(f"Deleted {len(applications)} test visit applications")

            # 删除测试车辆
            if applicant_ids:
                vehicles = Vehicle.query.filter(Vehicle.user_id.in_(applicant_ids)).all()
                for vehicle in vehicles:
                    db.session.delete(vehicle)
                    deleted_count += 1
                print(f"Deleted {len(vehicles)} test vehicles")

            # 删除测试校友档案
            if applicant_ids:
                alumni_profiles = AlumniProfile.query.filter(AlumniProfile.user_id.in_(applicant_ids)).all()
                for profile in alumni_profiles:
                    db.session.delete(profile)
                    deleted_count += 1
                print(f"Deleted {len(alumni_profiles)} test alumni profiles")

            # 删除测试用户账户（不包括管理员）
            test_users = User.query.filter(
                (User.username.like('%alumni%')) |
                (User.username.like('%teacher%')) |
                (User.username.like('%security%'))
            ).all()
            for user in test_users:
                db.session.delete(user)
                deleted_count += 1
            print(f"Deleted {len(test_users)} test user accounts")

            db.session.commit()
            print(f"\nSuccessfully deleted {deleted_count} test records")
            print("\nRemaining data:")
            print("- Admin account: admin")
            print("- Production data preserved")

        except Exception as e:
            db.session.rollback()
            print(f"Delete test data failed: {e}")

def main():
    """主函数：删除测试数据"""
    print("Deleting test data...")
    print("=" * 50)
    print("WARNING: This will delete all test data including:")
    print("- Test alumni accounts and profiles")
    print("- Test teacher accounts")
    print("- Test security accounts")
    print("- Test visit applications")
    print("- Test vehicle records")
    print("- Test visit records")
    print("- Admin account will be preserved")
    print("=" * 50)

    # 确认删除
    confirm = input("\nAre you sure you want to delete all test data? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return

    delete_test_data()
    print("\nTest data cleanup completed!")

if __name__ == '__main__':
    main()