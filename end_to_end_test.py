#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import requests
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.visit_application import VisitApplication

BASE_URL = 'http://localhost:5000'

def get_token(username, password):
    """获取访问令牌"""
    response = requests.post(f"{BASE_URL}/api/auth/login",
                            json={'username': username, 'password': password})
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"登录失败: {response.text}")
        return None

def test_visit_application(visitor_token):
    """测试访问申请提交"""
    headers = {'Authorization': f'Bearer {visitor_token}'}

    application_data = {
        'visit_purpose': '校友返校参观',
        'target_person': '张老师',
        'target_department': '计算机学院',
        'visit_date': datetime.now().strftime('%Y-%m-%d'),
        'visit_time_start': '09:00',
        'visit_time_end': '17:00',
        'visitor_info': {
            'name': '测试访客',
            'phone': '13800138000',
            'id_card': '110101199001011234'
        }
    }

    response = requests.post(f"{BASE_URL}/api/visits",
                           json=application_data, headers=headers)

    if response.status_code == 201:
        return response.json()['application']['id']
    else:
        print(f"申请提交失败: {response.text}")
        return None

def test_teacher_approval(teacher_token, application_id):
    """测试教师审批"""
    headers = {'Authorization': f'Bearer {teacher_token}'}

    approval_data = {
        'status': 'approved',
        'approval_comment': '测试审批通过'
    }

    response = requests.put(f"{BASE_URL}/api/visits/{application_id}/approve",
                          json=approval_data, headers=headers)

    return response.status_code == 200

def test_security_verification(security_token, application_id):
    """测试保安验证"""
    headers = {'Authorization': f'Bearer {security_token}'}

    # 二维码验证
    qr_data = {'application_id': application_id}
    response = requests.post(f"{BASE_URL}/api/security-portal/visit/verify-qr",
                          json=qr_data, headers=headers)

    if response.status_code == 200:
        print("二维码验证成功")
        return True
    else:
        print(f"二维码验证失败: {response.text}")
        return False

def main():
    print("开始端到端测试...")

    # 1. 获取各个用户的访问令牌
    print("1. 获取访问令牌...")
    visitor_token = get_token('test_visitor_20251012_090428', 'Test123456')
    teacher_token = get_token('teacher001', 'teacher123')
    security_token = get_token('security001', 'security123')

    if not all([visitor_token, teacher_token, security_token]):
        print("❌ 获取令牌失败")
        return False

    print("✅ 所有令牌获取成功")

    # 2. 测试访问申请提交
    print("2. 提交访问申请...")
    application_id = test_visit_application(visitor_token)

    if not application_id:
        print("❌ 访问申请提交失败")
        return False

    print(f"✅ 访问申请提交成功，申请ID: {application_id}")

    # 3. 测试教师审批
    print("3. 教师审批申请...")
    if test_teacher_approval(teacher_token, application_id):
        print("✅ 教师审批成功")
    else:
        print("❌ 教师审批失败")
        return False

    # 4. 测试保安验证
    print("4. 保安验证申请...")
    if test_security_verification(security_token, application_id):
        print("✅ 保安验证成功")
    else:
        print("❌ 保安验证失败")
        return False

    print("\n🎉 端到端测试完成！")
    print("✅ 访客注册和登录")
    print("✅ 访问申请提交")
    print("✅ 教师审批")
    print("✅ 保安二维码验证")

    return True

if __name__ == '__main__':
    success = main()
    if success:
        print("\n所有测试通过！系统运行正常。")
    else:
        print("\n测试失败，请检查系统配置。")