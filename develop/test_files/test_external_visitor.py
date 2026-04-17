#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test external visitor creation and verification"""
import requests
import json

base_url = "http://127.0.0.1:5000"
headers = {"Content-Type": "application/json; charset=utf-8"}

print("="*70)
print("External Visitor System - Test")
print("="*70)

# Test 1: Create external visitor
print("\n[Test 1] Creating external visitor...")
visitor_data = {
    "visitor_name": "张三",
    "visitor_phone": "13900000001",
    "visitor_company": "XX快递",
    "visit_purpose": "送货",
    "contact_person": "李老师",
    "visit_date": "2026-03-28",
    "notes": "每日送货"
}

try:
    response = requests.post(
        f"{base_url}/api/external-visitor/create",
        headers=headers,
        json=visitor_data,
        timeout=5
    )
    result = response.json()

    if result.get('success'):
        data = result['data']
        print(f"[OK] Visitor created successfully!")
        print(f"     Visitor Code: {data['visitor_code']}")
        print(f"     Visitor Name: {data['visitor_name']}")
        print(f"     Contact Person: {data['contact_person']}")
        print(f"     Visit Purpose: {data['visit_purpose']}")
        print(f"     Visit Date: {data['visit_date']}")

        visitor_code = data['visitor_code']

        # Test 2: Verify at gate
        print("\n[Test 2] Verifying at gate...")
        verify_data = {
            "code": visitor_code,
            "guard_name": "门卫01"
        }

        response = requests.post(
            f"{base_url}/api/electronic-card/guard/verify",
            headers=headers,
            json=verify_data,
            timeout=5
        )
        result = response.json()

        if result.get('success'):
            person_info = result.get('data', {}).get('person_info', {})
            print(f"[OK] Verification successful!")
            print(f"     Type: {person_info.get('user_type_label')}")
            print(f"     Purpose: {person_info.get('visit_purpose')}")
            print(f"     Contact: {person_info.get('host_name')}")
        else:
            print(f"[FAIL] Verification failed: {result.get('error')}")

    else:
        print(f"[FAIL] Creation failed: {result.get('error')}")

except Exception as e:
    print(f"[ERROR] Request failed: {e}")

print("\n" + "="*70)
print("Test Complete")
print("="*70)
