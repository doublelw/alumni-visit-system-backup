"""
调试用户创建API
"""

import requests
import json

def debug_user_creation():
    """调试用户创建API"""

    # 登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        login_response = requests.post("http://127.0.0.1:5000/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            print(login_response.text)
            return False

        token = login_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}

        print("=== 调试用户创建API ===")

        # 测试1: 创建一个教师用户
        print("\n1. 创建教师用户测试")
        teacher_data = {
            "username": "test_teacher_debug",
            "real_name": "测试教师",
            "email": "teacher_debug@test.com",
            "phone": "13800138888",
            "password": "test123456",
            "user_type": "teacher",
            "status": "active",
            "employee_id": "T8889"
        }

        print(f"发送数据: {json.dumps(teacher_data, indent=2, ensure_ascii=False)}")

        create_response = requests.post("http://127.0.0.1:5000/api/admin/users", headers=headers, json=teacher_data)
        print(f"响应状态码: {create_response.status_code}")
        print(f"响应内容: {create_response.text}")

        if create_response.status_code == 200:
            teacher_user = create_response.json()['user']
            print(f"教师用户创建成功: {teacher_user['real_name']}")
            print(f"用户类型: {teacher_user['user_type']}")
            print(f"可拜访状态: {teacher_user['is_visitable']}")
        else:
            print("创建失败，检查错误信息")

        return True

    except Exception as e:
        print(f"调试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    debug_user_creation()