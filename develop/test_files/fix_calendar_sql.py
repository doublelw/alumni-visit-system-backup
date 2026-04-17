#!/usr/bin/env python3
"""
使用原生SQL修复校历表中的无效枚举值
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db

def fix_invalid_enum_with_sql():
    """使用原生SQL修复无效枚举值"""
    app = create_app()

    with app.app_context():
        print("=== 使用原生SQL修复校历枚举值 ===")

        try:
            # 首先查看有问题的数据
            print("1. 检查有问题的数据...")

            # 查看club_type字段的问题数据
            result = db.session.execute(db.text("""
                SELECT id, title, club_type
                FROM school_calendar
                WHERE club_type IS NOT NULL
                AND club_type NOT IN ('academic', 'sports', 'arts', 'volunteer', 'technology', 'other')
                LIMIT 10
            """))

            problematic_records = result.fetchall()
            print(f"找到 {len(problematic_records)} 条有问题的club_type记录:")

            for record in problematic_records:
                print(f"  ID: {record[0]}, Title: {record[1]}, Club Type: {repr(record[2])}")

            # 修复club_type字段
            if problematic_records:
                print("\n2. 修复club_type字段...")
                result = db.session.execute(db.text("""
                    UPDATE school_calendar
                    SET club_type = NULL
                    WHERE club_type IS NOT NULL
                    AND club_type NOT IN ('academic', 'sports', 'arts', 'volunteer', 'technology', 'other')
                """))
                print(f"修复了 {result.rowcount} 条记录")

            # 检查其他可能的问题字段
            print("\n3. 检查event_type字段...")
            result = db.session.execute(db.text("""
                SELECT id, title, event_type
                FROM school_calendar
                WHERE event_type NOT IN ('anniversary', 'festival', 'activity', 'club', 'holiday', 'exam', 'meeting')
                LIMIT 5
            """))

            event_type_issues = result.fetchall()
            if event_type_issues:
                print(f"找到 {len(event_type_issues)} 条有问题的event_type记录:")
                for record in event_type_issues:
                    print(f"  ID: {record[0]}, Title: {record[1]}, Event Type: {repr(record[2])}")

            # 检查status字段
            print("\n4. 检查status字段...")
            result = db.session.execute(db.text("""
                SELECT id, title, status
                FROM school_calendar
                WHERE status NOT IN ('draft', 'published', 'cancelled', 'completed')
                LIMIT 5
            """))

            status_issues = result.fetchall()
            if status_issues:
                print(f"找到 {len(status_issues)} 条有问题的status记录:")
                for record in status_issues:
                    print(f"  ID: {record[0]}, Title: {record[1]}, Status: {repr(record[2])}")

            # 提交更改
            print("\n5. 提交更改...")
            db.session.commit()
            print("✅ 数据库修复完成!")

            # 测试修复后的查询
            print("\n6. 测试修复后的查询...")
            result = db.session.execute(db.text("""
                SELECT COUNT(*) as total
                FROM school_calendar
                WHERE status = 'published'
            """))

            count = result.fetchone()[0]
            print(f"✅ 成功查询到 {count} 个已发布事件")

            # 测试前5条记录
            result = db.session.execute(db.text("""
                SELECT id, title, event_type, status
                FROM school_calendar
                WHERE status = 'published'
                ORDER BY start_date ASC
                LIMIT 5
            """))

            events = result.fetchall()
            print(f"✅ 前5个已发布事件:")
            for event in events:
                print(f"  - {event[1]} ({event[2]})")

            return True

        except Exception as e:
            print(f"修复失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = fix_invalid_enum_with_sql()
    if success:
        print("\n校历数据修复成功!")
    else:
        print("\n修复失败!")
        sys.exit(1)