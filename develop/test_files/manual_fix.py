#!/usr/bin/env python3
"""
手动添加缺失的数据库字段
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
import sqlite3

def manual_add_column():
    """手动添加缺失的列"""
    app = create_app()

    with app.app_context():
        # 获取数据库文件路径
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

        print(f"数据库路径: {db_path}")

        # 直接连接SQLite数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # 检查列是否存在
            cursor.execute("PRAGMA table_info(visit_applications)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            print(f"现有列: {column_names}")

            if 'needs_profile_approval' not in column_names:
                print("添加 needs_profile_approval 列...")
                cursor.execute("""
                    ALTER TABLE visit_applications
                    ADD COLUMN needs_profile_approval BOOLEAN NOT NULL DEFAULT 0
                """)
                conn.commit()
                print("列添加成功！")
            else:
                print("needs_profile_approval 列已存在")

        except Exception as e:
            print(f"操作失败: {e}")
            conn.rollback()
        finally:
            conn.close()

        # 验证添加结果
        try:
            from app.models.visit_application import VisitApplication
            applications = VisitApplication.query.all()
            print(f"成功查询到 {len(applications)} 条访问申请记录")
        except Exception as e:
            print(f"验证查询失败: {e}")

if __name__ == "__main__":
    manual_add_column()