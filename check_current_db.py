#!/usr/bin/env python3
"""
检查当前Flask应用使用的数据库
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db

def check_current_db():
    """检查当前数据库"""
    app = create_app()

    with app.app_context():
        # 获取数据库文件路径
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"Flask应用当前使用的数据库: {db_path}")

        # 直接连接SQLite数据库
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # 检查所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"数据库中的表: {[t[0] for t in tables]}")

            # 检查visit_applications表
            if 'visit_applications' in [t[0] for t in tables]:
                print("visit_applications 表存在")
                cursor.execute("SELECT COUNT(*) FROM visit_applications")
                count = cursor.fetchone()[0]
                print(f"visit_applications 表中有 {count} 条记录")
            else:
                print("visit_applications 表不存在")

        except Exception as e:
            print(f"检查失败: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    check_current_db()