#!/usr/bin/env python3
"""
修复校历表中的无效枚举值
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.school_calendar import SchoolCalendar

def fix_invalid_enum_values():
    """修复无效的枚举值"""
    app = create_app()

    with app.app_context():
        print("=== 修复校历表中的无效枚举值 ===")

        try:
            # 查找所有校历事件
            events = SchoolCalendar.query.all()
            print(f"总共找到 {len(events)} 个校历事件")

            invalid_events = []
            fixed_count = 0

            for event in events:
                needs_fix = False
                fixes = []

                # 检查 club_type 字段
                if event.club_type:
                    valid_types = ['academic', 'sports', 'arts', 'volunteer', 'technology', 'other']
                    if event.club_type not in valid_types:
                        fixes.append(f"club_type: {event.club_type} -> None")
                        event.club_type = None
                        needs_fix = True

                # 检查其他枚举字段
                if needs_fix:
                    invalid_events.append({
                        'id': event.id,
                        'title': event.title,
                        'fixes': fixes
                    })
                    fixed_count += 1

            # 显示发现的问题
            if invalid_events:
                print(f"\n发现 {len(invalid_events)} 个需要修复的事件:")
                for event_info in invalid_events[:5]:  # 只显示前5个
                    print(f"  ID {event_info['id']}: {event_info['title']}")
                    for fix in event_info['fixes']:
                        print(f"    - {fix}")

                if len(invalid_events) > 5:
                    print(f"  ... 还有 {len(invalid_events) - 5} 个事件")

                # 提交修复
                print(f"\n正在修复 {fixed_count} 个事件...")
                db.session.commit()
                print(f"✅ 成功修复了 {fixed_count} 个事件!")
            else:
                print("✅ 没有发现无效的枚举值")

            # 测试修复后的查询
            print("\n=== 测试修复后的查询 ===")
            query = SchoolCalendar.query.filter_by(status='published')
            query = query.order_by(SchoolCalendar.start_date.asc())
            pagination = query.paginate(page=1, per_page=5, error_out=False)

            print(f"查询成功: {pagination.total} 个已发布事件")

            # 测试to_dict方法
            for event in pagination.items:
                try:
                    event_dict = event.to_dict()
                    print(f"✅ 事件: {event_dict['title']} - {event_dict['event_type']}")
                except Exception as e:
                    print(f"❌ 事件 {event.id} to_dict 失败: {str(e)}")
                    return False

            print("✅ 所有测试通过!")
            return True

        except Exception as e:
            print(f"❌ 修复失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = fix_invalid_enum_values()
    if success:
        print("\n🎉 校历枚举值修复完成!")
    else:
        print("\n❌ 修复失败!")
        sys.exit(1)