"""
测试访客注册完整流程
"""

import requests
import time
import sqlite3

BASE_URL = "http://localhost:5000"

def check_database():
    """检查数据库中的访客记录"""
    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 查询访客用户
    cursor.execute('SELECT username, real_name, phone, user_type FROM users WHERE phone=?', ('13900009999',))
    user = cursor.fetchone()

    if user:
        print(f"  [数据库] 找到访客: {user}")
    else:
        print(f"  [数据库] 未找到访客")

    conn.close()
    return user

print("=" * 60)
print("访客注册流程测试")
print("=" * 60)

# 检查初始状态
print("\n[初始检查] 查询数据库")
check_database()

# ========== 步骤1：外网生成访客码 ==========
print("\n[步骤1] 外网生成访客码")

try:
    response = requests.post(f"{BASE_URL}/external/generate-code",
        json={"code_type": "visitor", "phone": "13900009999"},
        timeout=10
    )

    result = response.json()
    if result.get('success'):
        visitor_code = result['code']
        print(f"  [OK] 生成访客码: {visitor_code}")
    else:
        print(f"  [ERROR] 生成失败: {result}")
        exit(1)

except Exception as e:
    print(f"  [ERROR] 请求失败: {e}")
    exit(1)

# ========== 步骤2：老师验证并创建访客账号 ==========
print("\n[步骤2a] 老师登录")

try:
    response = requests.post(f"{BASE_URL}/api/wechat/teacher/login",
        json={"phone": "13800000001", "password": "1234"},
        timeout=10
    )

    result = response.json()
    if result.get('success'):
        teacher_token = result['data']['token']
        print(f"  [OK] 老师登录成功")
    else:
        print(f"  [ERROR] 登录失败: {result}")
        exit(1)

except Exception as e:
    print(f"  [ERROR] 请求失败: {e}")
    exit(1)

print("\n[步骤2b] 老师验证访客码并创建账号")

try:
    response = requests.post(f"{BASE_URL}/api/wechat/teacher/add-visitor-v2",
        json={
            "access_code": visitor_code,
            "name": "张三",
            "id_card": "110101199001011234",
            "visit_purpose": "meeting",
            "visit_reason": "商务洽谈"
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=10
    )

    result = response.json()
    print(f"  [响应] {result}")

    if result.get('success'):
        print(f"  [OK] 访客账号创建成功")
    else:
        print(f"  [ERROR] 创建失败: {result}")

except Exception as e:
    print(f"  [ERROR] 请求失败: {e}")
    import traceback
    traceback.print_exc()

# ========== 检查数据库 ==========
print("\n[步骤3] 检查数据库")
visitor = check_database()

if visitor:
    print("\n[步骤4] 门卫验证访客码")

    try:
        response = requests.post(f"{BASE_URL}/api/guard/verify",
            json={
                "code": visitor_code,
                "guard_name": "门卫01",
                "verify_type": "visitor"
            },
            timeout=10
        )

        result = response.json()
        print(f"  [响应] {result}")

        if result.get('success') and result['data'].get('valid'):
            user_info = result['data']['user_info']
            print(f"  [OK] 门卫验证通过")
            print(f"  [信息] 姓名: {user_info['name']}, 手机: {user_info['phone']}")
        else:
            print(f"  [ERROR] 门卫验证失败")

    except Exception as e:
        print(f"  [ERROR] 请求失败: {e}")
else:
    print("\n[跳过] 数据库中没有访客记录，跳过门卫验证")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
