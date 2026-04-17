"""
测试访问记录创建 - 专注于能创建记录的场景
"""

import requests
import sqlite3
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_visitor_flow():
    """测试访客审批流程（创建记录）"""
    print_section("Test 1: Visitor Approval Flow (Creates Record)")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 获取访客用户
    cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "visitor" LIMIT 1')
    result = cursor.fetchone()
    if not result:
        print("[SKIP] No visitor user")
        return None

    user = {'id': result[0], 'name': result[1], 'phone': result[2], 'password': result[3]}
    print(f"Visitor: {user['name']} (ID={user['id']})")

    # 创建今天的访问申请
    visit_date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO visit_applications
        (applicant_id, visit_date, visit_time_start, visit_time_end, visit_purpose, application_status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user['id'], visit_date, '09:00', '17:00', '访客测试', 'approved'))
    application_id = cursor.lastrowid
    print(f"Created application ID: {application_id}")

    # 生成访问码
    app = create_app()
    with app.app_context():
        timestamp = int(time.time())
        code = generate_hmac_code(user['phone'], user['password'], timestamp)
        access_code = code[-6:]

    cursor.execute('UPDATE visit_applications SET access_code = ? WHERE id = ?', (access_code, application_id))
    conn.commit()
    conn.close()

    print(f"Generated access code: {access_code}")

    # 门卫验证
    print(f"\n[Step 1] Guard verification...")
    verify_response = requests.post(
        f"{BASE_URL}/api/guard/verify",
        json={"code": access_code, "guard_name": "Test Guard", "verify_type": "visitor"},
        timeout=10
    )

    verify_result = verify_response.json()
    if not verify_result.get('success'):
        print(f"  [FAIL] Verification failed: {verify_result}")
        return False

    print(f"  [OK] Verification successful")

    application_id = verify_result.get('data', {}).get('application_id')
    print(f"  Application ID: {application_id}")

    # 确认放行
    if application_id:
        print(f"\n[Step 2] Confirm entry...")
        confirm_response = requests.post(
            f"{BASE_URL}/api/guard/confirm",
            json={"application_id": int(application_id), "guard_name": "Test Guard"},
            timeout=10
        )

        confirm_result = confirm_response.json()
        if confirm_result.get('success'):
            print(f"  [OK] Confirm successful")
            return True
        else:
            print(f"  [FAIL] Confirm failed: {confirm_result}")
            return False
    else:
        print(f"  [WARNING] No application_id")
        return False

def test_parent_flow():
    """测试家长访问流程（创建记录）"""
    print_section("Test 2: Parent Visit Flow (Creates Record)")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 获取家长用户
    cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "parent" LIMIT 1')
    result = cursor.fetchone()
    if not result:
        print("[SKIP] No parent user")
        return None

    user = {'id': result[0], 'name': result[1], 'phone': result[2], 'password': result[3]}
    print(f"Parent: {user['name']} (ID={user['id']})")

    # 创建今天的访问申请
    visit_date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO visit_applications
        (applicant_id, visit_date, visit_time_start, visit_time_end, visit_purpose, application_status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user['id'], visit_date, '09:00', '17:00', '家长探望', 'approved'))
    application_id = cursor.lastrowid
    print(f"Created application ID: {application_id}")

    # 生成访问码
    app = create_app()
    with app.app_context():
        timestamp = int(time.time())
        code = generate_hmac_code(user['phone'], user['password'], timestamp)
        access_code = code[-6:]

    cursor.execute('UPDATE visit_applications SET access_code = ? WHERE id = ?', (access_code, application_id))
    conn.commit()
    conn.close()

    print(f"Generated access code: {access_code}")

    # 门卫验证
    print(f"\n[Step 1] Guard verification...")
    verify_response = requests.post(
        f"{BASE_URL}/api/guard/verify",
        json={"code": access_code, "guard_name": "Test Guard", "verify_type": "visitor"},
        timeout=10
    )

    verify_result = verify_response.json()
    if not verify_result.get('success'):
        print(f"  [FAIL] Verification failed: {verify_result}")
        return False

    print(f"  [OK] Verification successful")

    application_id = verify_result.get('data', {}).get('application_id')
    print(f"  Application ID: {application_id}")

    # 确认放行
    if application_id:
        print(f"\n[Step 2] Confirm entry...")
        confirm_response = requests.post(
            f"{BASE_URL}/api/guard/confirm",
            json={"application_id": int(application_id), "guard_name": "Test Guard"},
            timeout=10
        )

        confirm_result = confirm_response.json()
        if confirm_result.get('success'):
            print(f"  [OK] Confirm successful")
            return True
        else:
            print(f"  [FAIL] Confirm failed: {confirm_result}")
            return False
    else:
        print(f"  [WARNING] No application_id")
        return False

def main():
    print_section("Visit Records Creation Test")

    # 记录初始记录数
    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM visit_records')
    initial_count = cursor.fetchone()[0]
    conn.close()

    print(f"\nInitial visit records: {initial_count}")

    results = {}

    # Test 1: 访客流程
    result = test_visitor_flow()
    results['Visitor'] = result

    # Test 2: 家长流程
    result = test_parent_flow()
    results['Parent'] = result

    # 检查最终记录数
    print_section("Final Results")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM visit_records')
    final_count = cursor.fetchone()[0]
    new_records = final_count - initial_count

    print(f"\nInitial visit records: {initial_count}")
    print(f"Final visit records: {final_count}")
    print(f"New records created: {new_records}")

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

    # 结果统计
    print(f"\nTest Results:")
    for test, result in results.items():
        if result is True:
            print(f"  [PASS] {test}")
        elif result is False:
            print(f"  [FAIL] {test}")
        else:
            print(f"  [SKIP] {test}")

    print_section("Verdict")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)

    if failed == 0 and passed >= 1 and new_records >= 2:
        print("  [SUCCESS] Tests passed!")
        print(f"  {new_records} new visit records created")
        print("  System is working correctly!")
        return True
    else:
        print("  [FAIL] Some tests failed or no records created")
        return False

if __name__ == "__main__":
    print("\nEnsure Flask server is running (python run.py)")
    print("Waiting 3 seconds...")
    time.sleep(3)

    success = main()

    print("\n" + "=" * 80)
    if success:
        print("  [SUCCESS] Visit records are being created correctly!")
    else:
        print("  [FAIL] Something went wrong")
    print("=" * 80 + "\n")

    sys.exit(0 if success else 1)
