"""
数据库迁移脚本：将user_type字段从枚举类型改为字符串类型以支持多用户类型
"""

import sqlite3
import sys
import os

def migrate_database():
    """迁移数据库，更新user_type字段类型"""
    db_path = 'backend/instance/alumni_system_dev.db'

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        # 备份数据库
        backup_path = db_path + '.backup'
        if os.path.exists(backup_path):
            os.remove(backup_path)

        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")

        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建临时表
        print("创建临时表...")
        cursor.execute('''
            CREATE TABLE users_temp (
                id INTEGER PRIMARY KEY,
                uuid TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                real_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                user_type TEXT NOT NULL DEFAULT 'alumni',
                status TEXT NOT NULL DEFAULT 'pending',
                organization_id INTEGER,
                student_id TEXT,
                employee_id TEXT,
                class_id TEXT,
                grade TEXT,
                is_class_teacher INTEGER DEFAULT 0,
                is_visitable INTEGER DEFAULT 0,
                parent_student_id INTEGER,
                student_parent_id INTEGER,
                wechat_nickname TEXT,
                wechat_openid TEXT,
                face_encodings TEXT,
                face_threshold REAL DEFAULT 0.6,
                last_login TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        # 复制数据到临时表
        print("复制现有数据...")
        cursor.execute('''
            INSERT INTO users_temp
            SELECT id, uuid, username, password_hash, real_name, email, phone,
                   user_type, status, organization_id, student_id, employee_id,
                   class_id, grade, is_class_teacher, is_visitable, parent_student_id,
                   student_parent_id, wechat_nickname, wechat_openid, face_encodings,
                   face_threshold, last_login, created_at, updated_at
            FROM users
        ''')

        # 删除原表
        print("删除原表...")
        cursor.execute('DROP TABLE users')

        # 重命名临时表
        print("重命名表...")
        cursor.execute('ALTER TABLE users_temp RENAME TO users')

        # 重建索引
        print("重建索引...")
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_users_uuid ON users (uuid)')

        # 提交事务
        conn.commit()
        print("数据库迁移完成！")

        # 验证数据
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total = cursor.fetchone()[0]
        print(f"总用户数: {total}")

        cursor.execute("SELECT user_type, COUNT(*) as count FROM users GROUP BY user_type")
        print("用户类型分布:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} 人")

        return True

    except Exception as e:
        print(f"迁移失败: {e}")
        # 恢复备份
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            print(f"已恢复数据库备份")
        return False

    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== 用户类型字段迁移 ===")
    success = migrate_database()

    if success:
        print("\n迁移成功！现在用户类型字段支持存储多个类型（逗号分隔）")
        print("   例如: 'student,teacher,alumni'")
    else:
        print("\n迁移失败，请检查错误信息")
        sys.exit(1)