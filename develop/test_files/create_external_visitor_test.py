"""
Create external visitor test data
"""
import sqlite3
from datetime import datetime
import random
import string

db_path = 'backend/instance/alumni_system_dev.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*60)
print('Creating External Visitor Test Data')
print('='*60)

# Generate 6-digit code
visitor_code = '999999'

# Check if code already exists
cursor.execute("SELECT id, application_status FROM visit_applications WHERE qr_code = ?", (visitor_code,))
existing = cursor.fetchone()

if existing:
    print(f"\n[INFO] Code {visitor_code} already exists")
    print(f"Status: {existing[1]}")
else:
    # Create external visitor application
    now = datetime.now()
    visit_date = now.strftime('%Y-%m-%d')
    approval_time = now.strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
        INSERT INTO visit_applications (
            applicant_id, visit_date, visit_time_start, visit_time_end,
            visit_purpose, target_person, qr_code, application_status,
            approved_by, approval_time, visit_started, created_at, updated_at
        ) VALUES (0, ?, '08:00', '20:00', ?, ?, ?, 'approved',
                0, ?, 0, ?, ?)
    """, (
        visit_date,
        "送货 - 顺丰速运",
        "后勤部李老师",
        visitor_code,
        approval_time,
        now.strftime('%Y-%m-%d %H:%M:%S'),
        now.strftime('%Y-%m-%d %H:%M:%S')
    ))

    conn.commit()
    print(f"\n[OK] External visitor created successfully!")
    print(f"\n" + "="*60)
    print(f"验证码: {visitor_code}")
    print(f"访客类型: 外部访客")
    print(f"访问目的: 送货 - 顺丰速运")
    print(f"校内联系人: 后勤部李老师")
    print(f"审批时间: {approval_time}")
    print(f"访问日期: {visit_date}")
    print("="*60)
    print(f"\n🌐 测试地址:")
    print(f"   门卫验证: http://127.0.0.1:5000/guard-verify")
    print(f"\n使用方法:")
    print(f"   1. 访问门卫验证页面")
    print(f"   2. 输入验证码: {visitor_code}")
    print(f"   3. 点击验证")
    print(f"   4. 查看外部访客显示效果")
    print("="*60)

# Verify the created record
cursor.execute("""
    SELECT id, visit_purpose, target_person, approval_time
    FROM visit_applications
    WHERE qr_code = ?
""", (visitor_code,))

result = cursor.fetchone()
if result:
    print(f"\n[验证] 数据库记录确认:")
    print(f"   ID: {result[0]}")
    print(f"   访问目的: {result[1]}")
    print(f"   联系人: {result[2]}")
    print(f"   审批时间: {result[3]}")

conn.close()
