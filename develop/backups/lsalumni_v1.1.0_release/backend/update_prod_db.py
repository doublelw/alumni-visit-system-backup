#!/usr/bin/env python3
"""
更新生产数据库：添加wechat字段，修改email字段为可选
"""

import sqlite3
import os

def update_production_db():
    """更新生产数据库"""

    # 生产数据库文件路径
    db_path = '/var/www/lsalumni/backend/instance/alumni_system_prod.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查wechat字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        # 添加wechat字段（如果不存在）
        if 'wechat' not in columns:
            print("添加wechat字段...")
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN wechat VARCHAR(50) NULL
            """)
            print("成功添加wechat字段")

        # 检查email字段是否允许NULL值（通过检查表结构）
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        email_info = None
        for col in columns_info:
            if col[1] == 'email':
                email_info = col
                break

        if email_info and email_info[3] == 1:  # notnull = 1 表示不允许NULL
            print("修改email字段为可选...")
            # SQLite不支持直接修改列的NOT NULL约束，需要重建表
            cursor.execute("BEGIN TRANSACTION")

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
                    wechat, wechat_openid, wechat_nickname, is_class_teacher, created_at, updated_at
                )
                SELECT
                    id, uuid, username, password_hash, real_name, email, phone,
                    user_type, status, organization_id, student_id, employee_id,
                    is_visitable, class_id, grade, parent_student_id, student_parent_id,
                    wechat, wechat_openid, wechat_nickname, is_class_teacher, created_at, updated_at
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
        else:
            print("email字段已支持可选值")

        print("数据库更新完成！")
        return True

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_production_db()