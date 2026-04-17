#!/usr/bin/env python3
"""
添加wechat字段到users表
"""

import sqlite3
import os

def add_wechat_field():
    """添加wechat字段到users表"""

    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'alumni_system_dev.db')

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查wechat字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'wechat' in columns:
            print("wechat字段已存在")
            return True

        # 添加wechat字段
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN wechat VARCHAR(50) NULL
        """)

        conn.commit()
        print("成功添加wechat字段到users表")
        return True

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_wechat_field()