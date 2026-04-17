#!/usr/bin/env python3
"""
测试新的公开Calendar API
"""

import sys
import os
import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_new_public_api():
    """测试新的公开Calendar API"""
    print("=== 测试新的公开Calendar API ===")

    base_url = 'https://localhost:5000'

    # 测试新的公开API
    public_url = f"{base_url}/api/public/calendar/events?status=published&per_page=5"

    try:
        session = requests.Session()
        session.proxies = {}
        session.verify = False

        response = session.get(public_url, timeout=15)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"成功! 返回 {len(events)} 个事件")

            # 显示前两个事件
            for i, event in enumerate(events[:2]):
                print(f"  事件 {i+1}: {event['title'][:30]}...")

            return True
        else:
            print(f"失败: {response.status_code}")
            print(f"错误: {response.text[:200]}...")

    except Exception as e:
        print(f"请求异常: {str(e)}")
        return False

if __name__ == '__main__':
    print("开始测试新的公开Calendar API...")

    success = test_new_public_api()

    print("\n" + "="*60)
    print("测试结果:")
    print(f"公开API: {'✅ 成功' if success else '❌ 失败'}")

    if success:
        print("\n🎉 公开Calendar API现在可以正常工作!")
        print("前端应该可以正常加载活动数据了。")
    else:
        print("\n❌ 仍有问题需要解决。")