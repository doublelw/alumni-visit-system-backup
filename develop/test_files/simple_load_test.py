#!/usr/bin/env python3
"""
简化版并发性能测试脚本
模拟50个用户同时访问网站并提交注册
"""

import requests
import threading
import time
import random
import json
from datetime import datetime

class SimpleLoadTest:
    def __init__(self, base_url="https://www.pofeclife.top", users=50):
        self.base_url = base_url
        self.users = users
        self.results = []
        self.lock = threading.Lock()

    def generate_user_data(self, user_id):
        """生成测试用户数据"""
        timestamp = int(time.time())
        return {
            "username": f"loadtest_user_{user_id}_{timestamp}",
            "password": "test123456",
            "realName": f"压力测试用户{user_id}",
            "email": f"loadtest{user_id}_{timestamp}@test.com",
            "phone": f"138{random.randint(10000000, 99999999)}",
            "idCard": f"{random.randint(100000000000000000, 999999999999999999)}",  # 18位身份证号
            "graduationYear": str(random.randint(2015, 2023)),
            "classNumber": str(random.randint(1, 20)),  # 班级编号
            "division": random.choice(["理科", "文科", "工科", "综合"]),
            "major": random.choice(["计算机科学与技术", "软件工程", "电子信息工程", "机械工程", "经济管理"]),
            "classTeacher": f"老师{random.randint(1, 50)}",
            "currentCity": random.choice(["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]),
            "workUnit": f"测试公司{random.randint(1, 100)}",
            "position": random.choice(["软件工程师", "产品经理", "项目经理", "技术总监", "市场专员"]),
            "diningCompanions": str(random.randint(0, 3)),  # 字符串形式的就餐人数
            "specialDietaryNeeds": random.choice(["", "无特殊需求", "素食", "清真"]),
            "visitPurpose": random.choice(["返校参观", "师生聚会", "校园活动", "学术交流"]),
            "expectedArrivalTime": f"{random.randint(8, 18)}:{random.randint(0, 59):02d}",
            "vehicleInfo": random.choice(["", "私家车", "出租车", "公共交通"]),
            "healthDeclaration": "true",
            "agreement": "true"
        }

    def test_user_registration(self, user_id):
        """单个用户注册测试"""
        user_data = self.generate_user_data(user_id)

        result = {
            "user_id": user_id,
            "username": user_data["username"],
            "start_time": time.time(),
            "success": False,
            "error": None,
            "response_time": 0,
            "status_code": 0
        }

        try:
            # 创建session
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'LoadTest/1.0',
                'Content-Type': 'application/json'
            })

            # 1. 访问首页
            start = time.time()
            home_response = session.get(self.base_url, timeout=10)
            home_time = time.time() - start

            if home_response.status_code != 200:
                result["error"] = f"首页访问失败: {home_response.status_code}"
                result["response_time"] = home_time * 1000
                result["status_code"] = home_response.status_code
                return result

            # 2. 提交注册
            start = time.time()
            register_response = session.post(
                f"{self.base_url}/api/auth/register",
                json=user_data,
                timeout=15
            )
            register_time = time.time() - start

            result["response_time"] = (home_time + register_time) * 1000
            result["status_code"] = register_response.status_code

            # 检查注册是否成功
            if register_response.status_code == 200:
                try:
                    response_data = register_response.json()
                    if response_data.get("success", False):
                        result["success"] = True
                    else:
                        result["error"] = response_data.get("message", "注册失败")
                except:
                    # 如果不是JSON格式，检查HTTP状态
                    if "成功" in register_response.text or "success" in register_response.text.lower():
                        result["success"] = True
                    else:
                        result["error"] = "注册响应格式异常"
            else:
                result["error"] = f"HTTP {register_response.status_code}: {register_response.text[:100]}"

        except requests.exceptions.Timeout:
            result["error"] = "请求超时"
        except requests.exceptions.ConnectionError:
            result["error"] = "连接错误"
        except Exception as e:
            result["error"] = f"未知错误: {str(e)}"

        result["end_time"] = time.time()

        # 线程安全地添加结果
        with self.lock:
            self.results.append(result)

        return result

    def run_test(self):
        """运行并发测试"""
        print(f"开始并发性能测试")
        print(f"目标网站: {self.base_url}")
        print(f"并发用户数: {self.users}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)

        start_time = time.time()

        # 创建并启动线程
        threads = []
        for i in range(self.users):
            thread = threading.Thread(target=self.test_user_registration, args=(i + 1,))
            threads.append(thread)
            thread.start()
            # 小延迟避免同时启动造成峰值压力
            time.sleep(0.05)

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # 分析结果
        self.analyze_results(total_time)

    def analyze_results(self, total_time):
        """分析测试结果"""
        print("\n" + "=" * 60)
        print("并发性能测试报告")
        print("=" * 60)

        total_users = len(self.results)
        successful_users = sum(1 for r in self.results if r["success"])
        failed_users = total_users - successful_users
        success_rate = (successful_users / total_users * 100) if total_users > 0 else 0

        print(f"测试总耗时: {total_time:.2f} 秒")
        print(f"测试用户总数: {total_users}")
        print(f"成功注册数: {successful_users}")
        print(f"失败注册数: {failed_users}")
        print(f"成功率: {success_rate:.2f}%")

        if successful_users > 0:
            response_times = [r["response_time"] for r in self.results if r["success"]]
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)

            print(f"\n响应时间统计 (成功注册):")
            print(f"平均响应时间: {avg_time:.0f} ms")
            print(f"最快响应时间: {min_time:.0f} ms")
            print(f"最慢响应时间: {max_time:.0f} ms")

        print(f"\n吞吐量: {total_users / total_time:.2f} 用户/秒")

        # 错误统计
        if failed_users > 0:
            print(f"\n错误统计:")
            error_counts = {}
            for result in self.results:
                if not result["success"]:
                    error = result["error"] or "未知错误"
                    error_counts[error] = error_counts.get(error, 0) + 1

            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {count}x: {error}")

        # 性能评估
        print(f"\n性能评估:")
        if success_rate >= 90:
            print("✅ 优秀 - 系统能够稳定处理50个并发用户")
        elif success_rate >= 75:
            print("✅ 良好 - 系统基本能处理50个并发用户，有少量失败")
        elif success_rate >= 50:
            print("⚠️  一般 - 系统在高并发下出现较多问题，需要优化")
        else:
            print("❌ 较差 - 系统无法稳定处理50个并发用户，急需优化")

        # 建议
        print(f"\n改进建议:")
        if success_rate < 90:
            print("• 检查数据库连接池配置")
            print("• 优化数据库查询性能")
            print("• 考虑添加应用层缓存")

        avg_response_time = sum(r["response_time"] for r in self.results) / len(self.results) if self.results else 0
        if avg_response_time > 5000:  # 5秒
            print("• 平均响应时间较长，建议优化应用逻辑")

        print("• 监控服务器资源使用情况")
        print("• 考虑使用负载均衡和集群部署")

        # 保存详细结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"load_test_results_{timestamp}.json"

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_info": {
                    "url": self.base_url,
                    "users": self.users,
                    "total_time": total_time,
                    "timestamp": timestamp,
                    "success_rate": success_rate
                },
                "detailed_results": self.results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n详细测试结果已保存到: {result_file}")

if __name__ == "__main__":
    print("校友入校登记系统 - 简化并发性能测试")
    print("=" * 50)

    # 运行测试
    test = SimpleLoadTest(
        base_url="https://www.pofeclife.top",
        users=50
    )

    test.run_test()