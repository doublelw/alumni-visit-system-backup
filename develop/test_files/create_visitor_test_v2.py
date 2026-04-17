"""
Create visitor application test data
"""
import sqlite3
from datetime import datetime, timedelta

# Connect to database
db_path = 'backend/instance/alumni_system_dev.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*50)
print('Creating visitor application test data')
print('='*50)

# 1. Create host user (if not exists)
cursor.execute(
    "INSERT OR IGNORE INTO users (username, password_hash, real_name, user_type, status, phone) VALUES (?, ?, ?, ?, ?, ?)",
    ('test_host', 'hash', 'Test Teacher', 'teacher', 'active', '13900000001')
)
print('[OK] Host user ready')

# Get host user ID
cursor.execute("SELECT id FROM users WHERE username = 'test_host'")
host_user = cursor.fetchone()
host_id = host_user[0] if host_user else 1

# 2. Create visitor application with access code
access_code = '666666'
now = datetime.now()
expires_at = (now + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
visit_date = now.strftime('%Y-%m-%d')
approval_time = now.strftime('%Y-%m-%d %H:%M:%S')

# First check if qr_code column exists
cursor.execute("PRAGMA table_info(visit_applications)")
columns = [col[1] for col in cursor.fetchall()]

# Use qr_code for access code
cursor.execute("""
    INSERT INTO visit_applications (
        applicant_id, visit_date, visit_time_start, visit_time_end, visit_purpose,
        target_person, qr_code, application_status,
        approved_by, approval_time, visit_started,
        created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    host_id,  # Use host_id as applicant_id
    visit_date,
    '09:00',
    '18:00',
    'Business Meeting',
    'Test Teacher',
    access_code,
    'approved',
    'admin',
    approval_time,
    0,
    now.strftime('%Y-%m-%d %H:%M:%S'),
    now.strftime('%Y-%m-%d %H:%M:%S')
))

conn.commit()

print("\n" + "="*50)
print("[OK] Visitor application created successfully!")
print("="*50)
print(f"\n   Access Code: {access_code}")
print(f"   Visit Purpose: Business Meeting")
print(f"   Target Person: Test Teacher")
print(f"   Visit Date: {visit_date}")
print(f"   Approval Time: {approval_time}")
print("="*50)
print("\n[INFO] Please enter in guard verify page: 666666")
print("        Visit: http://127.0.0.1:5000/guard-verify")
print("="*50)

# Verify the data
cursor.execute("SELECT id, qr_code, application_status FROM visit_applications WHERE qr_code = ?", (access_code,))
result = cursor.fetchone()
if result:
    print(f"\n[VERIFY] Record created in database:")
    print(f"         ID: {result[0]}")
    print(f"         QR Code: {result[1]}")
    print(f"         Status: {result[2]}")

conn.close()
