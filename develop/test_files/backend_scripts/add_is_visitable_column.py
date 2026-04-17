#!/usr/bin/env python3
"""
添加is_visitable列到users表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def add_is_visitable_column():
    """添加is_visitable列到users表"""

    app = create_app()
    with app.app_context():
        print("正在添加is_visitable列到users表...")

        try:
            # 检查列是否已存在
            result = db.session.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]

            if 'is_visitable' not in columns:
                # 添加列
                db.session.execute(text("ALTER TABLE users ADD COLUMN is_visitable BOOLEAN DEFAULT 0"))
                db.session.commit()
                print("成功添加is_visitable列")
            else:
                print("is_visitable列已存在")

        except Exception as e:
            db.session.rollback()
            print(f"添加列失败: {str(e)}")
            return

if __name__ == '__main__':
    add_is_visitable_column()