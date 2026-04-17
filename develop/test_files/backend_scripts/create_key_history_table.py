"""
创建密钥历史记录表

直接在数据库中创建 key_history 表
"""

import sqlite3
import os

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'alumni_system_dev.db')

print(f"Database path: {db_path}")

if not os.path.exists(db_path):
    print("Database file does not exist")
    exit(1)

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查表是否已存在
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='key_history'
    """)

    if cursor.fetchone():
        print("key_history table already exists")
    else:
        # 创建表
        cursor.execute("""
            CREATE TABLE key_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_type VARCHAR(50) NOT NULL,
                old_key VARCHAR(100),
                new_key VARCHAR(100),
                changed_by VARCHAR(100) NOT NULL,
                changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reason VARCHAR(200)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX ix_key_history_key_type
            ON key_history (key_type)
        """)

        conn.commit()
        print("[OK] key_history table created successfully")

    # 验证表结构
    cursor.execute("PRAGMA table_info(key_history)")
    columns = cursor.fetchall()
    print("\nTable structure:")
    for col in columns:
        print(f"  - {col[1]}: {col[2]}")

except Exception as e:
    conn.rollback()
    print(f"[ERROR] Failed to create table: {e}")
finally:
    conn.close()

print("\nDone!")
