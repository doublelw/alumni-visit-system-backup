#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动添加dining_companions字段到alumni_profiles表
"""

import sqlite3
import sys
import os

# 数据库文件路径
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'alumni_system_dev.db')

def add_dining_companions_column():
    """添加dining_companions列到alumni_profiles表"""
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(alumni_profiles)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'dining_companions' not in columns:
            print("添加dining_companions列...")
            cursor.execute("""
                ALTER TABLE alumni_profiles
                ADD COLUMN dining_companions INTEGER DEFAULT 1
            """)
            print("✓ dining_companions列添加成功")
        else:
            print("dining_companions列已存在")

        # 提交更改
        conn.commit()

        # 验证列是否添加成功
        cursor.execute("PRAGMA table_info(alumni_profiles)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'dining_companions' in columns:
            print("✓ 验证成功：dining_companions列存在于alumni_profiles表中")
        else:
            print("✗ 验证失败：dining_companions列未找到")
            return False

        conn.close()
        return True

    except Exception as e:
        print(f"✗ 错误：{str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == '__main__':
    print(f"数据库路径: {db_path}")

    if not os.path.exists(db_path):
        print(f"✗ 数据库文件不存在: {db_path}")
        sys.exit(1)

    success = add_dining_companions_column()

    if success:
        print("✓ dining_companions字段添加完成")
        sys.exit(0)
    else:
        print("✗ dining_companions字段添加失败")
        sys.exit(1)