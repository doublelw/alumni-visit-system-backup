#!/usr/bin/env python3
"""
测试Calendar API数据 - 简化版本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.school_calendar import SchoolCalendar

def test_calendar_api_logic():
    """测试Calendar API逻辑"""
    app = create_app()

    with app.app_context():
        print("=== 测试Calendar API逻辑 ===")

        try:
            # 模拟API查询
            print("1. 执行数据库查询...")
            query = SchoolCalendar.query.filter_by(status='published')
            query = query.order_by(SchoolCalendar.start_date.asc())
            pagination = query.paginate(page=1, per_page=5, error_out=False)

            print(f"   查询成功: {pagination.total} 条记录")
            print(f"   当前页记录数: {len(pagination.items)}")

            # 测试每个记录的to_dict方法
            print("2. 测试记录转换...")
            events_list = []
            error_count = 0

            for i, event in enumerate(pagination.items):
                try:
                    event_dict = event.to_dict()
                    events_list.append(event_dict)
                    print(f"   记录 {i+1}: {event_dict['title'][:30]}... OK")
                except Exception as e:
                    error_count += 1
                    print(f"   记录 {i+1} (ID: {event.id}) FAILED: {str(e)}")
                    print(f"   Title: {event.title}")
                    print(f"   Event Type: {getattr(event, 'event_type', 'N/A')}")
                    print(f"   Status: {getattr(event, 'status', 'N/A')}")
                    print(f"   Start Date: {getattr(event, 'start_date', 'N/A')}")
                    print(f"   Club Type: {getattr(event, 'club_type', 'N/A')}")

            if error_count > 0:
                print(f"   发现 {error_count} 个问题记录!")
                return False
            else:
                print(f"   所有记录转换成功!")

            # 构建API响应
            print("3. 构建API响应...")
            response_data = {
                'events': events_list,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }

            print(f"   API响应构建成功: {len(response_data['events'])} 个事件")
            return True

        except Exception as e:
            print(f"API测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def check_problematic_records():
    """检查有问题的记录"""
    app = create_app()

    with app.app_context():
        print("\n=== 检查有问题的记录 ===")

        try:
            # 查询前10个记录并逐个测试
            events = SchoolCalendar.query.filter_by(status='published').limit(10).all()
            print(f"检查前 {len(events)} 个记录...")

            problem_count = 0
            for event in events:
                try:
                    event_dict = event.to_dict()
                    print(f"ID {event.id}: {event.title[:30]}... OK")
                except Exception as e:
                    problem_count += 1
                    print(f"ID {event.id}: {event.title[:30]}... ERROR - {str(e)}")

                    # 显示详细字段信息
                    print(f"  详细信息:")
                    print(f"    event_type: {repr(getattr(event, 'event_type', 'MISSING'))}")
                    print(f"    status: {repr(getattr(event, 'status', 'MISSING'))}")
                    print(f"    club_type: {repr(getattr(event, 'club_type', 'MISSING'))}")

            if problem_count == 0:
                print("前10个记录都没有问题")
            else:
                print(f"发现 {problem_count} 个问题记录")

            return problem_count == 0

        except Exception as e:
            print(f"检查失败: {str(e)}")
            return False

if __name__ == '__main__':
    print("开始Calendar API数据测试...")

    # 检查前10个记录
    first_check = check_problematic_records()

    # 完整API测试
    if first_check:
        api_test = test_calendar_api_logic()

        if api_test:
            print("\n结论: Calendar API逻辑正常工作")
            print("500错误可能来自HTTP层面的其他问题")
        else:
            print("\n结论: 发现数据问题，这就是500错误的原因")
    else:
        print("\n结论: 前10个记录中就有问题，需要立即修复")