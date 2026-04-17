#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User

def activate_users():
    app = create_app()

    with app.app_context():
        try:
            # 激活所有测试用户
            users = User.query.all()

            for user in users:
                if user.status != 'active':
                    user.status = 'active'
                    print(f"激活用户: {user.username} ({user.real_name})")

            db.session.commit()
            print(f"已激活 {len(users)} 个用户")

            return True

        except Exception as e:
            print(f"激活用户失败: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("开始激活用户账户...")

    if activate_users():
        print("用户账户激活完成")
    else:
        print("用户账户激活失败")