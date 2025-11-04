#!/usr/bin/env python3
"""
简单测试脚本：验证用户创建API功能
"""

import requests
import json

def test_user_api():
    """测试用户创建API"""
    base_url = "http://localhost:5000"

    print("🔧 测试用户创建API功能...")

    # 首先测试登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        print("📍 测试管理员登录...")
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)

        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print("✅ 管理员登录成功")

            # 测试用户创建API
            print("📍 测试用户创建API...")
            user_data = {
                "username": "testuser_v26",
                "password": "testpass123",
                "real_name": "测试用户v26",
                "email": "testv26@example.com",
                "phone": "13800138000",
                "user_type": "teacher"
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            create_response = requests.post(f"{base_url}/api/admin/users", json=user_data, headers=headers)

            if create_response.status_code == 201:
                print("✅ 用户创建API工作正常")
                print(f"📍 响应: {create_response.json()}")
                return True
            else:
                print(f"❌ 用户创建失败: {create_response.status_code}")
                print(f"📍 错误响应: {create_response.text}")
                return False

        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"📍 响应: {login_response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    print("=== 用户创建功能验证测试 v2.6 ===")
    print("修复内容: 将用户管理方法从 AlumniApprovePage 移动到 UsersPage")
    print()

    success = test_user_api()

    print()
    if success:
        print("🎉 后端API测试通过！")
        print("📝 现在可以测试前端管理界面:")
        print("   1. 访问 http://localhost:5000/admin-login")
        print("   2. 登录后进入用户管理页面")
        print("   3. 点击'添加用户'按钮")
        print("   4. 填写用户信息并创建")
        print("   5. 应该能看到调试日志和成功消息")
    else:
        print("❌ 后端API测试失败")
        print("📝 请检查服务器是否正常运行")

if __name__ == "__main__":
    main()