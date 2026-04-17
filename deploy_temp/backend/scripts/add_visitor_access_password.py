#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加访客访问密码字段
"""

import os
import sys

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from sqlalchemy import text

def add_access_password_field():
    """添加access_password字段到visitor_profiles表"""
    app = create_app()

    with app.app_context():
        print("[开始] 添加访客访问密码字段...")

        try:
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('visitor_profiles')]

            if 'access_password' in columns:
                print("[信息] access_password字段已存在，跳过添加")
            else:
                # 添加字段
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE visitor_profiles ADD COLUMN access_password VARCHAR(10)"))
                    conn.commit()

                print("[成功] 已添加access_password字段")

            # 验证字段是否添加成功
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('visitor_profiles')]

            if 'access_password' in columns:
                print("[完成] 访客访问密码字段添加成功！")
            else:
                print("[错误] 字段添加失败")

        except Exception as e:
            print(f"[错误] 添加字段失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    add_access_password_field()
