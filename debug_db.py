#!/usr/bin/env python3
"""
调试数据库问题
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.visit_application import VisitApplication

def debug_database():
    """调试数据库问题"""
    app = create_app()

    with app.app_context():
        print("=== 数据库调试信息 ===")

        # 检查用户
        users = User.query.all()
        print(f"用户总数: {len(users)}")
        for user in users:
            print(f"用户ID: {user.id}, 用户名: {user.username}, 类型: {user.user_type}")

        # 检查访问申请
        try:
            applications = VisitApplication.query.all()
            print(f"访问申请总数: {len(applications)}")
            for app in applications:
                print(f"申请ID: {app.id}, 申请人ID: {app.applicant_id}, 状态: {app.application_status}")
        except Exception as e:
            print(f"查询访问申请出错: {e}")
            print(f"错误类型: {type(e)}")

            # 检查表结构
            print("\n=== VisitApplication表结构 ===")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = inspector.get_columns('visit_applications')
            for col in columns:
                print(f"列名: {col['name']}, 类型: {col['type']}")

if __name__ == "__main__":
    debug_database()