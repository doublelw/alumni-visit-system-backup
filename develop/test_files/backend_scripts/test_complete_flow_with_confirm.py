"""
完整门卫验证流程测试 - 包括确认放行
测试完整的访问流程：申请 → 审批 → 验证 → 确认放行 → 创建访问记录
"""

import requests
import sqlite3
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

# 步骤1：检查现有访问申请
print_section("步骤1：检查现有的访问申请")

conn = sqlite3.connect('instance/alumni_system_dev.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM visit_applications WHERE application_status = "approved"')
approved_count = cursor.fetchone()[0]
print(f"已审批的访问申请数: {approved_count}")

cursor.execute('SELECT id, applicant_id, visit_date, visit_purpose, visit_started FROM visit_applications WHERE application_status = "approved" LIMIT 5')
applications = cursor.fetchall()
print(f"\n前5个已审批的访问申请:")
for app in applications:
    cursor.execute('SELECT real_name FROM users WHERE id = ?', (app[1],))
    result = cursor.fetchone()
    applicant_name = result[0] if result else f"用户ID{app[1]}(已删除)"
    print(f"  ID={app[0]}, 申请人={applicant_name}, 日期={app[2]}, 目的={app[3]}, 已进门={app[4]}")

conn.close()

# 步骤2：如果有已审批的申请，进行门卫验证测试
if applications:
    print_section("步骤2：门卫验证测试 - 完整流程（验证 + 确认放行）")

    application_id = applications[0][0]

    # 获取这个申请的access_code
    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 如果第一个申请没有码，找最近有码的申请
    cursor.execute('SELECT access_code FROM visit_applications WHERE id = ?', (application_id,))
    result = cursor.fetchone()

    if not result or not result[0]:
        print(f"\n  申请ID {application_id} 没有access_code，查找其他有码的申请...")
        cursor.execute('''
            SELECT id, access_code FROM visit_applications
            WHERE access_code IS NOT NULL AND access_code != ''
            ORDER BY id DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        if result:
            application_id = result[0]
            print(f"  使用申请ID {application_id} 的码: {result[1]}")

    conn.close()

    if result and result[1]:
        access_code = result[1]
        print(f"\n使用访问申请的码: {access_code}")

        # 2.1 门卫验证
        print(f"\n[2.1] 门卫验证码...")
        verify_response = requests.post(
            f"{BASE_URL}/api/guard/verify",
            json={
                "code": access_code,
                "guard_name": "测试门卫",
                "verify_type": "visitor"
            },
            timeout=10
        )

        verify_result = verify_response.json()
        if verify_result.get('success'):
            print(f"  [OK] 验证成功")
            user_info = verify_result['data'].get('user_info', {})
            print(f"  申请人: {user_info.get('name', 'N/A')}")
            print(f"  类型: {user_info.get('type', 'N/A')}")

            returned_app_id = verify_result['data'].get('application_id')
            print(f"  申请ID: {returned_app_id}")

            # 2.2 点击"确认放行"
            if returned_app_id:
                print(f"\n[2.2] 点击'确认放行'按钮...")
                confirm_response = requests.post(
                    f"{BASE_URL}/api/guard/confirm",
                    json={
                        "application_id": int(returned_app_id),
                        "guard_name": "测试门卫"
                    },
                    timeout=10
                )

                confirm_result = confirm_response.json()
                if confirm_result.get('success'):
                    print(f"  [OK] 确认放行成功！访问记录已创建")
                else:
                    print(f"  [FAIL] 确认放行失败: {confirm_result}")
            else:
                print(f"  [WARNING] 验证成功但没有application_id，无法确认放行")
        else:
            print(f"  [FAIL] 验证失败: {verify_result}")

        # 2.3 检查访问记录是否创建
        print(f"\n[2.3] 检查访问记录...")
        conn = sqlite3.connect('instance/alumni_system_dev.db')
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM visit_records')
        record_count = cursor.fetchone()[0]
        print(f"  当前访问记录总数: {record_count}")

        cursor.execute('''
            SELECT vr.id, u.real_name, vr.visit_date, vr.visit_purpose, vr.guard_name, vr.entry_time
            FROM visit_records vr
            JOIN users u ON vr.user_id = u.id
            ORDER BY vr.created_at DESC
            LIMIT 3
        ''')
        recent_records = cursor.fetchall()
        print(f"\n  最新的3条访问记录:")
        for record in recent_records:
            print(f"    - {record[1]} 于 {record[2]} 访问目的: {record[3]}, 门卫: {record[4]}, 进门时间: {record[5]}")

        conn.close()
    else:
        print(f"\n  [WARNING] 访问申请没有access_code，无法测试")

else:
    print("\n  [WARNING] 没有已审批的访问申请，无法进行完整流程测试")
    print("  建议：先通过管理后台创建并审批一些访问申请")

# 步骤3：测试管理后台的访问申请和记录查询
print_section("步骤3：测试管理后台查询功能")

# 模拟管理员登录
print("\n[3.1] 管理员登录...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"username": "admin", "password": "admin123"},
    timeout=10
)

if login_response.status_code == 200:
    login_result = login_response.json()
    admin_token = login_result.get('access_token') or login_result.get('token')
    print(f"  [OK] 管理员登录成功")

    headers = {"Authorization": f"Bearer {admin_token}"}

    # 3.2 查询访问申请
    print(f"\n[3.2] 查询访问申请...")
    apps_response = requests.get(
        f"{BASE_URL}/api/visits/applications?page=1&per_page=10",
        headers=headers,
        timeout=10
    )

    if apps_response.status_code == 200:
        apps_result = apps_response.json()
        if apps_result.get('success') or apps_result.get('applications'):
            applications = apps_result.get('applications', apps_result.get('data', []))
            print(f"  [OK] 访问申请查询成功")
            print(f"  申请数量: {len(applications) if isinstance(applications, list) else 'N/A'}")
        else:
            print(f"  访问申请响应: {apps_result}")
    else:
        print(f"  [FAIL] 访问申请查询失败: HTTP {apps_response.status_code}")

    # 3.3 查询访问记录
    print(f"\n[3.3] 查询访问记录...")
    records_response = requests.get(
        f"{BASE_URL}/api/visits/records?page=1&per_page=10",
        headers=headers,
        timeout=10
    )

    if records_response.status_code == 200:
        records_result = records_response.json()
        if records_result.get('success') or records_result.get('records'):
            records = records_result.get('records', records_result.get('data', []))
            print(f"  [OK] 访问记录查询成功")
            print(f"  记录数量: {len(records) if isinstance(records, list) else 'N/A'}")

            if isinstance(records, list) and records:
                print(f"\n  最新的访问记录:")
                for record in records[:3]:
                    print(f"    - {record}")
        else:
            print(f"  访问记录响应: {records_result}")
    else:
        print(f"  [FAIL] 访问记录查询失败: HTTP {records_response.status_code}")
else:
    print(f"  [FAIL] 管理员登录失败")

# 步骤4：总结
print_section("测试总结")

print("""
[OK] 完整流程说明：
  1. 用户提交访问申请 → 老师审批 → 生成访问码
  2. 门卫验证访问码 → 验证通过
  3. 门卫点击"确认放行"按钮 → 创建visit_record记录
  4. 后台管理可以查询访问申请和访问记录

[WARNING] 注意事项：
  - HMAC码验证不创建访问记录（因为HMAC码不关联申请）
  - 只有审批流程的访问码才会创建访问记录
  - 必须调用 /api/guard/confirm 接口才会创建记录
""")

print("\n" + "=" * 80)
print("  请查看管理后台确认:")
print("  1. 访问申请页面：http://localhost:5000/admin")
print("  2. 查看访问申请和访问记录")
print("=" * 80)
