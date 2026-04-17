"""
测试增强后的访问记录字段
验证新增的字段是否正确填充
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

def main():
    print_section("测试增强后的访问记录字段")

    # 创建一个访问申请并验证
    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 获取访客用户
    cursor.execute('SELECT id, real_name, phone, wechat_password, email FROM users WHERE user_type = "visitor" LIMIT 1')
    result = cursor.fetchone()
    if not result:
        print("[ERROR] No visitor user found")
        return False

    user = {
        'id': result[0],
        'name': result[1],
        'phone': result[2],
        'password': result[3],
        'email': result[4]
    }

    print(f"测试用户: {user['name']}")
    print(f"  手机: {user['phone']}")
    print(f"  邮箱: {user['email'] or '未填写'}")

    # 创建访问申请（含目的地和接待人）
    visit_date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO visit_applications
        (applicant_id, visit_date, visit_time_start, visit_time_end,
         visit_purpose, target_department, target_person, application_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user['id'], visit_date, '09:00', '17:00',
          '教务处办理手续', '教务处', '张老师', 'approved'))

    application_id = cursor.lastrowid
    print(f"\n创建访问申请 ID: {application_id}")
    print(f"  访问目的: 教务处办理手续")
    print(f"  访问目的地: 教务处")
    print(f"  接待人: 张老师")

    # 生成访问码
    app = create_app()
    with app.app_context():
        timestamp = int(time.time())
        code = generate_hmac_code(user['phone'], user['password'], timestamp)
        access_code = code[-6:]

    cursor.execute('UPDATE visit_applications SET access_code = ? WHERE id = ?', (access_code, application_id))
    conn.commit()
    conn.close()

    print(f"  访问码: {access_code}")

    # 门卫验证
    print_section("门卫验证 + 确认放行")

    verify_response = requests.post(
        f"{BASE_URL}/api/guard/verify",
        json={"code": access_code, "guard_name": "门卫01", "verify_type": "visitor"},
        timeout=10
    )

    verify_result = verify_response.json()
    if not verify_result.get('success'):
        print(f"[ERROR] Verification failed: {verify_result}")
        return False

    print(f"[OK] 验证成功")

    application_id = verify_result.get('data', {}).get('application_id')

    # 确认放行
    if application_id:
        confirm_response = requests.post(
            f"{BASE_URL}/api/guard/confirm",
            json={"application_id": int(application_id), "guard_name": "门卫01"},
            timeout=10
        )

        confirm_result = confirm_response.json()
        if confirm_result.get('success'):
            print(f"[OK] 确认放行成功")
        else:
            print(f"[ERROR] Confirm failed: {confirm_result}")
            return False
    else:
        print(f"[ERROR] No application_id returned")
        return False

    # 检查新创建的访问记录
    print_section("检查新字段是否正确填充")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT vr.id, u.real_name, vr.visitor_type, vr.destination,
               vr.host_person, vr.guard_name, vr.info_complete,
               vr.visit_purpose, vr.entry_time
        FROM visit_records vr
        JOIN users u ON vr.user_id = u.id
        ORDER BY vr.created_at DESC
        LIMIT 1
    ''')

    record = cursor.fetchone()
    conn.close()

    if record:
        print(f"\n最新访问记录:")
        print(f"  记录ID: {record[0]}")
        print(f"  姓名: {record[1]}")
        print(f"  访问者类型: {record[2]} [OK]")
        print(f"  访问目的地: {record[3] or '未填写'} [OK]")
        print(f"  接待人: {record[4] or '未填写'} [OK]")
        print(f"  门卫姓名: {record[5] or '未填写'} [OK]")
        print(f"  信息完整度: {'完整' if record[6] else '不完整'} [OK]")
        print(f"  访问目的: {record[7] or '未填写'} [OK]")
        print(f"  进门时间: {record[8]}")

        # 验证字段是否正确
        success = True
        issues = []

        if not record[2]:  # visitor_type
            issues.append("visitor_type 未填充")
            success = False

        if not record[5]:  # guard_name
            issues.append("guard_name 未填充")
            success = False

        if not record[7]:  # visit_purpose
            issues.append("visit_purpose 未填充")
            success = False

        if success:
            print_section("测试通过 [OK]")
            print("所有新字段都已正确填充！")
            return True
        else:
            print_section("测试失败 [FAIL]")
            print("问题:")
            for issue in issues:
                print(f"  - {issue}")
            return False
    else:
        print("[ERROR] 没有找到访问记录")
        return False

if __name__ == "__main__":
    print("\n确保Flask服务器正在运行...")
    time.sleep(2)

    success = main()

    print("\n" + "=" * 80)
    if success:
        print("  [SUCCESS] All new fields tested successfully")
    else:
        print("  [FAIL] Some fields not populated correctly")
    print("=" * 80 + "\n")

    sys.exit(0 if success else 1)
