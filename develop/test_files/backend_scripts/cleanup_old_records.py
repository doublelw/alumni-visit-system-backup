"""
清理旧审批记录
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.visit_application import VisitApplication
from app.models.user import User

def cleanup():
    app = create_app()
    with app.app_context():
        # 查找校友用户
        user = User.query.filter_by(user_type='alumni', status='active').first()
        if not user:
            print("[X] 未找到校友用户")
            return

        print(f"[用户] {user.real_name} (ID: {user.id})")

        # 查找该用户的所有审批记录
        applications = VisitApplication.query.filter_by(applicant_id=user.id).all()

        print(f"[找到] {len(applications)} 条审批记录:")
        for app in applications:
            print(f"      ID: {app.id}, 日期: {app.visit_date}, 状态: {app.application_status}, 审批时间: {app.approval_time}")

        # 删除所有记录
        from app import db
        for app in applications:
            db.session.delete(app)
        db.session.commit()

        print(f"\n[OK] 已清理 {len(applications)} 条记录")

if __name__ == '__main__':
    cleanup()
