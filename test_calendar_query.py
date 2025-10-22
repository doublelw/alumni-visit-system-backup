#!/usr/bin/env python3
"""
测试校历查询
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.school_calendar import SchoolCalendar

def test_calendar_query():
    """测试校历查询"""
    app = create_app()

    with app.app_context():
        print("正在测试校历查询...")

        try:
            # 测试基本查询
            events = SchoolCalendar.query.limit(5).all()
            print(f"查询到 {len(events)} 个事件")

            # 测试to_dict方法
            for i, event in enumerate(events):
                try:
                    event_dict = event.to_dict()
                    print(f"事件 {i+1}: {event_dict['title']} - {event_dict['event_type']}")
                except Exception as e:
                    print(f"事件 {i+1} to_dict 失败: {str(e)}")
                    print(f"事件ID: {event.id}, creator_id: {event.created_by}")
                    # 尝试访问creator
                    try:
                        creator = event.creator
                        print(f"Creator: {creator}")
                    except Exception as ce:
                        print(f"访问creator失败: {str(ce)}")

            # 测试分页查询
            pagination = SchoolCalendar.query.paginate(page=1, per_page=5, error_out=False)
            print(f"分页查询: {pagination.total} 总记录, {pagination.pages} 页")

            # 测试状态过滤
            published_events = SchoolCalendar.query.filter_by(status='published').limit(5).all()
            print(f"已发布事件: {len(published_events)} 个")

            print("校历查询测试成功！")
            return True

        except Exception as e:
            print(f"校历查询测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_calendar_query()
    if success:
        print("校历查询正常")
    else:
        print("校历查询有问题")
        sys.exit(1)