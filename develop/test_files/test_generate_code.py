"""
测试家长生成6位码API
"""
import requests
import json

# 先登录获取token
login_url = 'http://127.0.0.1:5000/api/wechat/parent/login'
login_data = {
    'phone': '13900002002',
    'password': '88'
}

print("=" * 60)
print("Step 1: 家长登录")
print("=" * 60)

response = requests.post(login_url, json=login_data)
result = response.json()

if result.get('success'):
    token = result['data']['token']
    parent_id = result['data']['parent']['id']
    print(f"[OK] Login successful")
    print(f"Token: {token[:30]}...")
    print(f"Parent ID: {parent_id}")

    # 生成6位码
    print("\n" + "=" * 60)
    print("Step 2: 生成6位码")
    print("=" * 60)

    code_url = 'http://127.0.0.1:5000/api/wechat/parent/generate-visit-code'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    code_data = {
        'student_id': 44,
        'visit_date': '2026-03-27',
        'visit_purpose': '学生请假'
    }

    print(f"Request: {json.dumps(code_data, ensure_ascii=False)}")

    response = requests.post(code_url, headers=headers, json=code_data)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"\n[SUCCESS] Generated code: {result['data']['code']}")
        else:
            print(f"\n[ERROR] {result.get('error')}")
    else:
        print(f"\n[ERROR] HTTP {response.status_code}")

else:
    print(f"[ERROR] Login failed: {result.get('error')}")
