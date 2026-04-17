"""
Create complete test data for guard verification system
Including student, teacher, and parent visitor scenarios
"""
import sqlite3
from datetime import datetime, timedelta

db_path = 'backend/instance/alumni_system_dev.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*60)
print('Creating Complete Test Data for Guard Verification')
print('='*60)

# Get existing users
cursor.execute("""
    SELECT id, real_name, user_type, grade, class_id, student_id
    FROM users
    WHERE user_type IN ('student', 'parent')
    LIMIT 5
""")
users = cursor.fetchall()

if not users:
    print("[ERROR] No student or parent users found. Please create some first.")
    conn.close()
    exit(1)

print(f"\n[INFO] Found {len(users)} test users")

# Create test visitor applications for different user types
test_cases = [
    {
        'code': '111111',
        'description': 'Student Visitor',
        'user_type': 'student',
        'visit_purpose': '学生事务办理',
        'target_person': '教务处'
    },
    {
        'code': '222222',
        'description': 'Parent Visitor',
        'user_type': 'parent',
        'visit_purpose': '家长会面',
        'target_person': '班主任'
    },
    {
        'code': '333333',
        'description': 'Teacher Visitor',
        'user_type': 'teacher',
        'visit_purpose': '教研活动',
        'target_person': '教研组长'
    }
]

created_count = 0
for test_case in test_cases:
    code = test_case['code']
    user_type = test_case['user_type']

    # Find a user of this type
    matching_user = None
    for user in users:
        if user[2] == user_type:
            matching_user = user
            break

    if not matching_user:
        print(f"[SKIP] {test_case['description']}: No matching user found")
        continue

    user_id, user_name, _, user_grade, user_class, user_student_id = matching_user

    # Check if code already exists
    cursor.execute("SELECT id FROM visit_applications WHERE qr_code = ?", (code,))
    if cursor.fetchone():
        print(f"[SKIP] {test_case['description']}: Code {code} already exists")
        continue

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
        user_id,
        visit_date,
        '09:00',
        '18:00',
        test_case['visit_purpose'],
        test_case['target_person'],
        code,
        'approved',
        'admin',
        approval_time,
        0,
        now.strftime('%Y-%m-%d %H:%M:%S'),
        now.strftime('%Y-%m-%d %H:%M:%S')
    ))

    created_count += 1
    print(f"[OK] Created: {test_case['description']}")
    print(f"     Code: {code}")
    print(f"     User: {user_name} ({user_type})")
    if user_grade and user_class:
        print(f"     Class: {user_grade} {user_class}")
    print()

conn.commit()

print("="*60)
print(f"[SUCCESS] Created {created_count} test visitor applications")
print("="*60)
print("\n📱 Test Access Codes:")
print("   111111 - Student Visitor (学生访客)")
print("   222222 - Parent Visitor (家长访客)")
print("   333333 - Teacher Visitor (教师访客)")
print("   666666 - Test Teacher (测试教师)")
print("\n🌐 Visit: http://127.0.0.1:5000/guard-verify")
print("="*60)

conn.close()
