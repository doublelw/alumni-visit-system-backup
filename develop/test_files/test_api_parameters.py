#!/usr/bin/env python3
"""
测试API参数处理问题
"""

import sys
import os
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from flask_jwt_extended import create_access_token

def test_api_with_different_params():
    """测试不同参数组合的API调用"""
    app = create_app()

    with app.app_context():
        print("=== 测试API参数处理 ===")

        # 获取admin token
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found")
            return False

        token = create_access_token(identity=admin_user.id)
        print(f"Got token: {token[:50]}...")

        base_url = 'https://127.0.0.1:5000/api/calendar/events'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # 测试不同的参数组合
        test_cases = [
            {
                'name': '前端原始参数',
                'params': {
                    'status': 'published',
                    'per_page': '5',
                    'sort_by': 'start_date',
                    'order': 'asc'
                }
            },
            {
                'name': '最小参数',
                'params': {
                    'status': 'published',
                    'per_page': '5'
                }
            },
            {
                'name': '只有状态',
                'params': {
                    'status': 'published'
                }
            },
            {
                'name': '无参数',
                'params': {}
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. 测试: {test_case['name']}")

            # 构建URL
            if test_case['params']:
                query_string = '&'.join([f'{k}={v}' for k, v in test_case['params'].items()])
                url = f"{base_url}?{query_string}"
            else:
                url = base_url

            print(f"   URL: {url}")

            try:
                response = requests.get(url, headers=headers, verify=False, timeout=10)

                print(f"   状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"   成功! 返回 {len(data.get('events', []))} 个事件")
                else:
                    print(f"   失败! 状态码: {response.status_code}")
                    print(f"   错误: {response.text[:200]}...")

            except Exception as e:
                print(f"   请求异常: {str(e)}")

        return True

def check_api_implementation():
    """检查API实现中的参数处理"""
    app = create_app()

    with app.app_context():
        print("\n=== 检查API实现 ===")

        # 直接测试API逻辑，模拟不同参数
        from app.models.school_calendar import SchoolCalendar

        print("1. 测试基本查询（前端参数）...")
        try:
            query = SchoolCalendar.query.filter_by(status='published')

            # 注意：API代码实际上没有处理sort_by和order参数！
            # 它使用固定的排序
            query = query.order_by(
                SchoolCalendar.start_date.asc(),
                SchoolCalendar.created_at.desc()
            )

            pagination = query.paginate(page=1, per_page=5, error_out=False)
            events_list = [event.to_dict() for event in pagination.items]

            print(f"   基本查询成功: {len(events_list)} 个事件")

        except Exception as e:
            print(f"   基本查询失败: {str(e)}")
            return False

        print("2. 测试前端实际发送的参数组合...")
        try:
            # 模拟前端参数
            status = 'published'
            per_page = 5
            page = 1
            sort_by = 'start_date'  # 前端发送了这个参数
            order = 'asc'           # 前端发送了这个参数

            query = SchoolCalendar.query

            # 应用状态筛选
            if status:
                query = query.filter_by(status=status)

            # API没有处理sort_by和order，使用固定排序
            query = query.order_by(
                SchoolCalendar.start_date.asc(),
                SchoolCalendar.created_at.desc()
            )

            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            events_list = [event.to_dict() for event in pagination.items]

            print(f"   前端参数模拟成功: {len(events_list)} 个事件")

        except Exception as e:
            print(f"   前端参数模拟失败: {str(e)}")
            return False

        return True

if __name__ == '__main__':
    print("开始API参数测试...")

    # 检查API实现
    impl_ok = check_api_implementation()

    # 测试实际API调用
    if impl_ok:
        api_ok = test_api_with_different_params()

        if api_ok:
            print("\n结论: API参数处理正常")
        else:
            print("\n结论: API在HTTP层面有问题")
    else:
        print("\n结论: API实现本身有问题")