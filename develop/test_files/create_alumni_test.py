"""
Create alumni test data for guard verification
"""
import sqlite3
import os
from datetime import datetime

# Get script directory and find database
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'backend', 'instance', 'alumni_system_dev.db')

if not os.path.exists(db_path):
    print(f"[ERROR] Database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*60)
print('Creating Alumni Test Data')
print('='*60)

# Check for existing alumni users
cursor.execute("""
    SELECT id, real_name, user_type, grade
    FROM users
    WHERE user_type LIKE '%alumni%'
    LIMIT 5
""")
alumni_users = cursor.fetchall()

if alumni_users:
    print(f"\n[INFO] Found {len(alumni_users)} existing alumni users")
    for user in alumni_users:
        print(f"  ID: {user[0]}, Name: {user[1]}, Type: {user[2]}, Grade: {user[3]}")
else:
    print("\n[INFO] No alumni users found. Creating one...")

    # Create an alumni user
    now = datetime.now()
    cursor.execute("""
        INSERT INTO users (username, password_hash, real_name, email, phone, user_type, status, grade, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'alumni_test',
        'test_hash',
        '张三',
        'alumni@test.com',
        '13900000001',
        'alumni',
        'active',
        '2020',  # Graduation year
        now.strftime('%Y-%m-%d %H:%M:%S'),
        now.strftime('%Y-%m-%d %H:%M:%S')
    ))

    alumni_id = cursor.lastrowid
    print(f"[OK] Created alumni user: ID={alumni_id}, Name=张三, Grade=2020")

    # Create alumni profile
    cursor.execute("""
        INSERT INTO alumni_profiles (user_id, student_id, graduation_year, class_name, division,
                                    id_card, contact_teacher, contact_teacher_phone, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        alumni_id,
        'A2020001',
        2020,
        '高三1班',
        '高中部',
        '110101199001011234',
        '李老师',
        '13800000001',
        now.strftime('%Y-%m-%d %H:%M:%S'),
        now.strftime('%Y-%m-%d %H:%M:%S')
    ))

    print(f"[OK] Created alumni profile for 张三 (2020届)")

# Check if alumni verification code exists
code = '888888'
cursor.execute("SELECT id FROM visit_applications WHERE qr_code = ?", (code,))
existing = cursor.fetchone()

if existing:
    print(f"\n[SKIP] Code {code} already exists")
else:
    # Get an alumni user
    cursor.execute("""
        SELECT id, real_name, user_type, grade
        FROM users
        WHERE user_type LIKE '%alumni%'
        LIMIT 1
    """)
    alumni_user = cursor.fetchone()

    if alumni_user:
        alumni_id, alumni_name, user_type, grade = alumni_user

        # Create visitor application
        now = datetime.now()
        visit_date = now.strftime('%Y-%m-%d')
        approval_time = now.strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            INSERT INTO visit_applications (
                applicant_id, visit_date, visit_time_start, visit_time_end, visit_purpose,
                target_person, qr_code, application_status,
                approved_by, approval_time, visit_started,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alumni_id,
            visit_date,
            '09:00',
            '18:00',
            '校友返校参观',
            '校友办',
            code,
            'approved',
            'admin',
            approval_time,
            0,
            now.strftime('%Y-%m-%d %H:%M:%S'),
            now.strftime('%Y-%m-%d %H:%M:%S')
        ))

        print(f"\n[OK] Created alumni visitor application")
        print(f"     Code: {code}")
        print(f"     User: {alumni_name} ({user_type})")
        print(f"     Grade: {grade}")
    else:
        print("\n[ERROR] No alumni user found to create application")

conn.commit()

# Show all test codes
print("\n" + "="*60)
print("Available Test Codes:")
print("="*60)
cursor.execute("""
    SELECT va.qr_code, u.real_name, u.user_type, u.grade
    FROM visit_applications va
    LEFT JOIN users u ON va.applicant_id = u.id
    WHERE va.application_status = 'approved'
    ORDER BY u.user_type
""")
all_codes = cursor.fetchall()

for code_data in all_codes:
    code, name, type_, grade = code_data
    print(f"  {code} - {name} ({type_}) - Grade: {grade}")

print("\n" + "="*60)
print("Test at: http://127.0.0.1:5000/guard-verify")
print("="*60)

conn.close()
