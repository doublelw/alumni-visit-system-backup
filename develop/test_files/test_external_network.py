"""
测试外网/内网分离架构的访客登记流程
"""

import requests
import time

BASE_URL = "http://localhost:5000"

print("=" * 60)
print("外网/内网分离架构 - 访客登记流程测试")
print("=" * 60)

# ========== 步骤1：访客在外网登记（生成访客码）==========
print("\n[步骤1] 访客在外网登记（模拟访客填写信息）")

visitor_data = {
    "name": "张三",
    "phone": "13900009999",
    "id_card": "110101199001011234",
    "visit_purpose": "meeting",
    "visit_reason": "商务洽谈"
}

print(f"  访客信息: 姓名={visitor_data['name']}, 手机={visitor_data['phone']}")

try:
    # 调用外网API生成访客码
    response = requests.post(f"{BASE_URL}/external/generate-code", json={
        "code_type": "visitor",
        "phone": visitor_data['phone']
    }, timeout=10)

    result = response.json()
    if result.get('success'):
        visitor_code = result['code']
        print(f"  [OK] 外网生成访客码: {visitor_code}")
        print(f"  [提示] 访客将此码发送给老师: {visitor_code}")
    else:
        print(f"  [ERROR] 生成访客码失败: {result}")
        exit(1)

except Exception as e:
    print(f"  [ERROR] 外网请求失败: {e}")
    exit(1)

# ========== 步骤2：老师登录获取token ==========
print("\n[步骤2a] 老师登录（获取JWT token）")

try:
    response = requests.post(f"{BASE_URL}/api/wechat/teacher/login", json={
        "phone": "13800000001",
        "password": "1234"
    }, timeout=10)

    result = response.json()
    if result.get('success'):
        teacher_token = result['data']['token']
        print(f"  [OK] 老师登录成功，获取token: {teacher_token[:20]}...")
    else:
        print(f"  [ERROR] 老师登录失败: {result}")
        exit(1)
except Exception as e:
    print(f"  [ERROR] 登录请求失败: {e}")
    exit(1)

# ========== 步骤2b：老师验证访客码并补充信息 ==========
print("\n[步骤2b] 老师验证访客码（模拟教师操作）")

print(f"  老师输入访客码: {visitor_code}")
print(f"  老师补充信息: 姓名={visitor_data['name']}, 身份证={visitor_data['id_card']}")

try:
    # 调用内网API添加访客（使用新的外网/内网分离版本）
    response = requests.post(f"{BASE_URL}/api/wechat/teacher/add-visitor-v2",
        json={
            "access_code": visitor_code,
            "name": visitor_data['name'],
            "id_card": visitor_data['id_card'],
            "visit_purpose": visitor_data['visit_purpose'],
            "visit_reason": visitor_data['visit_reason']
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=10
    )

    result = response.json()
    if result.get('success'):
        visitor_info = result['data']['visitor']
        print(f"  [OK] 内网创建访客账号: {visitor_info}")
        print(f"  [OK] 访客码: {result['data']['access_code']}")
    else:
        print(f"  [ERROR] 添加访客失败: {result}")
        exit(1)

except Exception as e:
    print(f"  [ERROR] 内网请求失败: {e}")
    exit(1)

# ========== 步骤3：门卫验证访客码 ==========
print("\n[步骤3] 门卫验证访客码（模拟门卫操作）")

print(f"  门卫输入访客码: {visitor_code}")

try:
    # 调用门卫验证API
    response = requests.post(f"{BASE_URL}/api/guard/verify",
        json={
            "code": visitor_code,
            "guard_name": "门卫01",
            "verify_type": "visitor"
        },
        timeout=10
    )

    result = response.json()
    if result.get('success') and result['data']['valid']:
        user_info = result['data']['user_info']
        print(f"  [OK] 门卫验证通过")
        print(f"  [OK] 访客姓名: {user_info['name']}")
        print(f"  [OK] 访客手机: {user_info['phone']}")
        print(f"  [OK] 访问目的: {user_info.get('visit_purpose', '未指定')}")
    else:
        print(f"  [ERROR] 门卫验证失败: {result}")
        exit(1)

except Exception as e:
    print(f"  [ERROR] 门卫验证请求失败: {e}")
    exit(1)

# ========== 完成 ==========
print("\n" + "=" * 60)
print("[SUCCESS] 外网/内网分离架构测试通过！")
print("=" * 60)
print("\n测试流程总结：")
print("1. 访客在外网登记 → 外网存储（访客码+手机号）")
print("2. 老师验证访客码 → 从外网获取信息 → 在内网创建完整账号")
print("3. 门卫验证访客码 → 查询内网数据库 → 验证通过")
print("\n架构特点：")
print("- 外网：只存储最小信息（访客码+手机号）")
print("- 内网：存储完整信息（姓名、身份证、访问记录等）")
print("- 数据流：外网 → 内网（单向迁移）")
print("- 隔离性：外网和内网数据库完全独立")
