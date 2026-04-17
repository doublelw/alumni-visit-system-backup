#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建测试审批记录（直接写入校内数据库）

用于测试同步功能，不需要微信云数据库
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.visit_application import VisitApplication

def create_test_approvals():
    """创建测试审批记录"""
    app = create_app()

    with app.app_context():
        print("创建测试审批记录...")

        # 获取或创建测试申请记录
        test_codes = ['123456', '654321', '111111']

        for code in test_codes:
            # 检查是否已存在
            existing = VisitApplication.query.filter_by(access_code=code).first()

            if not existing:
                # 创建新的测试申请
                if code == '123456':
                    # 家长进校
                    application = VisitApplication(
                        visitor_name='张父',
                        phone='13800138000',
                        visit_reason='家长进校',
                        access_code=code,
                        status='pending',
                        created_at=datetime.now()
                    )
                elif code == '654321':
                    # 学生请假
                    application = VisitApplication(
                        visitor_name='张父（家长）',
                        phone='13800138000',
                        visit_reason='学生请假：张三',
                        access_code=code,
                        status='pending',
                        created_at=datetime.now()
                    )
                else:
                    # 另一个家长进校
                    application = VisitApplication(
                        visitor_name='李母',
                        phone='13900139000',
                        visit_reason='家长进校',
                        access_code=code,
                        status='pending',
                        created_at=datetime.now()
                    )

                db.session.add(application)
                print(f"  ✅ 创建测试申请: {code}")
            else:
                print(f"  ⚠ 申请已存在: {code} (状态: {existing.status})")

        try:
            db.session.commit()
            print("\n✅ 测试数据创建完成！")
            print(f"\n现在可以使用以下审批码进行测试:")
            for code in test_codes:
                print(f"  - {code}")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 创建失败: {str(e)}")

if __name__ == '__main__':
    create_test_approvals()
