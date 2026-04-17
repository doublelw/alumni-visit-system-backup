"""
数据库迁移脚本 - 增强 visit_records 表字段

添加字段：
- visitor_type: 访问者类型
- destination: 访问目的地
- host_person: 接待人姓名
- host_person_id: 接待人ID
- guard_name: 门卫姓名
- info_complete: 信息完整度
- visit_purpose: 访问目的
"""

import sqlite3
import os

def migrate_visit_records_table():
    """增强 visit_records 表"""

    db_path = 'instance/alumni_system_dev.db'

    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("=" * 80)
        print("  开始迁移 visit_records 表")
        print("=" * 80)

        # 检查现有字段
        cursor.execute('PRAGMA table_info(visit_records)')
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n现有字段: {existing_columns}")

        # 添加新字段
        new_columns = {
            'visitor_type': 'VARCHAR(20)',
            'destination': 'VARCHAR(200)',
            'host_person': 'VARCHAR(100)',
            'host_person_id': 'INTEGER',
            'guard_name': 'VARCHAR(100)',
            'info_complete': 'BOOLEAN DEFAULT 0',
            'visit_purpose': 'TEXT'
        }

        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                print(f"\n添加字段: {column_name} ({column_type})")
                cursor.execute(f'ALTER TABLE visit_records ADD COLUMN {column_name} {column_type}')
                print(f"  [OK] 字段 {column_name} 添加成功")
            else:
                print(f"\n字段 {column_name} 已存在，跳过")

        # 为现有记录填充数据
        print("\n" + "=" * 80)
        print("  为现有记录填充数据")
        print("=" * 80)

        cursor.execute('SELECT id, user_id FROM visit_records')
        records = cursor.fetchall()

        print(f"\n需要更新的记录数: {len(records)}")

        for record_id, user_id in records:
            # 获取用户信息
            cursor.execute('SELECT user_type FROM users WHERE id = ?', (user_id,))
            user_result = cursor.fetchone()

            if user_result:
                visitor_type = user_result[0]

                # 更新 visitor_type
                cursor.execute(
                    'UPDATE visit_records SET visitor_type = ? WHERE id = ?',
                    (visitor_type, record_id)
                )

                print(f"  记录 {record_id}: 设置 visitor_type = {visitor_type}")

        # 提交事务
        conn.commit()

        print("\n" + "=" * 80)
        print("  迁移完成！")
        print("=" * 80)

        # 显示最终表结构
        cursor.execute('PRAGMA table_info(visit_records)')
        final_columns = cursor.fetchall()
        print("\n最终表结构:")
        for col in final_columns:
            print(f"  {col[1]:<20} {col[2]:<20}")

        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False

if __name__ == "__main__":
    success = migrate_visit_records_table()

    print("\n" + "=" * 80)
    if success:
        print("  [SUCCESS] 数据库迁移完成")
    else:
        print("  [FAIL] 数据库迁移失败")
    print("=" * 80)
