#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校友入校登记系统 API 自动化测试套件
完整的API端点测试，包含认证和业务流程测试
"""

import requests
import json
import time
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class APITestSuite:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.test_users = {}
        self.tokens = {}

    def log_test(self, test_name: str, method: str, url: str,
                 status_code: int, expected_code: int, success: bool,
                 response_data: dict = None, error_msg: str = None):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'method': method,
            'url': url,
            'status_code': status_code,
            'expected_code': expected_code,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data,
            'error_msg': error_msg
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} - {method} {url} ({status_code})")
        if error_msg:
            print(f"    Error: {error_msg}")

    def make_request(self, method: str, endpoint: str, data: dict = None,
                    headers: dict = None, expected_code: int = 200) -> requests.Response:
        """发送HTTP请求并记录结果"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=data)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            success = response.status_code == expected_code
            try:
                response_data = response.json()
            except:
                response_data = response.text

            self.log_test(
                test_name=f"{method} {endpoint}",
                method=method,
                url=url,
                status_code=response.status_code,
                expected_code=expected_code,
                success=success,
                response_data=response_data,
                error_msg=response_data if not success else None
            )

            return response

        except Exception as e:
            self.log_test(
                test_name=f"{method} {endpoint}",
                method=method,
                url=url,
                status_code=0,
                expected_code=expected_code,
                success=False,
                error_msg=str(e)
            )
            raise

    def generate_random_user(self, user_type: str = "alumni") -> Dict:
        """生成随机测试用户数据"""
        timestamp = int(time.time())
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

        if user_type == "alumni":
            return {
                'username': f'test_alumni_{timestamp}_{random_str}',
                'password': 'Test123456',
                'confirmPassword': 'Test123456',
                'realName': f'测试校友{random_str}',
                'email': f'test{timestamp}@example.com',
                'phone': f'1{random.randint(300000000, 899999999)}',
                'idCard': f'11010119{random.randint(800000000, 999999999)}X',
                'graduationYear': str(random.randint(2000, 2020)),
                'classNumber': f'计算机{random.randint(1, 5)}班',
                'department': '计算机学院',
                'major': '计算机科学与技术',
                'classTeacher': f'王老师{random_str}',
                'contactTeacher': '未指定',
                'contactTeacherPhone': '',
                'currentCity': '北京市',
                'workUnit': f'测试公司{random_str}',
                'position': '软件工程师',
                'emergencyContact': f'紧急联系人{random_str}',
                'emergencyPhone': f'1{random.randint(300000000, 899999999)}',
                'agreeTerms': True
            }
        elif user_type == "teacher":
            return {
                'username': f'test_teacher_{timestamp}_{random_str}',
                'password': 'Test123456',
                'realName': f'测试教师{random_str}',
                'email': f'teacher{timestamp}@example.com',
                'phone': f'1{random.randint(300000000, 899999999)}',
                'user_type': 'teacher'
            }
        elif user_type == "security":
            return {
                'username': f'test_security_{timestamp}_{random_str}',
                'password': 'Test123456',
                'realName': f'测试保安{random_str}',
                'email': f'security{timestamp}@example.com',
                'phone': f'1{random.randint(300000000, 899999999)}',
                'user_type': 'security'
            }

    def test_health_endpoints(self):
        """测试健康检查端点"""
        print("\n🔍 Testing Health Endpoints")
        print("=" * 50)

        # 测试基本健康检查
        self.make_request('GET', '/health', expected_code=200)

    def test_auth_endpoints(self):
        """测试认证相关API"""
        print("\n🔐 Testing Authentication Endpoints")
        print("=" * 50)

        # 测试用户注册
        alumni_user = self.generate_random_user('alumni')
        response = self.make_request('POST', '/api/auth/register', alumni_user, expected_code=201)
        if response.status_code == 201:
            self.test_users['alumni'] = alumni_user

        # 测试重复注册
        self.make_request('POST', '/api/auth/register', alumni_user, expected_code=400)

        # 测试登录
        login_data = {
            'username': alumni_user['username'],
            'password': alumni_user['password']
        }
        response = self.make_request('POST', '/api/auth/login', login_data, expected_code=200)
        if response.status_code == 200:
            token_data = response.json()
            self.tokens['alumni'] = token_data.get('access_token')

        # 测试错误密码登录
        wrong_login = {
            'username': alumni_user['username'],
            'password': 'wrongpassword'
        }
        self.make_request('POST', '/api/auth/login', wrong_login, expected_code=401)

        # 测试不存在的用户登录
        fake_login = {
            'username': 'nonexistentuser',
            'password': 'password'
        }
        self.make_request('POST', '/api/auth/login', fake_login, expected_code=401)

        # 测试获取用户信息（需要认证）
        if self.tokens.get('alumni'):
            headers = {'Authorization': f'Bearer {self.tokens["alumni"]}'}
            self.make_request('GET', '/api/auth/profile', headers=headers, expected_code=200)

        # 测试修改密码（需要认证）
        if self.tokens.get('alumni'):
            headers = {'Authorization': f'Bearer {self.tokens["alumni"]}'}
            password_data = {
                'old_password': alumni_user['password'],
                'new_password': 'NewTest123456'
            }
            self.make_request('POST', '/api/auth/change-password', password_data, headers=headers, expected_code=200)

    def test_visit_endpoints(self):
        """测试访问申请相关API"""
        print("\n📅 Testing Visit Application Endpoints")
        print("=" * 50)

        if not self.tokens.get('alumni'):
            print("⚠️  No authenticated alumni user, skipping visit tests")
            return

        headers = {'Authorization': f'Bearer {self.tokens["alumni"]}'}

        # 测试创建访问申请
        visit_data = {
            'visitDate': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'visitTimeStart': '09:00',
            'visitTimeEnd': '17:00',
            'visitPurpose': '拜访老师',
            'targetPerson': '王老师',
            'targetDepartment': '计算机学院',
            'notes': '测试访问申请'
        }
        response = self.make_request('POST', '/api/visits/applications', visit_data, headers=headers, expected_code=201)

        # 测试获取访问申请列表
        self.make_request('GET', '/api/visits/applications', headers=headers, expected_code=200)

        # 测试获取访问记录
        self.make_request('GET', '/api/visits/records', headers=headers, expected_code=200)

    def test_vehicle_endpoints(self):
        """测试车辆管理相关API"""
        print("\n🚗 Testing Vehicle Management Endpoints")
        print("=" * 50)

        if not self.tokens.get('alumni'):
            print("⚠️  No authenticated alumni user, skipping vehicle tests")
            return

        headers = {'Authorization': f'Bearer {self.tokens["alumni"]}'}

        # 测试添加车辆
        vehicle_data = {
            'plateNumber': f'京A{random.randint(10000, 99999)}',
            'vehicleType': '轿车',
            'vehicleColor': '白色',
            'vehicleBrand': '大众'
        }
        response = self.make_request('POST', '/api/vehicles/', vehicle_data, headers=headers, expected_code=201)

        # 测试获取车辆列表
        self.make_request('GET', '/api/vehicles/', headers=headers, expected_code=200)

    def test_face_endpoints(self):
        """测试人脸识别相关API"""
        print("\n👤 Testing Face Recognition Endpoints")
        print("=" * 50)

        if not self.tokens.get('alumni'):
            print("⚠️  No authenticated alumni user, skipping face tests")
            return

        headers = {'Authorization': f'Bearer {self.tokens["alumni"]}'}

        # 测试获取人脸注册状态
        self.make_request('GET', '/api/faces/status', headers=headers, expected_code=200)

        # 测试人脸验证（通常需要实际的人脸数据）
        verify_data = {
            'faceImage': 'base64_encoded_image_data_placeholder'
        }
        self.make_request('POST', '/api/faces/verify', verify_data, headers=headers, expected_code=400)  # 预期会失败，因为数据无效

    def test_admin_endpoints(self):
        """测试管理员相关API"""
        print("\n👨‍💼 Testing Admin Endpoints")
        print("=" * 50)

        # 创建管理员用户进行测试
        admin_user = self.generate_random_user('teacher')
        admin_user['user_type'] = 'admin'

        # 直接在数据库中创建管理员用户（如果可能）
        # 或者使用已有的管理员账户

        # 测试获取仪表板数据（需要管理员权限）
        admin_headers = {'Authorization': f'Bearer {self.tokens.get("alumni", "")}'}
        response = self.make_request('GET', '/api/admin/dashboard', headers=admin_headers, expected_code=403)  # 普通用户无权限

        # 测试获取用户列表（需要管理员权限）
        self.make_request('GET', '/api/admin/users', headers=admin_headers, expected_code=403)

        # 测试获取统计数据（需要管理员权限）
        self.make_request('GET', '/api/admin/statistics', headers=admin_headers, expected_code=403)

    def test_calendar_endpoints(self):
        """测试日历相关API"""
        print("\n📆 Testing Calendar Endpoints")
        print("=" * 50)

        # 测试获取公开日历
        self.make_request('GET', '/api/public/calendar', expected_code=200)

        # 测试获取学校日历（需要认证）
        if self.tokens.get('alumni'):
            headers = {'Authorization': f'Bearer {self.tokens["alumni"]}'}
            self.make_request('GET', '/api/calendar', headers=headers, expected_code=200)

    def test_qr_code_endpoints(self):
        """测试二维码相关API"""
        print("\n📱 Testing QR Code Endpoints")
        print("=" * 50)

        if self.tokens.get('alumni'):
            headers = {'Authorization': f'Bearer {self.tokens["alumni"]}'}

            # 测试生成二维码
            self.make_request('POST', '/api/qr-codes/generate', headers=headers, expected_code=200)

            # 测试验证二维码
            qr_data = {'qrData': 'test_qr_code_placeholder'}
            self.make_request('POST', '/api/qr-codes/verify', qr_data, expected_code=400)  # 预期会失败

    def test_security_portal_endpoints(self):
        """测试保安门户相关API"""
        print("\n🔒 Testing Security Portal Endpoints")
        print("=" * 50)

        if self.tokens.get('alumni'):
            headers = {'Authorization': f'Bearer {self.tokens["alumni"]}'}

            # 测试保安签到（需要保安权限）
            self.make_request('POST', '/api/security-portal/check-in', headers=headers, expected_code=403)

            # 测试获取访客信息
            self.make_request('GET', '/api/security-portal/visitors', headers=headers, expected_code=403)

    def test_error_handling(self):
        """测试错误处理"""
        print("\n⚠️  Testing Error Handling")
        print("=" * 50)

        # 测试不存在的端点
        self.make_request('GET', '/api/nonexistent', expected_code=404)

        # 测试无效的JSON数据
        self.make_request('POST', '/api/auth/login', '{"invalid": json}', expected_code=400)

        # 测试缺少必需字段
        self.make_request('POST', '/api/auth/login', {}, expected_code=400)

        # 测试无效的JWT token
        invalid_headers = {'Authorization': 'Bearer invalid_token'}
        self.make_request('GET', '/api/auth/profile', headers=invalid_headers, expected_code=422)

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 Starting API Test Suite")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Start Time: {datetime.now().isoformat()}")
        print("=" * 60)

        try:
            # 按逻辑顺序运行测试
            self.test_health_endpoints()
            self.test_auth_endpoints()
            self.test_visit_endpoints()
            self.test_vehicle_endpoints()
            self.test_face_endpoints()
            self.test_admin_endpoints()
            self.test_calendar_endpoints()
            self.test_qr_code_endpoints()
            self.test_security_portal_endpoints()
            self.test_error_handling()

        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")

        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['error_msg']}")

        print(f"\nEnd Time: {datetime.now().isoformat()}")
        print("=" * 60)

        # 生成详细的测试报告文件
        self.generate_report()

    def generate_report(self):
        """生成详细的测试报告"""
        report_data = {
            'test_suite': '校友入校登记系统 API 测试',
            'base_url': self.base_url,
            'start_time': self.test_results[0]['timestamp'] if self.test_results else datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results if r['success']]),
                'failed_tests': len([r for r in self.test_results if not r['success']]),
                'success_rate': len([r for r in self.test_results if r['success']]) / len(self.test_results) * 100 if self.test_results else 0
            },
            'test_results': self.test_results,
            'test_users': self.test_users,
            'environment_info': {
                'user_agent': self.session.headers.get('User-Agent', 'Default'),
                'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}"
            }
        }

        report_filename = f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Detailed report saved to: {report_filename}")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='校友入校登记系统 API 测试套件')
    parser.add_argument('--url', default='http://localhost:5000',
                       help='Base URL for the API (default: http://localhost:5000)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout in seconds (default: 30)')

    args = parser.parse_args()

    # 设置会话超时
    requests.adapters.HTTPAdapter(max_retries=3)

    # 创建测试套件并运行
    test_suite = APITestSuite(base_url=args.url)

    try:
        test_suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")

if __name__ == '__main__':
    main()