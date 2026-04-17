#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Direct test of external visitor creation"""
import requests
import json

url = "http://127.0.0.1:5000/api/external-visitor/create"
headers = {"Content-Type": "application/json"}

data = {
    "visitor_name": "张三",
    "visitor_phone": "13900000001",
    "visitor_company": "XX快递",
    "visit_purpose": "送货",
    "contact_person": "李老师"
}

print("Testing external visitor creation...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, ensure_ascii=False)}")

try:
    response = requests.post(url, headers=headers, json=data, timeout=5)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
