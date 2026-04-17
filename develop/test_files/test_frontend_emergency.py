#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端注册表单中紧急联系人字段是否为可选
"""

import requests
import json
import random

def generate_valid_id_card():
    """生成有效的身份证号"""
    # 地区代码
    area_code = "110101"  # 北京市东城区

    # 出生日期
    birth_year = random.randint(1970, 2000)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    birth_date = f"{birth_year:02d}{birth_month:02d}{birth_day:02d}"

    # 顺序码
    sequence = random.randint(1, 999)
    sequence_str = f"{sequence:03d}"

    # 前17位
    id_17 = area_code + birth_date + sequence_str

    # 计算校验码
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    checksums = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    sum_val = 0
    for i in range(17):
        sum_val += int(id_17[i]) * weights[i]

    checksum = checksums[sum_val % 11]

    return id_17 + checksum

def test_frontend_emergency_fields():
    """测试前端紧急联系人字段是否可选"""
    print("测试前端注册表单中紧急联系人字段...")

    # 测试数据1: 不填写任何紧急联系人信息
    test_data_1 = {
        "username": "test_frontend_1",
        "password": "Test123456",
        "confirmPassword": "Test123456",
        "realName": "测试用户1",
        "email": "testfrontend1@example.com",
        "phone": "13888888881",
        "idCard": generate_valid_id_card(),
        "graduationYear": "2010",
        "classNumber": "高三(1)班",
        "department": "教务处",
        "major": "理科",
        "classTeacher": "张老师",
        "currentCity": "北京市",
        "workUnit": "某科技公司",
        "position": "工程师",
        # 紧急联系人字段为空
        "emergencyContact": "",
        "emergencyPhone": "",
        "agreeTerms": True
    }

    # 测试数据2: 只填写紧急联系人姓名，不填写电话
    test_data_2 = {
        "username": "test_frontend_2",
        "password": "Test123456",
        "confirmPassword": "Test123456",
        "realName": "测试用户2",
        "email": "testfrontend2@example.com",
        "phone": "13888888882",
        "idCard": generate_valid_id_card(),
        "graduationYear": "2011",
        "classNumber": "高三(2)班",
        "department": "教务处",
        "major": "文科",
        "classTeacher": "李老师",
        "currentCity": "上海市",
        "workUnit": "某互联网公司",
        "position": "产品经理",
        # 只填写紧急联系人姓名
        "emergencyContact": "张三",
        "emergencyPhone": "",
        "agreeTerms": True
    }

    # 测试数据3: 填写完整的紧急联系人信息
    test_data_3 = {
        "username": "test_frontend_3",
        "password": "Test123456",
        "confirmPassword": "Test123456",
        "realName": "测试用户3",
        "email": "testfrontend3@example.com",
        "phone": "13888888883",
        "idCard": generate_valid_id_card(),
        "graduationYear": "2012",
        "classNumber": "高三(3)班",
        "department": "教务处",
        "major": "理科",
        "classTeacher": "王老师",
        "currentCity": "深圳市",
        "workUnit": "某金融公司",
        "position": "数据分析师",
        # 填写完整紧急联系人信息
        "emergencyContact": "李四",
        "emergencyPhone": "13999999999",
        "agreeTerms": True
    }

    success_count = 0
    total_tests = 3

    # 测试1: 不填写任何紧急联系人信息
    print("\n测试1: 不填写任何紧急联系人信息")
    try:
        response = requests.post(
            'http://127.0.0.1:5001/api/auth/register',
            json=test_data_1,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 201:
            print("✅ 成功！可以不填写紧急联系人信息")
            success_count += 1
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求错误: {e}")

    # 测试2: 只填写紧急联系人姓名
    print("\n测试2: 只填写紧急联系人姓名")
    try:
        response = requests.post(
            'http://127.0.0.1:5001/api/auth/register',
            json=test_data_2,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 201:
            print("✅ 成功！可以只填写紧急联系人姓名")
            success_count += 1
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求错误: {e}")

    # 测试3: 填写完整紧急联系人信息
    print("\n测试3: 填写完整紧急联系人信息")
    try:
        response = requests.post(
            'http://127.0.0.1:5001/api/auth/register',
            json=test_data_3,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 201:
            print("✅ 成功！可以填写完整紧急联系人信息")
            success_count += 1
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求错误: {e}")

    print(f"\n测试结果: {success_count}/{total_tests} 通过")
    if success_count == total_tests:
        print("🎉 所有测试通过！紧急联系人字段已成功设置为可选。")
        return True
    else:
        print("⚠️ 部分测试失败，需要检查实现。")
        return False

if __name__ == "__main__":
    print("开始测试前端紧急联系人字段...")
    print("=" * 50)

    test_frontend_emergency_fields()