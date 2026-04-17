"""
完整的5个用户故事端到端测试 - 包含访问记录创建
"""

import requests
import sqlite3
import sys
import os
import time
from datetime import datetime, timedelta

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def complete_verification_with_confirm(user, user_type, verify_type, time_window_minutes):
    """完整的验证流程：验证 + 确认放行"""
    try:
        # 生成HMAC码
        app = create_app()
        with app.app_context():
            timestamp = int(time.time())
            code = generate_hmac_code(user['phone'], user['password'], timestamp)
            access_code = code[-6:]

        print(f"  Generated code: {access_code} (time window: {time_window_minutes}min)")

        # Step 1: 验证码
        print(f"  [Step 1] Verifying code...")
        verify_response = requests.post(
            f"{BASE_URL}/api/guard/verify",
            json={
                "code": access_code,
                "guard_name": "Test Guard",
                "verify_type": verify_type
            },
            timeout=10
        )

        verify_result = verify_response.json()

        if not verify_result.get('success'):
            print(f"    [FAIL] Verification failed: {verify_result.get('data', {}).get('message', 'Unknown')}")
            return False, None

        print(f"    [OK] Verification successful")

        # Step 2: 确认放行（如果有application_id）
        application_id = verify_result.get('data', {}).get('application_id')
        if application_id:
            print(f"  [Step 2] Confirming entry (application_id: {application_id})...")
            confirm_response = requests.post(
                f"{BASE_URL}/api/guard/confirm",
                json={
                    "application_id": int(application_id),
                    "guard_name": "Test Guard"
                },
                timeout=10
            )

            confirm_result = confirm_response.json()
            if confirm_result.get('success'):
                print(f"    [OK] Confirm successful, visit record created")
                return True, verify_result.get('data', {}).get('user_info', {})
            else:
                print(f"    [FAIL] Confirm failed: {confirm_result}")
                return False, None
        else:
            print(f"  [Step 2] No application_id (direct HMAC verification, no record created)")
            return True, verify_result.get('data', {}).get('user_info', {})

    except Exception as e:
        print(f"    [ERROR] {e}")
        return False, None

def main():
    print_section("Complete E2E Test - All 5 User Stories")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 记录初始访问记录数
    cursor.execute('SELECT COUNT(*) FROM visit_records')
    initial_count = cursor.fetchone()[0]
    print(f"\nInitial visit records count: {initial_count}")

    results = {}

    # Story 1: 校友入校 (Alumni)
    print_section("Story 1: Alumni Visit")

    cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "alumni" LIMIT 1')
    result = cursor.fetchone()
    if result:
        user = {'id': result[0], 'name': result[1], 'phone': result[2], 'password': result[3]}
        print(f"User: {user['name']} ({user['phone']})")

        success, info = complete_verification_with_confirm(user, 'alumni', 'alumni', 3)
        results['Alumni'] = success
    else:
        print("[SKIP] No alumni user found")
        results['Alumni'] = None

    # Story 2: 家长入校 (Parent Visit)
    print_section("Story 2: Parent Visit")

    cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "parent" LIMIT 1')
    result = cursor.fetchone()
    if result:
        user = {'id': result[0], 'name': result[1], 'phone': result[2], 'password': result[3]}
        print(f"User: {user['name']} ({user['phone']})")

        success, info = complete_verification_with_confirm(user, 'parent', 'parent-visit', 3)
        results['Parent'] = success
    else:
        print("[SKIP] No parent user found")
        results['Parent'] = None

    # Story 3: 学生离校 (Student Leave)
    print_section("Story 3: Student Leave")

    cursor.execute('SELECT id, student_name, phone, wechat_password FROM student_leave_applications LIMIT 1')
    result = cursor.fetchone()
    if result:
        user = {'id': result[0], 'name': result[1], 'phone': result[2], 'password': result[3]}
        print(f"Student: {user['name']} ({user['phone']})")

        success, info = complete_verification_with_confirm(user, 'student', 'student-leave', 3)
        results['Student Leave'] = success
    else:
        print("[SKIP] No student leave application found")
        results['Student Leave'] = None

    # Story 4: 访客访问 (Visitor) - 需要先创建申请
    print_section("Story 4: Visitor Visit")

    cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "visitor" LIMIT 1')
    result = cursor.fetchone()
    if result:
        user = {'id': result[0], 'name': result[1], 'phone': result[2], 'password': result[3]}

        # 创建今天的访问申请
        visit_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO visit_applications
            (applicant_id, visit_date, visit_time_start, visit_time_end, visit_purpose, application_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user['id'], visit_date, '09:00', '17:00', '访客测试', 'approved'))
        application_id = cursor.lastrowid

        # 生成访问码
        app = create_app()
        with app.app_context():
            timestamp = int(time.time())
            code = generate_hmac_code(user['phone'], user['password'], timestamp)
            access_code = code[-6:]

        cursor.execute('UPDATE visit_applications SET access_code = ? WHERE id = ?', (access_code, application_id))
        conn.commit()

        print(f"User: {user['name']} ({user['phone']})")
        print(f"Created application {application_id}, code: {access_code}")

        success, info = complete_verification_with_confirm(user, 'visitor', 'visitor', 1440)
        results['Visitor'] = success
    else:
        print("[SKIP] No visitor user found")
        results['Visitor'] = None

    # Story 5: 活动报名 (Event Registration)
    print_section("Story 5: Event Registration")

    cursor.execute('''
        SELECT u.id, u.real_name, u.phone, u.wechat_password
        FROM event_registrations er
        JOIN users u ON er.user_id = u.id
        LIMIT 1
    ''')
    result = cursor.fetchone()
    if result:
        user = {'id': result[0], 'name': result[1], 'phone': result[2], 'password': result[3]}
        print(f"User: {user['name']} ({user['phone']})")

        success, info = complete_verification_with_confirm(user, 'event', 'event-registration', 3)
        results['Event'] = success
    else:
        print("[SKIP] No event registration found")
        results['Event'] = None

    conn.close()

    # 检查最终的访问记录数
    print_section("Final Results")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM visit_records')
    final_count = cursor.fetchone()[0]
    new_records = final_count - initial_count

    print(f"\nInitial visit records: {initial_count}")
    print(f"Final visit records: {final_count}")
    print(f"New visit records created: {new_records}")

    if final_count > 0:
        cursor.execute('''
            SELECT vr.id, u.real_name, va.visit_purpose, vr.gate_name, vr.entry_time
            FROM visit_records vr
            JOIN users u ON vr.user_id = u.id
            LEFT JOIN visit_applications va ON vr.visit_application_id = va.id
            ORDER BY vr.created_at DESC
            LIMIT 5
        ''')
        records = cursor.fetchall()
        print(f"\nLatest visit records:")
        for record in records:
            print(f"  ID={record[0]}, Name={record[1]}, Purpose={record[2]}, Gate={record[3]}, Time={record[4]}")

    conn.close()

    # 测试结果统计
    print(f"\nTest Results:")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for story, success in results.items():
        if success is True:
            print(f"  [PASS] {story}")
        elif success is False:
            print(f"  [FAIL] {story}")
        else:
            print(f"  [SKIP] {story}")

    print(f"\nPass rate: {passed}/{passed+failed+skipped} ({passed*100//(passed+failed+skipped) if passed+failed+skipped > 0 else 0}%)")
    print(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")

    print_section("Final Verdict")
    if failed == 0 and passed >= 3 and new_records > 0:
        print("  [SUCCESS] All critical tests passed!")
        print(f"  {new_records} new visit records created")
        return True
    elif failed > 0:
        print("  [FAIL] Some tests failed")
        return False
    else:
        print("  [WARNING] No new visit records created")
        return False

if __name__ == "__main__":
    print("\nEnsure Flask server is running (python run.py)")
    print("Waiting 3 seconds before starting test...")
    time.sleep(3)

    success = main()

    print("\n" + "=" * 80)
    if success:
        print("  [SUCCESS] Complete E2E test passed")
        print("  System is working correctly with visit records!")
    else:
        print("  [FAIL] Test failed - Check error messages")
    print("=" * 80 + "\n")

    sys.exit(0 if success else 1)
