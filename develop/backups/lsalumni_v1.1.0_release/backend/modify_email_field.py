#!/usr/bin/env python3
"""
修改email字段为可选（nullable）
"""

import sqlite3
import os

def modify_email_field():
    """修改email字段为可选"""

    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'alumni_system_dev.db')

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # SQLite不支持直接修改列的NOT NULL约束，需要重建表
        print("正在重建users表以支持email字段为可选...")

        # 1. 创建新的users表结构
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid VARCHAR(36) NOT NULL,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                real_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20) NOT NULL,
                user_type VARCHAR(255) NOT NULL DEFAULT 'alumni',
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                organization_id INTEGER,
                student_id VARCHAR(50),
                employee_id VARCHAR(50),
                is_visitable BOOLEAN NOT NULL DEFAULT 0,
                class_id VARCHAR(50),
                grade VARCHAR(20),
                parent_student_id INTEGER,
                student_parent_id INTEGER,
                wechat VARCHAR(50),
                wechat_openid VARCHAR(100),
                wechat_nickname VARCHAR(100),
                is_class_teacher BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (organization_id) REFERENCES organizations (id),
                FOREIGN KEY (parent_student_id) REFERENCES users (id),
                FOREIGN KEY (student_parent_id) REFERENCES users (id)
            )
        """)

        # 2. 复制数据
        cursor.execute("""
            INSERT INTO users_new (
                id, uuid, username, password_hash, real_name, email, phone,
                user_type, status, organization_id, student_id, employee_id,
                is_visitable, class_id, grade, parent_student_id, student_parent_id,
                wechat_openid, wechat_nickname, is_class_teacher, created_at, updated_at
            )
            SELECT
                id, uuid, username, password_hash, real_name, email, phone,
                user_type, status, organization_id, student_id, employee_id,
                is_visitable, class_id, grade, parent_student_id, student_parent_id,
                wechat_openid, wechat_nickname, is_class_teacher, created_at, updated_at
            FROM users
        """)

        # 3. 删除旧表
        cursor.execute("DROP TABLE users")

        # 4. 重命名新表
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        # 5. 重建索引
        cursor.execute("CREATE UNIQUE INDEX ix_users_uuid ON users (uuid)")
        cursor.execute("CREATE UNIQUE INDEX ix_users_username ON users (username)")
        cursor.execute("CREATE INDEX ix_users_email ON users (email)")

        conn.commit()
        print("成功修改email字段为可选")
        return True

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    modify_email_field()