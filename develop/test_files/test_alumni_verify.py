#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test alumni verification"""
import requests
import json

url = "http://127.0.0.1:5000/api/electronic-card/guard/verify"
headers = {"Content-Type": "application/json; charset=utf-8"}

# Test codes
test_codes = ['888888', '222222', '111111']

for code in test_codes:
    data = {
        "code": code,
        "guard_name": "门卫01"
    }

    print(f"\n{'='*60}")
    print(f"Testing code: {code}")
    print('='*60)

    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        result = response.json()

        if result.get('success'):
            person_info = result.get('data', {}).get('person_info', {})
            print(f"Name: {person_info.get('name')}")
            print(f"Type: {person_info.get('user_type_label')}")
            print(f"Class Name: {person_info.get('class_name', 'N/A')}")
            print(f"Graduation Year: {person_info.get('graduation_year', 'N/A')}")

            if person_info.get('related_student'):
                student = person_info['related_student']
                print(f"Related Student: {student.get('name')}")
                print(f"Child Class: {person_info.get('child_class_name', 'N/A')}")
        else:
            print(f"Error: {result.get('error')}")

    except Exception as e:
        print(f"Request failed: {e}")
