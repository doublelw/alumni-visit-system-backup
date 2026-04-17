#!/usr/bin/env python3
"""
校友入校登记系统并发性能测试脚本
模拟50个用户同时访问和提交注册
"""

import asyncio
import aiohttp
import time
import json
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import statistics

class PerformanceTest:
    def __init__(self, base_url="https://www.pofeclife.top", concurrent_users=50):
        self.base_url = base_url
        self.concurrent_users = concurrent_users
        self.results = []
        self.errors = []

    def generate_test_user(self, user_id):
        """生成测试用户数据"""
        return {
            "username": f"testuser_{user_id}_{int(time.time())}",
            "password": "test123456",
            "real_name": f"测试用户{user_id}",
            "email": f"test{user_id}_{int(time.time())}@example.com",
            "phone": f"138{random.randint(10000000, 99999999)}",
            "user_type": "alumni",
            "student_id": f"{random.randint(20200001, 20249999)}",
            "graduation_year": str(random.randint(2015, 2023)),
            "major": random.choice(["计算机科学与技术", "软件工程", "电子信息工程", "机械工程", "经济管理"]),
            "class_name": f"{random.randint(1, 10)}班",
            "dining_companions": random.randint(0, 3),  # 0-3人
            "special_dietary_needs": random.choice(["", "素食", "清真", "无特殊需求"]),
            "visit_purpose": random.choice(["返校参观", "师生聚会", "校园活动", "学术交流"]),
            "expected_arrival_time": f"{random.randint(8, 18)}:{random.randint(0, 59):02d}",
            "vehicle_info": random.choice(["", "私家车", "出租车", "公共交通"]),
            "health_declaration": "true",
            "agreement": "true"
        }

    async def test_homepage_access(self, session, user_id):
        """测试首页访问"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/", timeout=10) as response:
                content = await response.text()
                end_time = time.time()

                return {
                    "user_id": user_id,
                    "operation": "homepage_access",
                    "status_code": response.status,
                    "response_time": (end_time - start_time) * 1000,  # 毫秒
                    "success": response.status == 200,
                    "content_length": len(content)
                }
        except Exception as e:
            end_time = time.time()
            error_info = {
                "user_id": user_id,
                "operation": "homepage_access",
                "status_code": 0,
                "response_time": (end_time - start_time) * 1000,
                "success": False,
                "error": str(e)
            }
            self.errors.append(error_info)
            return error_info

    async def test_registration_page(self, session, user_id):
        """测试注册页面访问"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/", timeout=10) as response:
                content = await response.text()
                end_time = time.time()

                return {
                    "user_id": user_id,
                    "operation": "registration_page",
                    "status_code": response.status,
                    "response_time": (end_time - start_time) * 1000,
                    "success": response.status == 200 and "注册" in content,
                    "content_length": len(content)
                }
        except Exception as e:
            end_time = time.time()
            error_info = {
                "user_id": user_id,
                "operation": "registration_page",
                "status_code": 0,
                "response_time": (end_time - start_time) * 1000,
                "success": False,
                "error": str(e)
            }
            self.errors.append(error_info)
            return error_info

    async def test_registration_submit(self, session, user_id):
        """测试注册表单提交"""
        user_data = self.generate_test_user(user_id)
        start_time = time.time()

        try:
            async with session.post(
                f"{self.base_url}/api/register",
                json=user_data,
                timeout=15,
                headers={"Content-Type": "application/json"}
            ) as response:
                content = await response.text()
                end_time = time.time()

                # 尝试解析JSON响应
                try:
                    response_data = json.loads(content)
                    success = response.status == 200 and response_data.get("success", False)
                except:
                    success = response.status == 200

                return {
                    "user_id": user_id,
                    "operation": "registration_submit",
                    "status_code": response.status,
                    "response_time": (end_time - start_time) * 1000,
                    "success": success,
                    "content_length": len(content),
                    "username": user_data["username"]
                }
        except Exception as e:
            end_time = time.time()
            error_info = {
                "user_id": user_id,
                "operation": "registration_submit",
                "status_code": 0,
                "response_time": (end_time - start_time) * 1000,
                "success": False,
                "error": str(e),
                "username": user_data["username"]
            }
            self.errors.append(error_info)
            return error_info

    async def run_user_test(self, session, user_id):
        """为单个用户运行完整的测试流程"""
        print(f"用户 {user_id} 开始测试...")

        # 1. 访问首页
        homepage_result = await self.test_homepage_access(session, user_id)
        await asyncio.sleep(random.uniform(0.1, 0.5))  # 随机延迟

        # 2. 访问注册页面
        registration_page_result = await self.test_registration_page(session, user_id)
        await asyncio.sleep(random.uniform(0.5, 1.5))  # 模拟填写表单时间

        # 3. 提交注册
        registration_submit_result = await self.test_registration_submit(session, user_id)

        return [homepage_result, registration_page_result, registration_submit_result]

    async def run_concurrent_test(self):
        """运行并发测试"""
        print(f"开始并发性能测试：{self.concurrent_users} 个用户")
        print(f"目标网址：{self.base_url}")
        print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)

        # 创建HTTP连接器以限制连接池大小
        connector = aiohttp.TCPConnector(
            limit=self.concurrent_users + 10,
            limit_per_host=self.concurrent_users,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        timeout = aiohttp.ClientTimeout(total=30, connect=10)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 创建并发任务
            tasks = [
                self.run_user_test(session, i + 1)
                for i in range(self.concurrent_users)
            ]

            # 执行所有任务
            start_time = time.time()
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # 收集结果
            for user_results in all_results:
                if isinstance(user_results, list):
                    self.results.extend(user_results)
                else:
                    # 处理异常
                    self.errors.append({
                        "error": str(user_results),
                        "type": "user_test_exception"
                    })

        total_time = end_time - start_time
        self.analyze_results(total_time)

    def analyze_results(self, total_time):
        """分析测试结果"""
        print("\n" + "=" * 60)
        print("性能测试报告")
        print("=" * 60)

        # 总体统计
        total_operations = len(self.results)
        successful_operations = sum(1 for r in self.results if r.get("success", False))
        failed_operations = total_operations - successful_operations
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0

        print(f"总测试时间：{total_time:.2f} 秒")
        print(f"并发用户数：{self.concurrent_users}")
        print(f"总操作数：{total_operations}")
        print(f"成功操作数：{successful_operations}")
        print(f"失败操作数：{failed_operations}")
        print(f"成功率：{success_rate:.2f}%")
        print(f"错误数：{len(self.errors)}")

        # 按操作类型分析
        operations = ["homepage_access", "registration_page", "registration_submit"]

        print("\n" + "-" * 40)
        print("按操作类型分析：")
        print("-" * 40)

        for operation in operations:
            operation_results = [r for r in self.results if r.get("operation") == operation]
            if operation_results:
                response_times = [r["response_time"] for r in operation_results if r.get("success", False)]
                successful_count = sum(1 for r in operation_results if r.get("success", False))

                if response_times:
                    avg_time = statistics.mean(response_times)
                    min_time = min(response_times)
                    max_time = max(response_times)
                    median_time = statistics.median(response_times)
                    p95_time = sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max_time
                else:
                    avg_time = min_time = max_time = median_time = p95_time = 0

                operation_names = {
                    "homepage_access": "首页访问",
                    "registration_page": "注册页面",
                    "registration_submit": "注册提交"
                }

                print(f"{operation_names[operation]}:")
                print(f"  总数：{len(operation_results)}, 成功：{successful_count}, 成功率：{successful_count/len(operation_results)*100:.1f}%")
                print(f"  响应时间 - 平均：{avg_time:.0f}ms, 最小：{min_time:.0f}ms, 最大：{max_time:.0f}ms")
                print(f"  中位数：{median_time:.0f}ms, P95：{p95_time:.0f}ms")

        # 性能指标
        print("\n" + "-" * 40)
        print("性能指标：")
        print("-" * 40)

        all_response_times = [r["response_time"] for r in self.results if r.get("success", False)]
        if all_response_times:
            throughput = len(self.results) / total_time  # 每秒操作数
            print(f"吞吐量：{throughput:.2f} 操作/秒")
            print(f"平均响应时间：{statistics.mean(all_response_times):.0f}ms")
            print(f"最快响应时间：{min(all_response_times):.0f}ms")
            print(f"最慢响应时间：{max(all_response_times):.0f}ms")

        # 错误分析
        if self.errors:
            print("\n" + "-" * 40)
            print("错误详情：")
            print("-" * 40)
            error_types = {}
            for error in self.errors:
                error_key = error.get("error", "Unknown error")[:50]
                error_types[error_key] = error_types.get(error_key, 0) + 1

            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {count}x: {error_type}")

        # 并发性能评估
        print("\n" + "-" * 40)
        print("并发性能评估：")
        print("-" * 40)

        registration_results = [r for r in self.results if r.get("operation") == "registration_submit"]
        successful_registrations = [r for r in registration_results if r.get("success", False)]

        print(f"注册成功率：{len(successful_registrations)}/{len(registration_results)} ({len(successful_registrations)/len(registration_results)*100:.1f}%)")

        if len(successful_registrations) >= self.concurrent_users * 0.8:  # 80%成功率
            print("✅ 系统通过并发测试 - 能够处理50个并发用户")
        elif len(successful_registrations) >= self.concurrent_users * 0.6:  # 60%成功率
            print("⚠️  系统基本通过并发测试 - 建议优化性能")
        else:
            print("❌ 系统未通过并发测试 - 需要性能优化")

        # 推荐改进建议
        print("\n" + "-" * 40)
        print("改进建议：")
        print("-" * 40)

        if len(self.errors) > self.concurrent_users * 0.1:  # 错误率超过10%
            print("• 错误率较高，建议检查服务器日志和错误处理")

        avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        if avg_response_time > 5000:  # 平均响应时间超过5秒
            print("• 平均响应时间较长，建议优化数据库查询和应用逻辑")

        if len(successful_registrations) < len(registration_results) * 0.9:
            print("• 注册成功率偏低，建议检查数据库连接和事务处理")

        print("• 考虑添加缓存机制来提升性能")
        print("• 考虑使用负载均衡来处理更高的并发")
        print("• 监控服务器资源使用情况（CPU、内存、磁盘I/O）")

async def main():
    """主函数"""
    print("校友入校登记系统 - 并发性能测试工具")
    print("=" * 50)

    # 配置测试参数
    BASE_URL = "https://www.pofeclife.top"
    CONCURRENT_USERS = 50

    # 创建测试实例
    test = PerformanceTest(BASE_URL, CONCURRENT_USERS)

    try:
        # 运行测试
        await test.run_concurrent_test()

        # 保存详细结果到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"performance_test_results_{timestamp}.json"

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_config": {
                    "base_url": BASE_URL,
                    "concurrent_users": CONCURRENT_USERS,
                    "timestamp": timestamp
                },
                "results": test.results,
                "errors": test.errors
            }, f, ensure_ascii=False, indent=2)

        print(f"\n详细结果已保存到：{results_file}")

    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试执行出错：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())