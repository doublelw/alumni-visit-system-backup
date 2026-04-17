#!/usr/bin/env python3
"""
快速并发测试 - 5个用户
"""

import requests
import threading
import time
import random
from datetime import datetime

def generate_user_data(user_id):
    """生成测试用户数据"""
    timestamp = int(time.time())
    return {
        "username": f"quicktest_user_{user_id}_{timestamp}",
        "password": "test123456",
        "realName": f"快速测试用户{user_id}",
        "email": f"quicktest{user_id}_{timestamp}@test.com",
        "phone": f"138{random.randint(10000000, 99999999)}",
        "idCard": f"{random.randint(100000000000000000, 999999999999999999)}",
        "graduationYear": str(random.randint(2015, 2023)),
        "classNumber": str(random.randint(1, 20)),
        "division": random.choice(["理科", "文科", "工科", "综合"]),
        "major": random.choice(["计算机科学与技术", "软件工程", "电子信息工程"]),
        "classTeacher": f"老师{random.randint(1, 50)}",
        "currentCity": random.choice(["北京", "上海", "广州", "深圳"]),
        "workUnit": f"测试公司{random.randint(1, 100)}",
        "position": random.choice(["软件工程师", "产品经理", "项目经理"]),
        "diningCompanions": str(random.randint(0, 3)),
        "specialDietaryNeeds": random.choice(["", "无特殊需求", "素食"]),
        "visitPurpose": random.choice(["返校参观", "师生聚会", "校园活动"]),
        "expectedArrivalTime": f"{random.randint(8, 18)}:{random.randint(0, 59):02d}",
        "vehicleInfo": random.choice(["", "私家车", "出租车", "公共交通"]),
        "healthDeclaration": "true",
        "agreement": "true"
    }

def test_registration(user_id, results):
    """单个注册测试"""
    user_data = generate_user_data(user_id)

    try:
        # 访问首页
        session = requests.Session()
        home_response = session.get("https://www.pofeclife.top/", timeout=10)

        if home_response.status_code != 200:
            results.append({
                "user_id": user_id,
                "success": False,
                "error": f"首页访问失败: {home_response.status_code}"
            })
            return

        # 提交注册
        register_response = session.post(
            "https://www.pofeclife.top/api/auth/register",
            json=user_data,
            timeout=15,
            headers={"Content-Type": "application/json"}
        )

        success = (register_response.status_code == 200 and
                  "success" in register_response.text.lower())

        results.append({
            "user_id": user_id,
            "username": user_data["username"],
            "success": success,
            "status_code": register_response.status_code,
            "response": register_response.text[:100],
            "error": None if success else f"HTTP {register_response.status_code}"
        })

        print(f"用户 {user_id}: {'✓ 成功' if success else '✗ 失败'} (状态码: {register_response.status_code})")

    except Exception as e:
        results.append({
            "user_id": user_id,
            "success": False,
            "error": str(e)
        })
        print(f"用户 {user_id}: ✗ 异常 - {str(e)}")

def main():
    print("快速并发测试 - 5个用户")
    print("=" * 40)

    results = []
    threads = []
    start_time = time.time()

    # 创建5个并发线程
    for i in range(5):
        thread = threading.Thread(target=test_registration, args=(i + 1, results))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # 小延迟

    # 等待完成
    for thread in threads:
        thread.join()

    end_time = time.time()

    print("\n" + "=" * 40)
    print("测试结果")
    print("=" * 40)

    total_time = end_time - start_time
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"总耗时: {total_time:.2f} 秒")
    print(f"成功: {successful}/5")
    print(f"失败: {failed}/5")
    print(f"成功率: {successful/5*100:.1f}%")
    print(f"吞吐量: {5/total_time:.2f} 用户/秒")

    if failed > 0:
        print(f"\n失败详情:")
        for r in results:
            if not r["success"]:
                print(f"  用户{r['user_id']}: {r.get('error', '未知错误')}")

if __name__ == "__main__":
    main()