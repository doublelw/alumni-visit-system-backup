#!/usr/bin/env python3
"""
添加学生出校申请验证码字段的数据库迁移脚本
"""

import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app import create_app, db

def add_verification_code_field():
    """添加verification_code字段到student_exit_applications表"""

    app = create_app()

    with app.app_context():
        try:
            # 检查字段是否已存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = inspector.get_columns('student_exit_applications')
            column_names = [col['name'] for col in columns]

            if 'verification_code' not in column_names:
                # 添加字段
                with db.engine.connect() as conn:
                    conn.execute(db.text("""
                        ALTER TABLE student_exit_applications
                        ADD COLUMN verification_code VARCHAR(6) COMMENT '6位验证码'
                    """))
                    conn.commit()

                print("✅ 成功添加verification_code字段")
            else:
                print("✅ verification_code字段已存在")

        except Exception as e:
            print(f"❌ 添加字段失败: {str(e)}")
            return False

        return True

if __name__ == '__main__':
    print("开始添加学生出校申请验证码字段...")
    success = add_verification_code_field()

    if success:
        print("🎉 数据库迁移完成！")
    else:
        print("💥 数据库迁移失败！")
        sys.exit(1)