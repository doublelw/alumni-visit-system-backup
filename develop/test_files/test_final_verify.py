#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Final verification test for all user types"""
import requests
import json

url = "http://127.0.0.1:5000/api/electronic-card/guard/verify"
headers = {"Content-Type": "application/json; charset=utf-8"}

test_cases = [
    {'code': '888888', 'type': 'alumni', 'expected_field': 'graduation_year'},
    {'code': '222222', 'type': 'parent', 'expected_field': 'child_class_name'},
    {'code': '111111', 'type': 'student', 'expected_field': 'class_name'},
    {'code': '666666', 'type': 'teacher', 'expected_field': 'employee_id'},
]

print('='*70)
print('Gate Verification System - Final Test')
print('='*70)

for test in test_cases:
    code = test['code']
    user_type = test['type']
    expected_field = test['expected_field']

    data = {
        "code": code,
        "guard_name": "Guard01"
    }

    print(f"\n{'─'*70}")
    print(f"Code: {code} | Expected Type: {user_type}")
    print(f"{'─'*70}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        result = response.json()

        if result.get('success'):
            person_info = result.get('data', {}).get('person_info', {})

            print(f"[OK] Verification successful")
            print(f"   Name: {person_info.get('name', 'N/A')}")
            print(f"   Type: {person_info.get('user_type_label', 'N/A')}")

            # Check expected field
            field_value = person_info.get(expected_field, 'N/A')
            if field_value and field_value != 'N/A':
                print(f"   {expected_field}: {field_value}")

            # Show class_name if different
            class_name = person_info.get('class_name', '')
            if class_name and expected_field != 'class_name':
                print(f"   class_name: {class_name}")

            # Show related student for parents
            if user_type == 'parent' and person_info.get('related_student'):
                student = person_info['related_student']
                print(f"   Related Student: {student.get('name', 'N/A')}")

            # Show employee_id for teachers
            if user_type == 'teacher' and person_info.get('employee_id'):
                print(f"   Employee ID: {person_info['employee_id']}")

        else:
            error = result.get('error', 'Unknown error')
            print(f"[FAIL] Verification failed: {error}")

    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

print(f"\n{'='*70}")
print("Test Complete")
print('='*70)
