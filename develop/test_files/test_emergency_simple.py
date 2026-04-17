#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试注册流程中同行人信息删除功能
"""

import requests
import json

# 测试数据 - 不包含紧急联系人信息
test_data = {
    "username": "test_no_emergency",
    "password": "Test123456",
    "confirmPassword": "Test123456",
    "realName": "测试用户",
    "email": "testnoemergency@example.com",
    "phone": "13888888888",
    "idCard": "110101199001011234",
    "graduationYear": "2010",
    "classNumber": "高三(1)班",
    "department": "教务处",
    "major": "理科",
    "classTeacher": "张老师",
    "currentCity": "北京市",
    "workUnit": "某科技公司",
    "position": "工程师",
    # 不包含紧急联系人信息
    "emergencyContact": "",
    "emergencyPhone": "",
    "agreeTerms": True
}

def test_register_without_emergency():
    """测试不提供紧急联系人信息的注册"""
    print("测试不提供紧急联系人信息的注册...")

    try:
        response = requests.post(
            'http://127.0.0.1:5001/api/auth/register',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            print("注册成功！")
            print(f"   用户名: {result['user']['username']}")
            print(f"   用户ID: {result['user']['id']}")
            print(f"   状态: {result['user']['status']}")

            # 测试登录
            login_data = {
                "username": test_data["username"],
                "password": test_data["password"]
            }

            print("\n测试登录...")
            login_response = requests.post(
                'http://127.0.0.1:5001/api/auth/login',
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if login_response.status_code == 200:
                login_result = login_response.json()
                print("登录成功！")
                print(f"   获得token: {login_result['access_token'][:20]}...")
                return True
            else:
                print(f"登录失败: {login_response.status_code}")
                print(f"   错误信息: {login_response.text}")
                return False
        else:
            print(f"注册失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return False

def test_register_with_partial_emergency():
    """测试提供部分紧急联系人信息的注册"""
    print("\n测试提供部分紧急联系人信息的注册...")

    # 修改测试数据 - 只提供紧急联系人姓名，不提供电话
    partial_data = test_data.copy()
    partial_data["username"] = "test_partial_emergency"
    partial_data["email"] = "testpartial@example.com"
    partial_data["phone"] = "13777777777"
    partial_data["emergencyContact"] = "张三"
    partial_data["emergencyPhone"] = ""  # 留空电话号码

    try:
        response = requests.post(
            'http://127.0.0.1:5001/api/auth/register',
            json=partial_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 201:
            print("部分紧急联系人信息注册成功！")
            return True
        else:
            print(f"部分紧急联系人信息注册失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return False

def test_register_with_invalid_emergency_phone():
    """测试提供无效紧急联系人电话的注册"""
    print("\n测试提供无效紧急联系人电话的注册...")

    # 修改测试数据 - 提供无效的电话号码
    invalid_data = test_data.copy()
    invalid_data["username"] = "test_invalid_emergency"
    invalid_data["email"] = "testinvalid@example.com"
    invalid_data["phone"] = "13666666666"
    invalid_data["emergencyContact"] = "李四"
    invalid_data["emergencyPhone"] = "123"  # 无效电话号码

    try:
        response = requests.post(
            'http://127.0.0.1:5001/api/auth/register',
            json=invalid_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 400:
            print("正确拒绝了无效的紧急联系人电话！")
            result = response.json()
            print(f"   错误信息: {result.get('message', '未知错误')}")
            return True
        else:
            print(f"应该拒绝无效电话但却通过了: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return False

if __name__ == "__main__":
    print("开始测试同行人信息删除功能...")
    print("=" * 50)

    # 测试1: 不提供任何紧急联系人信息
    success1 = test_register_without_emergency()

    # 测试2: 提供部分紧急联系人信息
    success2 = test_register_with_partial_emergency()

    # 测试3: 提供无效紧急联系人电话
    success3 = test_register_with_invalid_emergency_phone()

    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"   测试1 (无紧急联系人): {'通过' if success1 else '失败'}")
    print(f"   测试2 (部分紧急联系人): {'通过' if success2 else '失败'}")
    print(f"   测试3 (无效电话验证): {'通过' if success3 else '失败'}")

    if all([success1, success2, success3]):
        print("\n所有测试通过！同行人信息已成功删除为选填项。")
    else:
        print("\n部分测试失败，需要检查实现。")