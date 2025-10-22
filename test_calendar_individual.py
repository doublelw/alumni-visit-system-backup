#!/usr/bin/env python3
"""
测试Calendar API逐个记录以找出问题数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.school_calendar import SchoolCalendar

def test_individual_records():
    """逐个测试校历记录的to_dict方法"""
    app = create_app()

    with app.app_context():
        print("=== 逐个测试校历记录 ===")

        # 获取所有已发布的事件
        events = SchoolCalendar.query.filter_by(status='published').order_by(SchoolCalendar.start_date.asc()).all()
        print(f"总共 {len(events)} 个已发布事件")

        problem_records = []
        success_count = 0

        for i, event in enumerate(events):
            try:
                event_dict = event.to_dict()
                success_count += 1

                # 每10个记录显示一次进度
                if (i + 1) % 10 == 0:
                    print(f"已测试 {i + 1}/{len(events)} 个记录...")

                # 只显示前几个成功记录的详情
                if i < 3:
                    print(f"✅ 记录 {i+1}: {event.title[:30]}...")

            except Exception as e:
                print(f"❌ 记录 {i+1} (ID: {event.id}) 失败: {str(e)}")
                problem_records.append({
                    'id': event.id,
                    'title': event.title,
                    'error': str(e)
                })

                # 如果找到问题记录，显示详细信息
                print(f"   问题记录详情:")
                print(f"   ID: {event.id}")
                print(f"   Title: {event.title}")
                print(f"   Event Type: {getattr(event, 'event_type', 'N/A')}")
                print(f"   Status: {getattr(event, 'status', 'N/A')}")
                print(f"   Start Date: {getattr(event, 'start_date', 'N/A')}")
                print(f"   Club Type: {getattr(event, 'club_type', 'N/A')}")

                # 限制显示的问题记录数量
                if len(problem_records) >= 5:
                    print(f"   ... 已找到5个问题记录，停止测试")
                    break

        print(f"\n=== 测试结果 ===")
        print(f"成功记录: {success_count}")
        print(f"问题记录: {len(problem_records)}")

        if problem_records:
            print(f"\n问题记录列表:")
            for record in problem_records:
                print(f"  ID {record['id']}: {record['title'][:30]}... - {record['error']}")
        else:
            print("✅ 所有记录都成功转换!")

        return len(problem_records) == 0

def test_api_with_problem_data():
    """测试API在遇到问题数据时的行为"""
    app = create_app()

    with app.app_context():
        print("\n=== 模拟API调用测试 ===")

        try:
            # 模拟API查询逻辑
            page = 1
            per_page = 5

            query = SchoolCalendar.query.filter_by(status='published')
            query = query.order_by(SchoolCalendar.start_date.asc())

            print("执行分页查询...")
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            print(f"查询成功: {pagination.total} 条记录")
            print(f"当前页: {len(pagination.items)} 条记录")

            # 尝试构建API响应
            events_list = []
            for i, event in enumerate(pagination.items):
                try:
                    event_dict = event.to_dict()
                    events_list.append(event_dict)
                    print(f"✅ 记录 {i+1}: {event_dict['title'][:30]}...")
                except Exception as e:
                    print(f"❌ 记录 {i+1} (ID: {event.id}) to_dict失败: {str(e)}")
                    # 这就是导致API 500错误的原因！
                    return False

            # 构建完整的API响应
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

            print(f"✅ API响应构建成功: {len(response_data['events'])} 个事件")
            return True

        except Exception as e:
            print(f"❌ API测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("开始测试Calendar API数据完整性...")

    # 测试单个记录
    individual_ok = test_individual_records()

    # 测试API逻辑
    if individual_ok:
        api_ok = test_api_with_problem_data()

        if api_ok:
            print("\n✅ 所有测试通过! Calendar API应该可以正常工作。")
        else:
            print("\n❌ API测试失败，这就是500错误的原因!")
    else:
        print("\n❌ 发现问题记录，需要修复数据库数据。")
        print("建议运行之前的数据修复脚本。")