#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证测试 - 使用正确的路径
验证所有主要功能是否正常
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

print("="*70)
print("校友入校登记系统 - 快速验证测试")
print("="*70)
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"服务器: {BASE_URL}")
print("="*70)

session = requests.Session()
test_results = []

def test(name, passed, details=""):
    """记录测试结果"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")
    if details and not passed:
        print(f"      {details}")
    test_results.append({"name": name, "passed": passed})
    return passed

# 1. 健康检查
print("\n[1] 系统健康检查")
print("-"*70)
try:
    response = session.get(f"{BASE_URL}/health", timeout=10)
    test("健康检查端点", response.status_code == 200,
         f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"      响应: {response.json()}")
except Exception as e:
    test("健康检查端点", False, str(e))

# 2. 页面访问测试（使用正确的路径）
print("\n[2] 页面访问测试")
print("-"*70)
pages = [
    ("首页", "/"),
    ("注册页面", "/register"),
    ("单次注册", "/registerOnce"),
    ("活动报名", "/event-registration"),
    ("管理员登录", "/admin-login"),
    ("管理后台", "/alumni-management-2025"),
]

for name, path in pages:
    try:
        response = session.get(f"{BASE_URL}{path}", timeout=10)
        test(f"{name} ({path})", response.status_code == 200,
             f"Status: {response.status_code}, Size: {len(response.content)} bytes")
    except Exception as e:
        test(f"{name} ({path})", False, str(e))

# 3. API端点测试
print("\n[3] API端点测试")
print("-"*70)

# 3.1 公开API
print("  3.1 公开API")
try:
    # 获取验证码
    response = session.get(f"{BASE_URL}/api/auth/captcha", timeout=10)
    test("获取验证码API", response.status_code == 200,
         f"Status: {response.status_code}")
except Exception as e:
    test("获取验证码API", False, str(e))

# 3.2 认证API
print("\n  3.2 认证API")

# 测试管理员登录
print("  测试管理员登录:")
try:
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    response = session.post(f"{BASE_URL}/api/auth/login",
                           json=login_data,
                           timeout=10)
    print(f"    登录API: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"    [成功] 获取到访问令牌")
        token = result.get("access_token")
        if token:
            headers = {"Authorization": f"Bearer {token}"}
            print(f"    Token: {token[:50]}...")
        else:
            headers = None
            print(f"    [警告] 未找到access_token字段")
    else:
        headers = None
        print(f"    [失败] {response.json()}")
except Exception as e:
    print(f"    [错误] {str(e)}")
    headers = None

# 3.3 受保护的API
if headers:
    print("\n  3.3 受保护的API测试")
    protected_apis = [
        ("管理员仪表板", "/api/admin/dashboard"),
        ("校友列表", "/api/users/alumni"),
        ("访问申请", "/api/visits/applications"),
    ]

    for name, endpoint in protected_apis:
        try:
            response = session.get(f"{BASE_URL}{endpoint}",
                                  headers=headers,
                                  timeout=10)
            test(f"{name}", response.status_code == 200,
                 f"Status: {response.status_code}")
        except Exception as e:
            test(f"{name}", False, str(e))
else:
    print("\n  3.3 受保护的API测试 - [跳过] 未获取到令牌")

# 4. 性能快速测试
print("\n[4] 性能快速测试")
print("-"*70)
print("  测试10个并发请求:")

import time
import concurrent.futures

def make_request(idx):
    start = time.time()
    try:
        response = session.get(f"{BASE_URL}/", timeout=10)
        elapsed = time.time() - start
        return {"success": response.status_code == 200, "time": elapsed}
    except:
        return {"success": False, "time": time.time() - start}

start_time = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(make_request, i) for i in range(10)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]

total_time = time.time() - start_time
successful = sum(1 for r in results if r["success"])
avg_time = sum(r["time"] for r in results) / len(results)

test(f"并发测试 (10请求)", successful >= 9,
     f"成功: {successful}/10, 平均: {avg_time:.3f}s")

# 5. 数据完整性测试
print("\n[5] 数据完整性测试")
print("-"*70)

if headers:
    print("  测试数据查询:")
    try:
        response = session.get(f"{BASE_URL}/api/admin/statistics",
                              headers=headers,
                              timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("    [成功] 获取到统计数据")
            print(f"    数据字段: {list(stats.keys())}")
        else:
            print(f"    [警告] Status: {response.status_code}")
    except Exception as e:
        print(f"    [错误] {str(e)}")
else:
    print("  [跳过] 未获取到令牌")

# 测试总结
print("\n" + "="*70)
print("测试总结")
print("="*70)

passed = sum(1 for r in test_results if r["passed"])
total = len(test_results)

print(f"总测试数: {total}")
print(f"通过: {passed}")
print(f"失败: {total - passed}")
print(f"通过率: {passed/total*100:.1f}%")

if passed == total:
    print("\n[成功] 所有测试通过！系统运行正常。")
elif passed >= total * 0.8:
    print("\n[良好] 大部分测试通过，系统基本正常。")
    print("       请检查失败的测试项。")
else:
    print("\n[警告] 部分测试失败，请检查系统配置。")
    print("\n失败的测试:")
    for r in test_results:
        if not r["passed"]:
            print(f"  - {r['name']}")

print("\n推荐操作:")
print("  1. 在浏览器中访问: http://localhost:5000/")
print("  2. 管理后台登录: http://localhost:5000/admin-login")
print("  3. 查看完整访问指南: SYSTEM_ACCESS_GUIDE.md")

print("\n" + "="*70)
print(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
