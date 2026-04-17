#!/usr/bin/env python3
"""
调试Calendar API - 模拟JavaScript请求
"""

import sys
import os
import requests
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from flask_jwt_extended import create_access_token

def test_calendar_api_like_js():
    """模拟JavaScript请求测试Calendar API"""
    app = create_app()

    with app.app_context():
        print("=== 模拟JavaScript Calendar API请求 ===")

        # 获取admin token
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found")
            return False

        token = create_access_token(identity=admin_user.id)
        print(f"Got admin token: {token[:50]}...")

        # 模拟JavaScript请求的参数
        params = {
            'status': 'published',
            'per_page': '5',
            'sort_by': 'start_date',
            'order': 'asc'
        }

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        url = 'https://127.0.0.1:5000/api/calendar/events'
        full_url = f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

        print(f"\n🌐 请求URL: {full_url}")
        print(f"📋 请求头: {json.dumps(headers, indent=2)}")

        try:
            print("\n📡 发送请求...")
            response = requests.get(full_url, headers=headers, verify=False)

            print(f"📊 响应状态码: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功! 响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                return True
            else:
                print(f"❌ 失败! 状态码: {response.status_code}")
                print(f"❌ 错误响应: {response.text}")
                return False

        except requests.exceptions.SSLError as e:
            print(f"🔒 SSL错误: {str(e)}")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 连接错误: {str(e)}")
            return False
        except Exception as e:
            print(f"💥 其他错误: {str(e)}")
            return False

def test_direct_api():
    """直接测试API逻辑"""
    app = create_app()

    with app.app_context():
        print("\n=== 直接测试API逻辑 ===")

        try:
            from app.models.school_calendar import SchoolCalendar

            # 模拟API中的查询逻辑
            query = SchoolCalendar.query

            # 应用筛选条件
            status = 'published'
            if status:
                query = query.filter_by(status=status)

            # 排序
            query = query.order_by(
                SchoolCalendar.start_date.asc(),
                SchoolCalendar.created_at.desc()
            )

            # 分页
            page = 1
            per_page = 5
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            print(f"✅ 查询成功: {pagination.total} 总记录, {pagination.pages} 页")

            # 测试to_dict方法
            events_list = []
            for i, event in enumerate(pagination.items):
                try:
                    event_dict = event.to_dict()
                    events_list.append(event_dict)
                    print(f"✅ 事件 {i+1}: {event_dict['title']} - {event_dict['event_type']}")
                except Exception as e:
                    print(f"❌ 事件 {i+1} to_dict失败: {str(e)}")
                    return False

            print(f"✅ 所有事件转换成功: {len(events_list)} 个")

            # 构建响应
            response_data = {
                'events': events_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }

            print(f"✅ 响应数据构建成功")
            return True

        except Exception as e:
            print(f"❌ 直接API测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("开始调试Calendar API...")

    # 先测试直接API逻辑
    direct_success = test_direct_api()

    # 再测试HTTP请求
    http_success = test_calendar_api_like_js()

    print(f"\n📋 测试结果:")
    print(f"   直接API逻辑: {'✅ 通过' if direct_success else '❌ 失败'}")
    print(f"   HTTP请求: {'✅ 通过' if http_success else '❌ 失败'}")

    if direct_success and not http_success:
        print(f"\n💡 结论: API逻辑正常，问题在于HTTP请求处理或网络连接")
    elif not direct_success:
        print(f"\n💡 结论: API逻辑本身有问题")
    else:
        print(f"\n🎉 结论: Calendar API完全正常!")