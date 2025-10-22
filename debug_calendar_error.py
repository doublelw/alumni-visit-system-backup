#!/usr/bin/env python3
"""
调试Calendar API 500错误 - 模拟前端请求
"""

import sys
import os
import requests
import json
import traceback
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from flask_jwt_extended import create_access_token

def test_calendar_with_debug():
    """详细测试Calendar API并记录所有信息"""
    app = create_app()

    with app.app_context():
        print("=== 详细调试Calendar API 500错误 ===")
        print(f"时间: {datetime.now()}")

        # 1. 获取admin token
        print("\n1. 获取admin token...")
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found")
            return False

        token = create_access_token(identity=admin_user.id)
        print(f"✅ 获得token: {token[:50]}...")

        # 2. 测试不同的参数组合
        test_cases = [
            {
                'name': '基本查询',
                'params': {
                    'status': 'published',
                    'per_page': '5',
                    'sort_by': 'start_date',
                    'order': 'asc'
                }
            },
            {
                'name': '无参数查询',
                'params': {}
            },
            {
                'name': '只有状态参数',
                'params': {
                    'status': 'published'
                }
            },
            {
                'name': '小分页',
                'params': {
                    'status': 'published',
                    'per_page': '1'
                }
            }
        ]

        base_url = 'https://127.0.0.1:5000/api/calendar/events'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. 测试用例: {test_case['name']}")
            print(f"   参数: {test_case['params']}")

            # 构建URL
            if test_case['params']:
                query_string = '&'.join([f'{k}={v}' for k, v in test_case['params'].items()])
                url = f"{base_url}?{query_string}"
            else:
                url = base_url

            print(f"   URL: {url}")

            try:
                # 发送请求
                print("   发送请求...")
                response = requests.get(url, headers=headers, verify=False, timeout=30)

                print(f"   状态码: {response.status_code}")
                print(f"   响应头: {dict(response.headers)}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ 成功! 返回 {len(data.get('events', []))} 个事件")
                    if data.get('events'):
                        print(f"   第一个事件: {data['events'][0].get('title', 'N/A')}")
                else:
                    print(f"   ❌ 失败!")
                    print(f"   响应内容: {response.text[:500]}")

                    # 尝试解析错误信息
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            print(f"   错误信息: {error_data['error']}")
                        if 'message' in error_data:
                            print(f"   消息: {error_data['message']}")
                    except:
                        print("   无法解析JSON错误响应")

            except requests.exceptions.SSLError as e:
                print(f"   ❌ SSL错误: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                print(f"   ❌ 连接错误: {str(e)}")
            except requests.exceptions.Timeout as e:
                print(f"   ❌ 超时错误: {str(e)}")
            except Exception as e:
                print(f"   ❌ 其他错误: {str(e)}")
                traceback.print_exc()

        # 3. 直接测试API逻辑
        print(f"\n{len(test_cases)+1}. 直接测试API逻辑...")
        try:
            from app.models.school_calendar import SchoolCalendar

            # 使用相同的查询参数
            query = SchoolCalendar.query.filter_by(status='published')
            query = query.order_by(SchoolCalendar.start_date.asc())
            pagination = query.paginate(page=1, per_page=5, error_out=False)

            print(f"   ✅ 直接查询成功: {pagination.total} 条记录")

            # 测试每个事件的to_dict方法
            success_count = 0
            for i, event in enumerate(pagination.items):
                try:
                    event_dict = event.to_dict()
                    success_count += 1
                    if i < 3:  # 只显示前3个
                        print(f"   ✅ 事件 {i+1}: {event_dict.get('title', 'N/A')}")
                except Exception as e:
                    print(f"   ❌ 事件 {event.id} to_dict失败: {str(e)}")
                    if i < 3:
                        traceback.print_exc()

            print(f"   成功转换: {success_count}/{len(pagination.items)}")

        except Exception as e:
            print(f"   ❌ 直接测试失败: {str(e)}")
            traceback.print_exc()

        return True

def check_database_state():
    """检查数据库状态"""
    app = create_app()

    with app.app_context():
        print("\n=== 检查数据库状态 ===")

        try:
            from app.models.school_calendar import SchoolCalendar

            # 检查总数
            total_count = SchoolCalendar.query.count()
            print(f"校历事件总数: {total_count}")

            # 检查已发布数量
            published_count = SchoolCalendar.query.filter_by(status='published').count()
            print(f"已发布事件数量: {published_count}")

            # 检查数据完整性
            print("\n检查数据完整性...")
            events = SchoolCalendar.query.limit(5).all()
            for event in events:
                print(f"  ID: {event.id}, Title: {event.title}, Status: {event.status}, Type: {event.event_type}")

                # 检查关键字段
                if not hasattr(event, 'event_type') or event.event_type is None:
                    print(f"    ⚠️ 缺少event_type字段")
                if not hasattr(event, 'status') or event.status is None:
                    print(f"    ⚠️ 缺少status字段")

        except Exception as e:
            print(f"❌ 数据库检查失败: {str(e)}")
            traceback.print_exc()

if __name__ == '__main__':
    print("开始详细调试Calendar API...")

    # 检查数据库状态
    check_database_state()

    # 测试API
    success = test_calendar_with_debug()

    print("\n=== 调试完成 ===")
    print("如果看到这个消息，说明调试脚本运行完成")
    print("请检查上面的输出以找出问题所在")