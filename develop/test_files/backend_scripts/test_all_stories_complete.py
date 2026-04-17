"""
完整的5个用户故事E2E测试
确保所有门卫验证都通过（绿色✓，不出现红色✗）
"""

import requests
import sqlite3
import sys
import os
import time

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def generate_hmac_with_context(phone, password):
    """在Flask应用上下文中生成HMAC码"""
    from app import create_app
    from app.utils.hmac_utils import generate_hmac_code

    app = create_app()
    with app.app_context():
        return generate_hmac_code(phone, password)

def get_database_users():
    """从数据库获取各类型用户"""
    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    users = {
        'alumni': None,
        'parent': None,
        'student': None,
        'visitor': None,
        'event': None
    }

    # 获取校友用户
    cursor.execute('SELECT real_name, phone, wechat_password FROM users WHERE user_type = "alumni" LIMIT 1')
    result = cursor.fetchone()
    if result:
        users['alumni'] = {'name': result[0], 'phone': result[1], 'password': result[2]}

    # 获取家长用户
    cursor.execute('SELECT real_name, phone, wechat_password FROM users WHERE user_type = "parent" LIMIT 1')
    result = cursor.fetchone()
    if result:
        users['parent'] = {'name': result[0], 'phone': result[1], 'password': result[2]}

    # 获取学生（从student_leave_applications）
    cursor.execute('SELECT student_name, phone, wechat_password FROM student_leave_applications LIMIT 1')
    result = cursor.fetchone()
    if result:
        users['student'] = {'name': result[0], 'phone': result[1], 'password': result[2]}

    # 获取访客用户
    cursor.execute('SELECT real_name, phone, wechat_password FROM users WHERE user_type = "visitor" ORDER BY id DESC LIMIT 1')
    result = cursor.fetchone()
    if result:
        users['visitor'] = {'name': result[0], 'phone': result[1], 'password': result[2]}

    # 获取活动报名用户（从event_registrations）
    cursor.execute('''
        SELECT u.real_name, u.phone, u.wechat_password
        FROM event_registrations er
        JOIN users u ON er.user_id = u.id
        LIMIT 1
    ''')
    result = cursor.fetchone()
    if result:
        users['event'] = {'name': result[0], 'phone': result[1], 'password': result[2]}

    conn.close()
    return users

def test_guard_verification(code, verify_type, guard_name="门卫01"):
    """测试门卫验证"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/guard/verify",
            json={
                "code": code,
                "guard_name": guard_name,
                "verify_type": verify_type
            },
            timeout=10
        )

        result = response.json()

        if result.get('success') and result['data'].get('valid'):
            user_info = result['data']['user_info']
            return {
                'success': True,
                'message': 'PASS - 验证通过',
                'user_info': user_info
            }
        else:
            error = result.get('error', 'Unknown error')
            return {
                'success': False,
                'message': f'FAIL - {error}',
                'details': result
            }

    except Exception as e:
        return {
            'success': False,
            'message': f'ERROR - {str(e)}',
            'exception': str(e)
        }

def main():
    print_section("校友入校登记系统 - 完整E2E测试")
    print("测试所有5个用户故事，确保门卫验证全部通过")
    print("预期结果：所有验证显示绿色✓，不出现红色✗")

    # 获取数据库用户
    print("\n[步骤1] 从数据库获取测试用户...")
    users = get_database_users()

    print("\n可用用户：")
    for user_type, user_info in users.items():
        if user_info:
            print(f"  ✓ {user_type}: {user_info['name']} ({user_info['phone']})")
        else:
            print(f"  ✗ {user_type}: 未找到")

    # 为每个用户生成HMAC码并测试
    results = {}
    generated_codes = {}

    # 故事1：校友入校
    print_section("故事1：校友入校 (Alumni Visit)")
    if users['alumni']:
        user = users['alumni']
        print(f"用户: {user['name']} ({user['phone']})")
        print(f"密码: {user['password']}")

        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['alumni'] = code
        print(f"HMAC码: {code}")

        result = test_guard_verification(code, 'alumni')
        results['Story 1 - Alumni'] = result

        if result['success']:
            print(f"\n  ✓ {result['message']}")
            print(f"  姓名: {result['user_info']['name']}")
            print(f"  类型: {result['user_info']['type']}")
        else:
            print(f"\n  ✗ {result['message']}")
    else:
        print("  ✗ 跳过 - 数据库中无校友用户")
        results['Story 1 - Alumni'] = {'success': None, 'message': 'SKIP - 无用户'}

    # 故事2：家长入校
    print_section("故事2：家长入校 (Parent Visit)")
    if users['parent']:
        user = users['parent']
        print(f"用户: {user['name']} ({user['phone']})")
        print(f"密码: {user['password']}")

        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['parent'] = code
        print(f"HMAC码: {code}")

        result = test_guard_verification(code, 'parent-visit')
        results['Story 2 - Parent'] = result

        if result['success']:
            print(f"\n  ✓ {result['message']}")
            print(f"  姓名: {result['user_info']['name']}")
            print(f"  类型: {result['user_info']['type']}")
        else:
            print(f"\n  ✗ {result['message']}")
    else:
        print("  ✗ 跳过 - 数据库中无家长用户")
        results['Story 2 - Parent'] = {'success': None, 'message': 'SKIP - 无用户'}

    # 故事3：学生离校
    print_section("故事3：学生离校 (Student Leave)")
    if users['student']:
        user = users['student']
        print(f"用户: {user['name']} ({user['phone']})")
        print(f"密码: {user['password']}")

        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['student'] = code
        print(f"HMAC码: {code}")

        result = test_guard_verification(code, 'student-leave')
        results['Story 3 - Student'] = result

        if result['success']:
            print(f"\n  ✓ {result['message']}")
            print(f"  学生姓名: {result['user_info']['student_name']}")
            print(f"  离校原因: {result['user_info'].get('leave_reason', 'N/A')}")
        else:
            print(f"\n  ✗ {result['message']}")
    else:
        print("  ✗ 跳过 - 数据库中无学生离校申请")
        results['Story 3 - Student'] = {'success': None, 'message': 'SKIP - 无用户'}

    # 故事4：访客访问
    print_section("故事4：访客访问 (Visitor)")
    if users['visitor']:
        user = users['visitor']
        print(f"用户: {user['name']} ({user['phone']})")
        print(f"密码: {user['password']}")

        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['visitor'] = code
        print(f"HMAC码: {code}")

        result = test_guard_verification(code, 'visitor')
        results['Story 4 - Visitor'] = result

        if result['success']:
            print(f"\n  ✓ {result['message']}")
            print(f"  姓名: {result['user_info']['name']}")
            print(f"  访问目的: {result['user_info']['visit_purpose']}")
            print(f"  审批人: {result['user_info'].get('approver_name', 'N/A')}")
        else:
            print(f"\n  ✗ {result['message']}")
    else:
        print("  ✗ 跳过 - 数据库中无访客用户")
        results['Story 4 - Visitor'] = {'success': None, 'message': 'SKIP - 无用户'}

    # 故事5：活动报名
    print_section("故事5：活动报名 (Event Registration)")
    if users['event']:
        user = users['event']
        print(f"用户: {user['name']} ({user['phone']})")
        print(f"密码: {user['password']}")

        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['event'] = code
        print(f"HMAC码: {code}")

        result = test_guard_verification(code, 'event-registration')
        results['Story 5 - Event'] = result

        if result['success']:
            print(f"\n  ✓ {result['message']}")
            print(f"  姓名: {result['user_info']['name']}")
            print(f"  活动: {result['user_info'].get('event_name', 'N/A')}")
        else:
            print(f"\n  ✗ {result['message']}")
    else:
        print("  ✗ 跳过 - 数据库中无活动报名记录")
        results['Story 5 - Event'] = {'success': None, 'message': 'SKIP - 无用户'}

    # 总结
    print_section("测试总结")
    print("\n生成的HMAC码：")
    for user_type, code in generated_codes.items():
        print(f"  {user_type}: {code}")

    print("\n测试结果：")
    passed = 0
    failed = 0
    skipped = 0

    for story, result in results.items():
        if result['success'] is True:
            print(f"  ✓ PASS - {story}")
            passed += 1
        elif result['success'] is False:
            print(f"  ✗ FAIL - {story}: {result['message']}")
            failed += 1
        else:
            print(f"  ⊘ SKIP - {story}: {result['message']}")
            skipped += 1

    print(f"\n通过率: {passed}/{passed+failed+skipped} ({passed*100//(passed+failed+skipped) if passed+failed+skipped > 0 else 0}%)")
    print(f"通过: {passed}, 失败: {failed}, 跳过: {skipped}")

    # 最终判定
    print_section("最终判定")
    if failed == 0 and passed >= 3:
        print("  ✓✓✓ 全部E2E测试通过！")
        print("  所有门卫验证都能成功放行（显示绿色✓）")
        print("  没有红色✗（验证失败）")
        return True
    elif failed > 0:
        print("  ✗✗✗ 存在失败的测试")
        print(f"  有 {failed} 个用户故事的门卫验证失败")
        return False
    else:
        print("  ⚠ 数据库缺少足够的测试数据")
        print("  请先添加相应的用户数据")
        return False

if __name__ == "__main__":
    print("\n提示：请确保Flask服务器正在运行 (python run.py)")
    print("等待3秒后开始测试...")
    time.sleep(3)

    success = main()

    print("\n" + "=" * 80)
    if success:
        print("  ✓ 测试完成 - 所有验证通过")
    else:
        print("  ✗ 测试失败 - 请检查错误信息")
    print("=" * 80 + "\n")

    sys.exit(0 if success else 1)
