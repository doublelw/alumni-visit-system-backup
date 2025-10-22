#!/usr/bin/env python3
"""
创建测试访问记录
"""

from datetime import datetime, timedelta, date, time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.visit_application import VisitApplication
from app.models.visit_record import VisitRecord

def create_test_visit_records():
    """创建测试访问记录"""
    app = create_app()

    with app.app_context():
        print("正在创建测试访问记录...")

        # 获取或创建测试用户
        test_user = User.query.filter_by(username='test_alumni').first()
        if not test_user:
            test_user = User(
                username='test_alumni',
                email='test@example.com',
                phone='13800138000',
                real_name='测试校友',
                user_type='alumni',
                status='active'
            )
            test_user.set_password('123456')
            db.session.add(test_user)
            db.session.flush()

        # 获取或创建管理员用户（保安）
        security_user = User.query.filter_by(username='test_security').first()
        if not security_user:
            security_user = User(
                username='test_security',
                email='security@example.com',
                phone='13800138001',
                real_name='测试保安',
                user_type='security',
                status='active'
            )
            security_user.set_password('123456')
            db.session.add(security_user)
            db.session.flush()

        # 创建测试访问申请
        test_application = VisitApplication.query.filter_by(applicant_id=test_user.id).first()
        if not test_application:
            test_application = VisitApplication(
                applicant_id=test_user.id,
                visit_date=date.today() - timedelta(days=1),
                visit_time_start=time(9, 0),
                visit_time_end=time(11, 0),
                visit_purpose='参观校园',
                target_person='张老师',
                target_department='教务处',
                application_status='approved',
                approved_by=security_user.id,
                approval_time=datetime.utcnow() - timedelta(days=1, hours=2),
                qr_code='test_qr_code_12345'
            )
            db.session.add(test_application)
            db.session.flush()

        # 创建多个测试访问记录
        test_records = [
            {
                'entry_time': datetime.utcnow() - timedelta(days=1, hours=3),
                'exit_time': datetime.utcnow() - timedelta(days=1, hours=1),
                'verification_method': 'qr_code',
                'gate_name': '南门',
                'notes': '正常访问'
            },
            {
                'entry_time': datetime.utcnow() - timedelta(days=2, hours=2),
                'exit_time': None,  # 还未离开
                'verification_method': 'face',
                'gate_name': '北门',
                'notes': '人脸识别进入'
            },
            {
                'entry_time': datetime.utcnow() - timedelta(days=3, hours=4),
                'exit_time': datetime.utcnow() - timedelta(days=3, hours=2),
                'verification_method': 'manual',
                'gate_name': '东门',
                'notes': '人工核验'
            }
        ]

        for i, record_data in enumerate(test_records):
            existing_record = VisitRecord.query.filter_by(
                user_id=test_user.id,
                entry_time=record_data['entry_time']
            ).first()

            if not existing_record:
                record = VisitRecord(
                    user_id=test_user.id,
                    visit_application_id=test_application.id if i == 0 else None,
                    entry_time=record_data['entry_time'],
                    exit_time=record_data['exit_time'],
                    verification_method=record_data['verification_method'],
                    gate_name=record_data['gate_name'],
                    security_guard_id=security_user.id,
                    notes=record_data['notes']
                )
                db.session.add(record)

        try:
            db.session.commit()
            print("✅ 测试访问记录创建成功！")

            # 显示创建的记录
            records = VisitRecord.query.all()
            print(f"共创建了 {len(records)} 条访问记录：")
            for record in records:
                user = record.user
                status = "已完成" if record.exit_time else "进行中"
                print(f"  - {user.real_name} ({record.verification_method}) - {record.entry_time} - {status}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建测试访问记录失败: {str(e)}")
            return False

        return True

if __name__ == '__main__':
    success = create_test_visit_records()
    if success:
        print("\n🎉 测试数据准备完成！现在可以访问管理后台测试访问记录功能。")
        print("📱 访问 https://127.0.0.1:5000/admin")
        print("👤 测试校友账号: test_alumni / 123456")
        print("🔐 测试管理员账号: admin / 123456")
    else:
        print("❌ 测试数据创建失败！")
        sys.exit(1)