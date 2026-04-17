#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test parent verification detailed info"""
import requests
import json

url = "http://127.0.0.1:5000/api/electronic-card/guard/verify"
headers = {"Content-Type": "application/json; charset=utf-8"}

# Test parent verification
data = {
    "code": "222222",
    "guard_name": "Guard01"
}

print("="*70)
print("Parent Verification - Detailed Student Info Test")
print("="*70)

try:
    response = requests.post(url, headers=headers, json=data, timeout=5)
    result = response.json()

    if result.get('success'):
        person_info = result.get('data', {}).get('person_info', {})

        print("\n[OK] Verification successful")
        print(f"Parent Name: {person_info.get('name')}")
        print(f"Parent Type: {person_info.get('user_type_label')}")
        print(f"\nChild Class: {person_info.get('child_class_name', 'N/A')}")

        if person_info.get('related_student'):
            student = person_info['related_student']
            print(f"\n--- Related Student Details ---")
            print(f"Name: {student.get('name', 'N/A')}")
            print(f"Student ID: {student.get('student_id', 'N/A')}")
            print(f"Grade: {student.get('grade', 'N/A')}")
            print(f"Class: {student.get('class', 'N/A')}")

            print(f"\n--- Display Format ---")
            display_name = student['name']
            if student.get('student_id'):
                display_name += f" (Student ID: {student['student_id']})"
            print(f"Student Display: {display_name}")
            print(f"Class Info: {student.get('grade', 'N/A')} {student.get('class', 'N/A')}")

        # Show host and approval info
        print(f"\n--- Visit Details ---")
        print(f"Host: {person_info.get('host_name', 'N/A')}")
        print(f"Visit Reason: {person_info.get('visit_reason', 'N/A')}")
        print(f"Approved By: {person_info.get('approved_by', 'N/A')}")
        print(f"Approved At: {person_info.get('approved_at', 'N/A')}")

    else:
        error = result.get('error', 'Unknown error')
        print(f"[FAIL] Verification failed: {error}")

except Exception as e:
    print(f"[ERROR] Request failed: {e}")

print("\n" + "="*70)
