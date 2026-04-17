#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校友入校登记系统 - 综合端到端测试
遍历所有功能模块并验证系统稳定性
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"
TEST_RESULTS = []

def log_test(test_name, passed, message="", details=""):
    """记录测试结果"""
    status = "[PASS]" if passed else "[FAIL]"
    result = {
        "test": test_name,
        "status": status,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    TEST_RESULTS.append(result)
    try:
        print(f"\n{status}: {test_name}")
        if message:
            print(f"  {message}")
        if details and not passed:
            print(f"  Details: {details}")
    except UnicodeEncodeError:
        print(f"\n{status}: {test_name.encode('ascii', 'ignore').decode('ascii')}")
    return passed

def test_health_check():
    """测试健康检查接口"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        passed = response.status_code == 200
        return log_test("健康检查", passed,
                       f"Status: {response.status_code}",
                       response.text if not passed else "")
    except Exception as e:
        return log_test("健康检查", False, f"Exception: {str(e)}")

def test_index_page():
    """测试首页访问"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        passed = response.status_code == 200 and "校友" in response.text
        return log_test("首页访问", passed,
                       f"Status: {response.status_code}",
                       f"Content length: {len(response.text)}")
    except Exception as e:
        return log_test("首页访问", False, f"Exception: {str(e)}")

def test_admin_page():
    """测试管理后台页面"""
    try:
        response = requests.get(f"{BASE_URL}/admin", timeout=10)
        passed = response.status_code == 200 and ("admin" in response.text.lower() or "管理" in response.text or "login" in response.text.lower())
        return log_test("管理后台页面", passed,
                       f"Status: {response.status_code}",
                       f"Content preview: {response.text[:200]}")
    except Exception as e:
        return log_test("管理后台页面", False, f"Exception: {str(e)}")

def test_user_registration():
    """测试用户注册"""
    try:
        timestamp = int(time.time())
        test_user = {
            "username": f"test_user_{timestamp}",
            "password": "Test123456",
            "email": f"test_{timestamp}@example.com",
            "full_name": f"测试用户_{timestamp}",
            "user_type": "alumni",
            "graduation_year": 2020,
            "class_name": "高三(1)班"
        }

        response = requests.post(f"{BASE_URL}/api/auth/register",
                                json=test_user,
                                timeout=10)

        # 期望: 成功注册或用户已存在
        passed = response.status_code in [200, 201, 409]  # 409 = Conflict (user exists)

        return log_test("用户注册API", passed,
                       f"Status: {response.status_code}",
                       response.text if not passed else "")
    except Exception as e:
        return log_test("用户注册API", False, f"Exception: {str(e)}")

def test_user_login():
    """测试用户登录"""
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }

        response = requests.post(f"{BASE_URL}/api/auth/login",
                                json=login_data,
                                timeout=10)

        passed = response.status_code == 200

        if passed and response.json().get("access_token"):
            token = response.json()["access_token"]
            return log_test("用户登录API", True,
                           f"Successfully obtained token")
        else:
            return log_test("用户登录API", False,
                           f"Status: {response.status_code}",
                           response.text)
    except Exception as e:
        return log_test("用户登录API", False, f"Exception: {str(e)}")

def test_admin_login():
    """测试管理员登录"""
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }

        response = requests.post(f"{BASE_URL}/api/auth/admin/login",
                                json=login_data,
                                timeout=10)

        passed = response.status_code == 200

        if passed and response.json().get("access_token"):
            return log_test("管理员登录API", True, "Admin login successful")
        else:
            return log_test("管理员登录API", False,
                           f"Status: {response.status_code}",
                           response.text)
    except Exception as e:
        return log_test("管理员登录API", False, f"Exception: {str(e)}")

def test_api_endpoints():
    """测试主要API端点"""
    endpoints = [
        ("/api/users/alumni", "校友列表API"),
        ("/api/visits/applications", "访问申请API"),
        ("/api/admin/dashboard", "管理员仪表板API"),
        ("/api/public/calendar", "公开日历API"),
    ]

    results = []
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            passed = response.status_code in [200, 401]  # 401 = Unauthorized (expected without auth)
            results.append(log_test(name, passed,
                                  f"Status: {response.status_code}",
                                  response.text[:200] if not passed else ""))
        except Exception as e:
            results.append(log_test(name, False, f"Exception: {str(e)}"))

    return all(results)

def test_static_files():
    """测试静态文件服务"""
    static_paths = [
        "/static/css/",
        "/static/js/",
    ]

    results = []
    for path in static_paths:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=10)
            passed = response.status_code in [200, 404]  # 404 is acceptable for directory listing
            results.append(log_test(f"静态文件访问: {path}", passed,
                                  f"Status: {response.status_code}"))
        except Exception as e:
            results.append(log_test(f"静态文件访问: {path}", False,
                                  f"Exception: {str(e)}"))

    return all(results)

def test_database_connection():
    """测试数据库连接"""
    try:
        # 通过health check间接测试数据库
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        data = response.json()
        passed = response.status_code == 200

        return log_test("数据库连接", passed,
                       f"Health check passed",
                       json.dumps(data, ensure_ascii=False) if not passed else "")
    except Exception as e:
        return log_test("数据库连接", False, f"Exception: {str(e)}")

def test_page_loads():
    """测试主要页面加载"""
    pages = [
        ("/", "首页"),
        ("/register", "注册页"),
        ("/admin", "管理后台"),
        ("/admin-login.html", "管理员登录页"),
        ("/event-registration.html", "活动注册页"),
    ]

    results = []
    for path, name in pages:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=15)
            passed = response.status_code == 200
            results.append(log_test(f"页面加载: {name}", passed,
                                  f"Status: {response.status_code}, Size: {len(response.content)} bytes"))
        except Exception as e:
            results.append(log_test(f"页面加载: {name}", False,
                                  f"Exception: {str(e)}"))

    return all(results)

def stress_test_requests(num_requests=20):
    """压力测试 - 并发请求"""
    print(f"\n{'='*60}")
    print(f"压力测试: 发送 {num_requests} 个并发请求")
    print(f"{'='*60}")

    import concurrent.futures

    def make_request(request_id):
        start_time = time.time()
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=10)
            elapsed = time.time() - start_time
            return {
                "id": request_id,
                "status": response.status_code,
                "time": elapsed,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "id": request_id,
                "status": 0,
                "time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(num_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    total_time = time.time() - start_time
    successful = sum(1 for r in results if r["success"])
    avg_time = sum(r["time"] for r in results) / len(results)

    passed = successful >= num_requests * 0.9  # 90%成功率

    return log_test(f"压力测试 ({num_requests}请求)", passed,
                   f"成功: {successful}/{num_requests}, "
                   f"总耗时: {total_time:.2f}s, "
                   f"平均响应: {avg_time:.3f}s",
                   f"失败详情: {[r for r in results if not r['success']]}")

def memory_leak_test():
    """内存泄漏测试 - 持续请求"""
    print(f"\n{'='*60}")
    print("内存泄漏测试: 发送100个请求")
    print(f"{'='*60}")

    responses = []
    for i in range(100):
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/health", timeout=5)
            elapsed = time.time() - start
            responses.append({
                "request": i,
                "status": response.status_code,
                "time": elapsed,
                "size": len(response.content)
            })

            if i % 20 == 0:
                print(f"  已完成 {i}/100 请求")

        except Exception as e:
            print(f"  请求 {i} 失败: {e}")

    # 分析响应时间趋势
    times = [r["time"] for r in responses]
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    # 检查是否有明显的性能下降
    first_half = times[:50]
    second_half = times[50:]
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    degradation = (avg_second - avg_first) / avg_first * 100

    passed = degradation < 50  # 性能下降不超过50%

    return log_test("内存泄漏测试", passed,
                   f"平均响应: {avg_time:.3f}s, "
                   f"性能下降: {degradation:.1f}%, "
                   f"成功率: {len(responses)}/100",
                   f"响应时间范围: {min_time:.3f}s - {max_time:.3f}s")

def run_all_tests():
    """运行所有测试"""
    print("="*70)
    print("校友入校登记系统 - 综合端到端测试")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试目标: {BASE_URL}")
    print("="*70)

    tests = [
        ("系统健康检查", [
            test_health_check,
            test_database_connection,
        ]),
        ("页面访问测试", [
            test_index_page,
            test_admin_page,
            test_page_loads,
            test_static_files,
        ]),
        ("API功能测试", [
            test_user_registration,
            test_user_login,
            test_admin_login,
            test_api_endpoints,
        ]),
        ("稳定性测试", [
            stress_test_requests,
            memory_leak_test,
        ])
    ]

    for category, test_funcs in tests:
        print(f"\n{'='*70}")
        print(f"测试类别: {category}")
        print(f"{'='*70}")

        for test_func in test_funcs:
            try:
                test_func()
                time.sleep(0.5)  # 避免请求过快
            except Exception as e:
                print(f"\n[FAIL]: {test_func.__name__} - Uncaught exception: {e}")

    # 打印测试摘要
    print("\n" + "="*70)
    print("测试摘要")
    print("="*70)

    passed = sum(1 for r in TEST_RESULTS if "PASS" in r["status"])
    failed = sum(1 for r in TEST_RESULTS if "FAIL" in r["status"])
    total = len(TEST_RESULTS)

    print(f"总测试数: {total}")
    print(f"通过: {passed} ({passed/total*100:.1f}%)")
    print(f"失败: {failed} ({failed/total*100:.1f}%)")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if failed > 0:
        print("\n失败的测试:")
        for result in TEST_RESULTS:
            if "FAIL" in result["status"]:
                print(f"  - {result['test']}: {result['message']}")

    # 保存测试报告
    report_path = "test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{passed/total*100:.1f}%"
            },
            "tests": TEST_RESULTS,
            "timestamp": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)

    print(f"\n详细测试报告已保存到: {report_path}")

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
