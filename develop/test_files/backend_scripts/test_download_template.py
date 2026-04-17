"""
测试用户模板下载功能
"""

import requests
import json

BASE_URL = "http://localhost:5000"

print("=" * 80)
print("  测试用户模板下载功能")
print("=" * 80)

# Step 1: 管理员登录
print("\n[Step 1] 管理员登录...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"username": "admin", "password": "admin123"},
    timeout=10
)

if login_response.status_code != 200:
    print(f"[ERROR] 登录失败: {login_response.text}")
    exit(1)

login_result = login_response.json()
admin_token = login_result.get('access_token') or login_result.get('token')
print(f"[OK] 管理员登录成功")
print(f"Token: {admin_token[:20]}...")

# Step 2: 下载用户模板
print("\n[Step 2] 下载用户模板...")
headers = {"Authorization": f"Bearer {admin_token}"}

template_response = requests.get(
    f"{BASE_URL}/api/admin/users/template",
    headers=headers,
    timeout=30
)

print(f"HTTP状态码: {template_response.status_code}")

if template_response.status_code == 200:
    # 检查Content-Type
    content_type = template_response.headers.get('Content-Type')
    content_disposition = template_response.headers.get('Content-Disposition')

    print(f"[OK] 下载成功！")
    print(f"Content-Type: {content_type}")
    print(f"Content-Disposition: {content_disposition}")

    # 保存到文件
    filename = "用户导入模板.xlsx"
    with open(filename, 'wb') as f:
        f.write(template_response.content)

    print(f"\n[SUCCESS] 文件已保存: {filename}")
    print(f"文件大小: {len(template_response.content)} 字节")
else:
    error_msg = template_response.text
    print(f"[ERROR] 下载失败:")
    print(json.dumps(json.loads(error_msg), indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
