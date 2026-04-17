"""
完整的门卫验证流程测试
包括：1) 验证码  2) 确认放行（创建访问记录）
"""

import requests
import sqlite3
import sys
import os

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

def complete_guard_verification(code, verify_type, guard_name="门卫01"):
    """
    完整的门卫验证流程：
    1. 验证码
    2. 如果验证成功且有application_id，则确认放行（创建访问记录）
    """
    try:
        # Step 1: 验证码
        print(f"\n  [步骤1] 验证码: {code}")
        verify_response = requests.post(
            f"{BASE_URL}/api/guard/verify",
            json={
                "code": code,
                "guard_name": guard_name,
                "verify_type": verify_type
            },
            timeout=10
        )

        verify_result = verify_response.json()

        if not verify_result.get('success'):
            print(f"  ✗ 验证失败: {verify_result.get('error', 'Unknown')}")
            return False, None

        print(f"  ✓ 验证通过")
        user_info = verify_result['data'].get('user_info', {})
        print(f"  用户: {user_info.get('name', 'N/A')}")
        print(f"  类型: {user_info.get('type', 'N/A')}")

        # Step 2: 如果有application_id，则确认放行
        application_id = verify_result['data'].get('application_id')
        if application_id:
            print(f"\n  [步骤2] 确认放行 (application_id: {application_id})")
            confirm_response = requests.post(
                f"{BASE_URL}/api/guard/confirm",
                json={
                    "application_id": application_id,
                    "guard_name": guard_name
                },
                timeout=10
            )

            confirm_result = confirm_response.json()
            if confirm_result.get('success'):
                print(f"  ✓ 放行确认成功，访问记录已创建")
                return True, user_info
            else:
                print(f"  ✗ 放行确认失败: {confirm_result.get('error', 'Unknown')}")
                return False, user_info
        else:
            print(f"\n  [步骤2] 无需确认放行（校友类型的码不需要创建访问记录）")
            return True, user_info

    except Exception as e:
        print(f"  ✗ 异常: {str(e)}")
        return False, None

def check_visit_records():
    """检查数据库中的访问记录数"""
    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM visit_records')
    count = cursor.fetchone()[0]

    conn.close()
    return count

def main():
    print_section("完整门卫验证流程测试")
    print("包括验证码 + 确认放行（创建访问记录）")

    # 记录初始访问记录数
    initial_count = check_visit_records()
    print(f"\n初始访问记录数: {initial_count}")

    # 获取数据库用户
    print("\n[步骤1] 从数据库获取测试用户...")
    users = get_database_users()

    print("\n可用用户:")
    for user_type, user_info in users.items():
        if user_info:
            print(f"  ✓ {user_type}: {user_info['name']} ({user_info['phone']})")
        else:
            print(f"  ✗ {user_type}: 未找到")

    # 测试每个用户故事
    results = {}
    generated_codes = {}

    # 故事1：校友入校
    print_section("故事1：校友入校 (Alumni Visit)")
    if users['alumni']:
        user = users['alumni']
        print(f"用户: {user['name']} ({user['phone']})")
        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['alumni'] = code
        print(f"HMAC码: {code}")

        success, info = complete_guard_verification(code, 'alumni')
        results['Story 1 - Alumni'] = success
    else:
        print("  ✗ 跳过 - 数据库中无校友用户")
        results['Story 1 - Alumni'] = None

    # 故事2：家长入校
    print_section("故事2：家长入校 (Parent Visit)")
    if users['parent']:
        user = users['parent']
        print(f"用户: {user['name']} ({user['phone']})")
        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['parent'] = code
        print(f"HMAC码: {code}")

        success, info = complete_guard_verification(code, 'parent-visit')
        results['Story 2 - Parent'] = success
    else:
        print("  ✗ 跳过 - 数据库中无家长用户")
        results['Story 2 - Parent'] = None

    # 故事3：学生离校
    print_section("故事3：学生离校 (Student Leave)")
    if users['student']:
        user = users['student']
        print(f"用户: {user['name']} ({user['phone']})")
        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['student'] = code
        print(f"HMAC码: {code}")

        success, info = complete_guard_verification(code, 'student-leave')
        results['Story 3 - Student'] = success
    else:
        print("  ✗ 跳过 - 数据库中无学生离校申请")
        results['Story 3 - Student'] = None

    # 故事4：访客访问
    print_section("故事4：访客访问 (Visitor)")
    if users['visitor']:
        user = users['visitor']
        print(f"用户: {user['name']} ({user['phone']})")
        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['visitor'] = code
        print(f"HMAC码: {code}")

        success, info = complete_guard_verification(code, 'visitor')
        results['Story 4 - Visitor'] = success
    else:
        print("  ✗ 跳过 - 数据库中无访客用户")
        results['Story 4 - Visitor'] = None

    # 故事5：活动报名
    print_section("故事5：活动报名 (Event Registration)")
    if users['event']:
        user = users['event']
        print(f"用户: {user['name']} ({user['phone']})")
        code = generate_hmac_with_context(user['phone'], user['password'])
        generated_codes['event'] = code
        print(f"HMAC码: {code}")

        success, info = complete_guard_verification(code, 'event-registration')
        results['Story 5 - Event'] = success
    else:
        print("  ✗ 跳过 - 数据库中无活动报名记录")
        results['Story 5 - Event'] = None

    # 检查最终的访问记录数
    final_count = check_visit_records()

    # 总结
    print_section("测试总结")
    print(f"\n初始访问记录数: {initial_count}")
    print(f"最终访问记录数: {final_count}")
    print(f"新增访问记录数: {final_count - initial_count}")

    print("\n测试结果:")
    passed = 0
    failed = 0
    skipped = 0

    for story, success in results.items():
        if success is True:
            print(f"  ✓ PASS - {story}")
            passed += 1
        elif success is False:
            print(f"  ✗ FAIL - {story}")
            failed += 1
        else:
            print(f"  ⊘ SKIP - {story}")
            skipped += 1

    print(f"\n通过率: {passed}/{passed+failed+skipped} ({passed*100//(passed+failed+skipped) if passed+failed+skipped > 0 else 0}%)")
    print(f"通过: {passed}, 失败: {failed}, 跳过: {skipped}")

    # 最终判定
    print_section("最终判定")
    if failed == 0 and passed >= 3 and final_count > initial_count:
        print("  ✓✓✓ 测试通过！")
        print(f"  所有验证通过，访问记录已创建（新增{final_count - initial_count}条）")
        return True
    elif failed > 0:
        print("  ✗✗✗ 存在失败的测试")
        return False
    else:
        print("  ⚠ 警告：没有创建访问记录")
        print("  可能原因：验证接口返回了数据，但没有application_id用于confirm接口")
        return False

if __name__ == "__main__":
    print("\n提示：请确保Flask服务器正在运行 (python run.py)")
    print("等待3秒后开始测试...")
    import time
    time.sleep(3)

    success = main()

    print("\n" + "=" * 80)
    if success:
        print("  ✓ 测试完成 - 访问记录已创建")
    else:
        print("  ✗ 测试失败 - 请检查错误信息")
    print("=" * 80 + "\n")

    sys.exit(0 if success else 1)
