"""
测试用户列表改进和可拜访状态功能 - 简化版
"""

import requests

def test_user_improvements():
    """测试用户列表改进和可拜访状态功能"""

    # 登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        login_response = requests.post("http://127.0.0.1:5000/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print("Login failed")
            return False

        token = login_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}

        print("=== 测试用户管理改进功能 ===")

        # 测试1: 创建一个教师用户
        print("\n1. 创建教师用户测试")
        teacher_data = {
            "username": "test_teacher_auto",
            "real_name": "测试教师",
            "email": "teacher_auto@test.com",
            "phone": "13800138888",
            "password": "test123456",
            "user_type": "teacher",
            "status": "active",
            "employee_id": "T8888"
        }

        create_response = requests.post("http://127.0.0.1:5000/api/admin/users", headers=headers, json=teacher_data)
        if create_response.status_code == 200:
            teacher_user = create_response.json()['user']
            print(f"教师用户创建成功: {teacher_user['real_name']}")
            print(f"用户类型: {teacher_user['user_type']}")
            print(f"可拜访状态: {teacher_user['is_visitable']}")

            if teacher_user['is_visitable']:
                print("成功: 教师自动设置为可拜访")
            else:
                print("失败: 教师未自动设置为可拜访")
        else:
            print(f"失败: 创建教师用户失败: {create_response.status_code}")

        # 测试2: 创建一个多身份用户（包含教师）
        print("\n2. 创建多身份用户测试")
        multi_user_data = {
            "username": "test_multi_user",
            "real_name": "多身份用户",
            "email": "multi@test.com",
            "phone": "13800138889",
            "password": "test123456",
            "user_type": "teacher,alumni",
            "status": "active",
            "employee_id": "T9999"
        }

        create_response2 = requests.post("http://127.0.0.1:5000/api/admin/users", headers=headers, json=multi_user_data)
        if create_response2.status_code == 200:
            multi_user = create_response2.json()['user']
            print(f"多身份用户创建成功: {multi_user['real_name']}")
            print(f"用户类型: {multi_user['user_type']}")
            print(f"可拜访状态: {multi_user['is_visitable']}")

            if multi_user['is_visitable']:
                print("成功: 包含教师身份的用户自动设置为可拜访")
            else:
                print("失败: 包含教师身份的用户未自动设置为可拜访")
        else:
            print(f"失败: 创建多身份用户失败: {create_response2.status_code}")

        # 测试3: 创建非教师用户
        print("\n3. 创建非教师用户测试")
        student_data = {
            "username": "test_student_only",
            "real_name": "纯学生用户",
            "email": "student@test.com",
            "phone": "13800138890",
            "password": "test123456",
            "user_type": "student",
            "status": "active",
            "student_id": "S2024001"
        }

        create_response3 = requests.post("http://127.0.0.1:5000/api/admin/users", headers=headers, json=student_data)
        if create_response3.status_code == 200:
            student_user = create_response3.json()['user']
            print(f"学生用户创建成功: {student_user['real_name']}")
            print(f"用户类型: {student_user['user_type']}")
            print(f"可拜访状态: {student_user['is_visitable']}")

            if not student_user['is_visitable']:
                print("成功: 非教师用户默认为不可拜访")
            else:
                print("失败: 非教师用户被错误设置为可拜访")
        else:
            print(f"失败: 创建学生用户失败: {create_response3.status_code}")

        print("\n=== 测试完成 ===")
        return True

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    test_user_improvements()