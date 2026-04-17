#!/usr/bin/env python3
"""
测试校历模型
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.school_calendar import SchoolCalendar

def test_calendar_model():
    """测试校历模型"""
    app = create_app()

    with app.app_context():
        print("正在测试校历模型...")

        try:
            # 尝试查询校历事件
            count = SchoolCalendar.query.count()
            print(f"校历事件总数: {count}")

            # 尝试创建一个测试事件
            test_event = SchoolCalendar(
                title="测试事件",
                description="这是一个测试事件",
                event_type="activity",
                start_date="2025-10-16",
                created_by=1  # 使用admin用户ID
            )

            print("校历模型测试成功！")
            return True

        except Exception as e:
            print(f"校历模型测试失败: {str(e)}")
            return False

if __name__ == '__main__':
    success = test_calendar_model()
    if success:
        print("✅ 校历模型正常")
    else:
        print("❌ 校历模型有问题")
        sys.exit(1)