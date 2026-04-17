#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test simple parent display format"""
import requests

url = "http://127.0.0.1:5000/api/electronic-card/guard/verify"
headers = {"Content-Type": "application/json; charset=utf-8"}

data = {
    "code": "222222",
    "guard_name": "Guard01"
}

print("="*70)
print("Parent Verification - Simple Format Test")
print("="*70)

try:
    response = requests.post(url, headers=headers, json=data, timeout=5)
    result = response.json()

    if result.get('success'):
        person_info = result.get('data', {}).get('person_info', {})

        print("\n[OK] Verification successful\n")
        print("Display Format:")
        print("-" * 70)

        # 模拟页面显示
        print(f"访客: {person_info.get('name')} ({person_info.get('user_type_label')})")
        print()

        if person_info.get('related_student'):
            student = person_info['related_student']
            student_info = student['name']
            if student.get('student_id'):
                student_info += f" ({student['student_id']})"
            print(f"关联学生:     {student_info}")

        if person_info.get('related_student', {}).get('grade'):
            student = person_info['related_student']
            print(f"学生班级:     {student['grade']} {student['class']}")

        print(f"接待人:       {person_info.get('host_name', 'N/A')}")
        print(f"访问事由:     {person_info.get('visit_reason', 'N/A')}")
        print(f"联系电话:     {person_info.get('phone', 'N/A')}")
        print("-" * 70)

    else:
        print(f"[FAIL] {result.get('error')}")

except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "="*70)
print("All fields use the same simple, compact format")
print("="*70)
