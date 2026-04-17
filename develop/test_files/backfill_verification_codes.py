#!/usr/bin/env python3
"""
为已有的返校日活动报名记录补充验证码
"""

import random
import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.event_registration import EventRegistration

def generate_verification_code():
    """生成6位数字验证码"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def backfill_verification_codes():
    """为没有验证码的记录补充验证码"""
    app = create_app()

    with app.app_context():
        # 查询所有没有验证码的有效报名记录
        registrations = EventRegistration.query.filter_by(status='active').all()

        updated_count = 0
        for registration in registrations:
            if not registration.verification_code:
                registration.verification_code = generate_verification_code()
                updated_count += 1
                print(f"为用户 {registration.username} 生成验证码: {registration.verification_code}")

        # 保存更改
        if updated_count > 0:
            db.session.commit()
            print(f"\n成功为 {updated_count} 条记录补充验证码")
        else:
            print("\n所有记录都已有验证码，无需补充")

if __name__ == '__main__':
    backfill_verification_codes()