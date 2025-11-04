"""
添加组织机构负责人字段迁移
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from sqlalchemy import text

def add_organization_leader_fields():
    """添加组织机构的负责人字段"""
    try:
        print("=== 添加组织机构负责人字段迁移 ===")

        # 创建应用实例
        app = create_app()

        with app.app_context():
            print("1. 检查数据库连接...")
            try:
                db.session.execute(text("SELECT 1"))
                print("成功: 数据库连接正常")
            except Exception as e:
                print(f"失败: 数据库连接失败: {e}")
                return False

            print("\n2. 检查organizations表结构...")
            try:
                # 获取表结构信息
                result = db.session.execute(text("PRAGMA table_info(organizations)"))
                columns = [row[1] for row in result.fetchall()]
                print(f"当前字段: {', '.join(columns)}")
            except Exception as e:
                print(f"失败: 检查表结构失败: {e}")
                return False

            print("\n3. 添加新字段...")

            # 需要添加的字段
            fields_to_add = [
                ("class_teacher_id", "INTEGER", "班主任用户ID"),
                ("head_teacher_id", "INTEGER", "年级组长用户ID"),
                ("leader_id", "INTEGER", "负责人用户ID")
            ]

            added_fields = []

            for field_name, field_type, comment in fields_to_add:
                if field_name not in columns:
                    try:
                        print(f"添加字段: {field_name}")
                        sql = f"ALTER TABLE organizations ADD COLUMN {field_name} {field_type}"
                        db.session.execute(text(sql))
                        added_fields.append(field_name)
                        print(f"成功: {field_name} 字段添加完成")
                    except Exception as e:
                        print(f"失败: 添加 {field_name} 字段失败: {e}")
                        return False
                else:
                    print(f"跳过: {field_name} 字段已存在")

            if added_fields:
                print("\n4. 提交数据库更改...")
                try:
                    db.session.commit()
                    print(f"成功: 数据库更改已提交，添加了 {len(added_fields)} 个新字段")
                except Exception as e:
                    print(f"失败: 提交更改失败: {e}")
                    db.session.rollback()
                    return False
            else:
                print("\n4. 所有字段都已存在，无需更改")

            print("\n5. 验证新字段...")
            try:
                result = db.session.execute(text("PRAGMA table_info(organizations)"))
                updated_columns = [row[1] for row in result.fetchall()]

                for field_name, _, _ in fields_to_add:
                    if field_name in updated_columns:
                        print(f"✓ {field_name} 字段验证成功")
                    else:
                        print(f"✗ {field_name} 字段验证失败")
                        return False
            except Exception as e:
                print(f"失败: 验证字段失败: {e}")
                return False

            print("\n=== 迁移完成 ===")
            return True

    except Exception as e:
        print(f"失败: 迁移过程中发生错误: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    success = add_organization_leader_fields()
    if success:
        print("\n🎉 组织机构负责人字段迁移成功！")
    else:
        print("\n💥 迁移失败，请查看上述错误信息！")
        sys.exit(1)