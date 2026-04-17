#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test guard verification API"""
import requests
import json

url = "http://127.0.0.1:5000/api/electronic-card/guard/verify"
headers = {"Content-Type": "application/json; charset=utf-8"}
data = {
    "code": "666666",
    "guard_name": "门卫01"
}

print("Testing guard verification...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, ensure_ascii=False)}")

try:
    response = requests.post(url, headers=headers, json=data, timeout=5)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
except Exception as e:
    print(f"\nError: {e}")
