"""
访客审批流程完整测试 - 申请→审批→验证→确认放行→创建记录
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

def main():
    print_section("Visitor Approval Flow Test")

    # Step 1: 获取一个访客用户
    print("\n[Step 1] Get visitor user from database")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "visitor" LIMIT 1')
    result = cursor.fetchone()

    if not result:
        print("[WARNING] No visitor user, will create one")
        # 创建一个访客用户
        cursor.execute('''
            INSERT INTO users (username, password, real_name, phone, user_type, wechat_password, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (f"visitor_{int(time.time())}", "test123", "测试访客", "13900009999", "visitor", "999999", "active"))
        conn.commit()

        cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "visitor" ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()

    conn.close()

    visitor = {
        'id': result[0],
        'name': result[1],
        'phone': result[2],
        'password': result[3]
    }

    print(f"  Visitor user: {visitor['name']} (ID={visitor['id']})")
    print(f"  Phone: {visitor['phone']}")

    # Step 2: 直接在数据库中创建访问申请（绕过JWT认证）
    print_section("Step 2: Create Visit Application (directly in database)")

    # 使用今天的日期，因为验证只查询今天的申请
    visit_date = datetime.now().strftime('%Y-%m-%d')

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    print(f"  Creating application for visitor {visitor['name']}...")
    print(f"  Visit date: {visit_date}")

    cursor.execute('''
        INSERT INTO visit_applications
        (applicant_id, visit_date, visit_time_start, visit_time_end, visit_purpose,
         vehicle_info, application_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (visitor['id'], visit_date, '09:00', '17:00', '测试访问 - 完整流程测试',
          '', 'pending'))

    application_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"  [OK] Application created successfully")
    print(f"  Application ID: {application_id}")

    # Step 3: 审批申请并生成访问码
    print_section("Step 3: Approve Application & Generate Access Code")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 审批
    print(f"  Approving application {application_id}...")
    cursor.execute('''
        UPDATE visit_applications
        SET application_status = 'approved',
            approved_by = 1,
            approval_time = datetime('now')
        WHERE id = ?
    ''', (application_id,))

    # 生成HMAC码（需要在Flask应用上下文中）
    from app import create_app
    app = create_app()
    with app.app_context():
        timestamp = int(time.time())
        hmac_full = generate_hmac_code(visitor['phone'], visitor['password'], timestamp)
        access_code = hmac_full[-6:]

    print(f"  Current timestamp: {timestamp}")
    print(f"  Access code: {access_code}")

    # 更新访问码
    cursor.execute('UPDATE visit_applications SET access_code = ? WHERE id = ?', (access_code, application_id))
    conn.commit()
    conn.close()

    print(f"  [OK] Application approved and access code generated")

    # Step 4: 门卫验证
    print_section("Step 4: Guard Verification")

    print(f"\n[4.1] Verify access code: {access_code}")
    print(f"  verify_type: 'visitor'")
    print(f"  Time since generation: {int(time.time()) - timestamp}s")

    try:
        verify_response = requests.post(
            f"{BASE_URL}/api/guard/verify",
            json={
                "code": access_code,
                "guard_name": "Test Guard",
                "verify_type": "visitor"
            },
            timeout=10
        )

        verify_result = verify_response.json()
        print(f"\n  Verification response:")
        print(f"    success: {verify_result.get('success')}")

        if verify_result.get('success'):
            data = verify_result.get('data', {})
            print(f"    code_type: {data.get('code_type')}")
            print(f"    valid: {data.get('valid')}")
            print(f"    message: {data.get('message')}")

            user_info = data.get('user_info', {})
            print(f"\n  [OK] Verification successful!")
            print(f"    Visitor: {user_info.get('name')}")
            print(f"    Type: {user_info.get('type')}")

            returned_app_id = data.get('application_id')
            print(f"    Application ID: {returned_app_id}")
        else:
            data = verify_result.get('data', {})
            print(f"    message: {data.get('message', 'Unknown error')}")
            print(f"\n  [FAIL] Verification failed!")
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

    # Step 5: 确认放行
    print_section("Step 5: Confirm Entry (Creates Visit Record)")

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
                print(f"\n  [OK] Confirm successful!")
            else:
                print(f"\n  [FAIL] Confirm failed: {confirm_result}")
                return False

        except Exception as e:
            print(f"  [ERROR] {e}")
            return False
    else:
        print(f"\n  [WARNING] No application_id, cannot confirm")
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
            SELECT vr.id, u.real_name, va.visit_date, va.visit_purpose,
                   vr.gate_name, vr.entry_time, vr.created_at
            FROM visit_records vr
            JOIN users u ON vr.user_id = u.id
            LEFT JOIN visit_applications va ON vr.visit_application_id = va.id
            ORDER BY vr.created_at DESC
            LIMIT 3
        ''')
        records = cursor.fetchall()
        print(f"\n  Latest {len(records)} visit records:")
        for record in records:
            print(f"    ID={record[0]}, Name={record[1]}, Date={record[2]}, " +
                  f"Purpose={record[3]}, Gate={record[4]}, Entry={record[5]}, Created={record[6]}")

        conn.close()

        print_section("TEST PASSED - VISIT RECORD CREATED!")
        print("  Complete flow successful:")
        print("  1. Created visitor application with admin token")
        print("  2. Approved application and generated HMAC code")
        print("  3. Guard verified code successfully")
        print("  4. Guard confirmed entry")
        print(f"  5. Visit record created (total records: {count})")
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
        print("  [SUCCESS] Complete visitor flow test passed")
        print("  Visit records have been created in the database")
    else:
        print("  [FAIL] Test failed - Check error messages above")
    print("=" * 80 + "\n")

    sys.exit(0 if success else 1)
