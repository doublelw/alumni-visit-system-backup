"""
创建访客申请测试数据
"""
import sqlite3
from datetime import datetime, timedelta

# 连接数据库
db_path = 'backend/instance/alumni_system_dev.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*50)
print("Creating visitor test data")
print('='*50)

# 1. 创建接待人（如果没有）
cursor.execute(
    "INSERT OR IGNORE INTO users (username, password_hash, real_name, user_type, status, phone) VALUES (?, ?, ?, ?, ?, ?)",
    ('test_host', 'hash', 'Test Teacher', 'teacher', 'active', '13900000001')
)
print("[OK] Host user ready")

# 2. 创建访客申请
access_code = '666666'
expires_at = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
approved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

cursor.execute("""
    INSERT INTO visit_applications (
        visitor_name, id_card, phone, visit_reason,
        visit_date, access_code, code_expires_at,
        host_name, host_id, status, approved_by,
        approved_at, used_count, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    'Test Visitor',
    '110101199001011234',
    '13800138000',
    'Business Meeting',
    datetime.now().strftime('%Y-%m-%d'),
    access_code,
    expires_at,
    'Test Teacher',
    1,
    'approved',
    'admin',
    approved_at,
    0,
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
))

conn.commit()

print("\n" + "="*50)
print("[OK] Visitor application created successfully!")
print("="*50)
print(f"\n   Access Code: {access_code}")
print(f"   Visitor Name: Test Visitor")
print(f"   Visit Reason: Business Meeting")
print(f"   Host Name: Test Teacher")
print(f"   Expires At: {expires_at}")
print("="*50)
print("\n[INFO] Please enter in guard verify page: 666666")
print("        Visit: http://127.0.0.1:5000/guard-verify")
print("="*50)

conn.close()
