#!/usr/bin/env python3
"""
测试HTTP连接而不是HTTPS
"""

import sys
import os
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from flask_jwt_extended import create_access_token

def test_http_vs_https():
    """测试HTTP与HTTPS连接的差异"""
    app = create_app()

    with app.app_context():
        print("=== 测试HTTP与HTTPS连接差异 ===")

        # 获取admin token
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found")
            return False

        token = create_access_token(identity=admin_user.id)
        print(f"Got token: {token[:50]}...")

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # 测试HTTPS (当前失败的)
        print("\n1. 测试HTTPS连接:")
        https_url = 'https://127.0.0.1:5000/api/calendar/events?status=published&per_page=5'

        try:
            response = requests.get(https_url, headers=headers, verify=False, timeout=10)
            print(f"   HTTPS状态码: {response.status_code}")
            if response.status_code == 200:
                print("   HTTPS连接成功!")
                return True
            else:
                print(f"   HTTPS失败: {response.text[:100]}...")
        except Exception as e:
            print(f"   HTTPS连接失败: {str(e)}")

        # 测试HTTP
        print("\n2. 测试HTTP连接:")
        http_url = 'http://127.0.0.1:5000/api/calendar/events?status=published&per_page=5'

        try:
            response = requests.get(http_url, headers=headers, timeout=10)
            print(f"   HTTP状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   HTTP连接成功! 返回 {len(data.get('events', []))} 个事件")
                return True
            else:
                print(f"   HTTP失败: {response.text[:100]}...")
        except Exception as e:
            print(f"   HTTP连接失败: {str(e)}")

        return False

def check_flask_server_config():
    """检查Flask服务器配置"""
    print("\n=== 检查Flask服务器配置 ===")

    try:
        app = create_app()
        with app.app_context():
            # 检查服务器配置
            print(f"Debug模式: {app.debug}")
            print(f"Secret Key设置: {'Yes' if app.secret_key else 'No'}")

            # 检查SSL配置
            print("检查SSL证书配置...")

            # 检查路由
            print("已注册的路由:")
            for rule in app.url_map.iter_rules():
                if 'calendar' in rule.rule:
                    print(f"  {rule.methods} {rule.rule} -> {rule.endpoint}")

            return True

    except Exception as e:
        print(f"检查配置失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("开始测试HTTP/HTTPS连接...")

    # 检查Flask配置
    check_flask_server_config()

    # 测试连接差异
    connection_ok = test_http_vs_https()

    if connection_ok:
        print("\n解决方案: 找到可用的连接方式")
    else:
        print("\n需要进一步调试Flask服务器配置")