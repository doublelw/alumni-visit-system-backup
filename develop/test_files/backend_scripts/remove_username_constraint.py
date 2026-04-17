#!/usr/bin/env python3
"""
直接移除用户名的唯一约束
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

        # 1. 检查数据库中的表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("数据库中的表:")
        for table in tables:
            print(f"  {table[0]}")

        # 2. 检查是否存在 users_new 表
        users_new_exists = any('users_new' in str(table) for table in tables)
        users_exists = any('users' in str(table) for table in tables)

        if users_new_exists and not users_exists:
            # 如果只有 users_new 表，直接重命名为 users
            print("发现 users_new 表，直接重命名为 users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
        elif users_exists:
            # 如果有 users 表，检查是否有唯一约束
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            print("当前用户表结构:")
            for col in columns:
                print(f"  {col}")

            # 检查索引
            cursor.execute("PRAGMA index_list(users)")
            indexes = cursor.fetchall()
            has_unique_username = False
            for idx in indexes:
                if idx[2] == 1:  # unique index
                    cursor.execute(f"PRAGMA index_info({idx[1]})")
                    idx_info = cursor.fetchall()
                    for info in idx_info:
                        if info[2] == 'username':
                            has_unique_username = True
                            break

            if not has_unique_username:
                print("用户名没有唯一约束，无需修改")
                return True
        else:
            print("没有找到用户表")
            return False

        # 3. 创建没有唯一约束的新表
        cursor.execute("DROP TABLE IF EXISTS users_new")
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid VARCHAR(36) UNIQUE NOT NULL,
                username VARCHAR(50) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                real_name VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20) NOT NULL,
                user_type VARCHAR(255) DEFAULT 'alumni' NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                organization_id INTEGER,
                student_id VARCHAR(50),
                employee_id VARCHAR(50),
                is_visitable BOOLEAN DEFAULT 0 NOT NULL,
                class_id VARCHAR(50),
                grade VARCHAR(20),
                parent_student_id INTEGER,
                student_parent_id INTEGER,
                wechat VARCHAR(50),
                wechat_openid VARCHAR(100),
                wechat_nickname VARCHAR(100),
                is_class_teacher BOOLEAN DEFAULT 0 NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. 复制数据（如果存在 users 表）
        cursor.execute("""
            INSERT INTO users_new (
                id, uuid, username, password_hash, real_name, email, phone, user_type, status,
                organization_id, student_id, employee_id, is_visitable, class_id, grade,
                parent_student_id, student_parent_id, wechat, wechat_openid, wechat_nickname,
                is_class_teacher, created_at, updated_at
            )
            SELECT
                id, uuid, username, password_hash, real_name, email, phone, user_type, status,
                organization_id, student_id, employee_id, is_visitable, class_id, grade,
                parent_student_id, student_parent_id, wechat, wechat_openid, wechat_nickname,
                is_class_teacher, created_at, updated_at
            FROM users
        """)

        # 5. 替换表
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        # 6. 重建索引（非唯一索引）
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_uuid ON users(uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_phone ON users(phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_username ON users(username)")

        # 部分唯一索引在邮箱上（只对非NULL值）
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_partial ON users(email) WHERE email IS NOT NULL AND email != ''")

        conn.commit()
        print("成功移除用户名唯一约束")

        # 7. 验证
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