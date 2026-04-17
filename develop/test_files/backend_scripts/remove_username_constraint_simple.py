#!/usr/bin/env python3
"""
简单版本：移除用户名的唯一约束 - 适用于生产环境
"""

import sqlite3
import os

def remove_username_unique_constraint():
    """移除用户名的唯一约束"""
    db_path = 'app.db'

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 检查当前表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("当前用户表结构:")
        for col in columns:
            print(f"  {col}")

        # 2. 创建没有唯一约束的新表（保持现有结构）
        cursor.execute("DROP TABLE IF EXISTS users_new")
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) NOT NULL,
                email VARCHAR(120),
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT 0 NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. 复制数据
        cursor.execute("""
            INSERT INTO users_new (id, username, email, password_hash, is_admin, created_at, updated_at)
            SELECT id, username, email, password_hash, is_admin, created_at, updated_at
            FROM users
        """)

        # 4. 替换表
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        # 5. 重建索引（非唯一索引）
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)")

        conn.commit()
        print("成功移除用户名唯一约束")

        # 6. 验证
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"用户数据总数: {count}")

        return True

    except Exception as e:
        print(f"错误: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("开始移除用户名唯一约束...")
    success = remove_username_unique_constraint()
    if success:
        print("操作完成！")
    else:
        print("操作失败！")