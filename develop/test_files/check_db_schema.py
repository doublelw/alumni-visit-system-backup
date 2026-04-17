#!/usr/bin/env python3
"""
检查数据库实际表结构
"""
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db

def check_db_schema():
    app = create_app('development')

    with app.app_context():
        print("=== 数据库表结构详细检查 ===")

        # 检查用户表结构
        inspector = db.inspect(db.engine)

        print("\n=== users 表结构 ===")
        if 'users' in inspector.get_table_names():
            columns = inspector.get_columns('users')
            for col in columns:
                nullable_str = "NULL" if col['nullable'] else "NOT NULL"
                default_str = f" DEFAULT {col['default']}" if col['default'] else ""
                print(f"  - {col['name']}: {col['type']} {nullable_str}{default_str}")

        print("\n=== student_exit_applications 表结构 ===")
        if 'student_exit_applications' in inspector.get_table_names():
            columns = inspector.get_columns('student_exit_applications')
            for col in columns:
                nullable_str = "NULL" if col['nullable'] else "NOT NULL"
                default_str = f" DEFAULT {col['default']}" if col['default'] else ""
                print(f"  - {col['name']}: {col['type']} {nullable_str}{default_str}")

            # 检查外键约束
            foreign_keys = inspector.get_foreign_keys('student_exit_applications')
            if foreign_keys:
                print("\n  外键约束:")
                for fk in foreign_keys:
                    print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        else:
            print("  ❌ student_exit_applications 表不存在!")

if __name__ == "__main__":
    check_db_schema()