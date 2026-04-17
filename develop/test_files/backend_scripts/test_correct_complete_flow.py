"""
正确的完整流程测试 - 确保使用同一个用户
"""

import requests
import sqlite3
import sys
import os
import time

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def main():
    print_section("Correct Complete Flow Test - Same User Throughout")

    # Step 1: 获取校友用户
    print("\n[Step 1] Get alumni user from database")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "alumni" LIMIT 1')
    result = cursor.fetchone()
    conn.close()

    if not result:
        print("[ERROR] No alumni user in database")
        return False

    alumni = {
        'id': result[0],
        'name': result[1],
        'phone': result[2],
        'password': result[3]
    }

    print(f"  Alumni user: {alumni['name']} (ID={alumni['id']})")
    print(f"  Phone: {alumni['phone']}")
    print(f"  Password: {alumni['password']}")

    # Step 2: 创建访问申请
    print_section("Step 2: Create Visit Application")

    from datetime import datetime, timedelta
    visit_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    application_data = {
        "applicant_id": alumni['id'],
        "visit_date": visit_date,
        "visit_purpose": "测试访问",
        "vehicle_info": "",
        "companion_count": 0,
        "companion_names": ""
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/visits/applications",
            json=application_data,
            timeout=10
        )

        result = response.json()
        if result.get('success') or result.get('application_id'):
            application_id = result.get('application_id') or result.get('id')
            print(f"  [OK] Application created successfully")
            print(f"  Application ID: {application_id}")
        else:
            print(f"  [FAIL] Failed to create application: {result}")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

    # Step 3: 审批申请并生成访问码
    print_section("Step 3: Approve Application & Generate Access Code")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 审批
    cursor.execute('''
        UPDATE visit_applications
        SET application_status = 'approved',
            approver_id = 1,
            approval_time = datetime('now')
        WHERE id = ?
    ''', (application_id,))

    # 生成HMAC码
    timestamp = int(time.time())
    hmac_full = generate_hmac_code(alumni['phone'], alumni['password'], timestamp)
    access_code = hmac_full[-6:]  # 取后6位

    print(f"  Current timestamp: {timestamp}")
    print(f"  Full HMAC: {hmac_full}")
    print(f"  Access code (last 6 digits): {access_code}")

    # 更新访问码
    cursor.execute('UPDATE visit_applications SET access_code = ? WHERE id = ?', (access_code, application_id))
    conn.commit()
    conn.close()

    print(f"  [OK] Application approved and access code generated")
    print(f"  Application {application_id} status: approved")
    print(f"  Access code: {access_code}")

    # Step 4: 门卫验证
    print_section("Step 4: Guard Verification")

    print(f"\n[4.1] Verify access code: {access_code}")
    print(f"  Using verify_type: 'alumni'")
    print(f"  Time since generation: {int(time.time()) - timestamp}s")

    try:
        verify_response = requests.post(
            f"{BASE_URL}/api/guard/verify",
            json={
                "code": access_code,
                "guard_name": "Test Guard",
                "verify_type": "alumni"
            },
            timeout=10
        )

        verify_result = verify_response.json()
        print(f"\n  Verification response:")
        print(f"    success: {verify_result.get('success')}")
        print(f"    data: {verify_result.get('data')}")

        if not verify_result.get('success'):
            print(f"\n  [FAIL] Verification failed!")
            print(f"  Message: {verify_result.get('data', {}).get('message', 'Unknown error')}")

            # 详细诊断
            print(f"\n  [DIAGNOSIS] Why did verification fail?")
            print(f"    Access code: {access_code}")
            print(f"    User: {alumni['name']} (ID={alumni['id']})")
            print(f"    Phone: {alumni['password']}")
            print(f"    Time elapsed: {int(time.time()) - timestamp}s")

            # 手动重新生成一个码测试
            app = create_app()
            with app.app_context():
                test_code = generate_hmac_code(alumni['phone'], alumni['password'])
                print(f"    Freshly generated code: {test_code}")
                print(f"    Match? {test_code == access_code}")

            return False

        print(f"\n  [OK] Verification successful!")

        user_info = verify_result['data'].get('user_info', {})
        print(f"    User name: {user_info.get('name')}")
        print(f"    User type: {user_info.get('type')}")

        returned_app_id = verify_result['data'].get('application_id')
        print(f"    Application ID: {returned_app_id}")

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

    # Step 5: 确认放行
    print_section("Step 5: Confirm Entry")

    if returned_app_id:
        print(f"\n[5.1] Click confirm button for application {returned_app_id}")

        try:
            confirm_response = requests.post(
                f"{BASE_URL}/api/guard/confirm",
                json={
                    "application_id": int(returned_app_id),
                    "guard_name": "Test Guard"
                },
                timeout=10
            )

            confirm_result = confirm_response.json()
            print(f"\n  Confirm response:")
            print(f"    success: {confirm_result.get('success')}")
            print(f"    message: {confirm_result.get('message', 'N/A')}")

            if confirm_result.get('success'):
                print(f"\n  [OK] Confirm successful! Visit record should be created")
            else:
                print(f"\n  [FAIL] Confirm failed: {confirm_result}")
                return False

        except Exception as e:
            print(f"  [ERROR] {e}")
            return False
    else:
        print(f"\n  [WARNING] No application_id returned, cannot confirm")
        return False

    # Step 6: 验证访问记录已创建
    print_section("Step 6: Verify Visit Record Created")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM visit_records')
    count = cursor.fetchone()[0]
    print(f"\n  Total visit records: {count}")

    if count > 0:
        cursor.execute('''
            SELECT vr.id, u.real_name, vr.visit_date, vr.visit_purpose,
                   vr.guard_name, vr.entry_time
            FROM visit_records vr
            JOIN users u ON vr.user_id = u.id
            ORDER BY vr.created_at DESC
            LIMIT 3
        ''')
        records = cursor.fetchall()
        print(f"\n  Latest {len(records)} visit records:")
        for record in records:
            print(f"    ID={record[0]}, Name={record[1]}, Date={record[2]}, " +
                  f"Purpose={record[3]}, Guard={record[4]}, Entry={record[5]}")

        conn.close()

        print_section("TEST PASSED")
        print("  Complete flow successful!")
        print("  1. Created application for alumni user")
        print("  2. Approved application and generated HMAC code")
        print("  3. Guard verified code successfully")
        print("  4. Guard confirmed entry, visit record created")
        print("=" * 80)
        return True
    else:
        conn.close()
        print(f"\n  [FAIL] No visit records found!")
        print_section("TEST FAILED")
        return False

if __name__ == "__main__":
    print("\nHint: Make sure Flask server is running (python run.py)")
    print("Waiting 3 seconds before starting test...")
    time.sleep(3)

    success = main()

    print("\n" + "=" * 80)
    if success:
        print("  [SUCCESS] Complete test passed - Visit records created")
    else:
        print("  [FAIL] Test failed - Check error messages above")
    print("=" * 80 + "\n")

    sys.exit(0 if success else 1)
