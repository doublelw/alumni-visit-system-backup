"""
Complete E2E Test - All 5 User Stories
Ensure all guard verifications pass (green checkmarks, no red X marks)
"""

import requests
import sqlite3
import sys
import os

BASE_URL = 'http://localhost:5000'

print('=' * 80)
print(' Complete E2E Test - All 5 User Stories')
print('=' * 80)
print('Testing all guard verifications - expecting ALL PASS (no failures)')

# Get users from database
conn = sqlite3.connect('instance/alumni_system_dev.db')
cursor = conn.cursor()

users = {}

# Alumni
cursor.execute('SELECT real_name, phone, wechat_password FROM users WHERE user_type = "alumni" LIMIT 1')
result = cursor.fetchone()
if result:
    users['alumni'] = {'name': result[0], 'phone': result[1], 'password': result[2]}

# Parent
cursor.execute('SELECT real_name, phone, wechat_password FROM users WHERE user_type = "parent" LIMIT 1')
result = cursor.fetchone()
if result:
    users['parent'] = {'name': result[0], 'phone': result[1], 'password': result[2]}

# Student
cursor.execute('''
    SELECT u.real_name, u.phone, u.wechat_password
    FROM users u
    JOIN student_leave_applications sla ON sla.student_id = u.id
    LIMIT 1
''')
result = cursor.fetchone()
if result:
    users['student'] = {'name': result[0], 'phone': result[1], 'password': result[2]}

# Visitor
cursor.execute('SELECT real_name, phone, wechat_password FROM users WHERE user_type = "visitor" ORDER BY id DESC LIMIT 1')
result = cursor.fetchone()
if result:
    users['visitor'] = {'name': result[0], 'phone': result[1], 'password': result[2]}

# Event registration
cursor.execute('''
    SELECT u.real_name, u.phone, u.wechat_password, er.verification_code
    FROM event_registrations er
    JOIN users u ON er.user_id = u.id
    LIMIT 1
''')
result = cursor.fetchone()
if result:
    users['event'] = {'name': result[0], 'phone': result[1], 'password': result[2], 'verification_code': result[3]}

conn.close()

print('\nAvailable users:')
for user_type, user_info in users.items():
    if user_info:
        print(f'  [OK] {user_type}: {user_info["name"]} ({user_info["phone"]})')
    else:
        print(f'  [SKIP] {user_type}: Not found')

# Test each story
print('\n' + '=' * 80)
print(' Testing Guard Verifications')
print('=' * 80)

results = {}

# Helper function to generate HMAC
from app import create_app
from app.utils.hmac_utils import generate_hmac_code

app = create_app()

def test_verification(code, verify_type, label):
    try:
        response = requests.post(
            f'{BASE_URL}/api/guard/verify',
            json={'code': code, 'guard_name': 'Guard01', 'verify_type': verify_type},
            timeout=10
        )
        result = response.json()

        if result.get('success') and result['data'].get('valid'):
            user_info = result['data']['user_info']
            print(f'\n[{label}]')
            print(f'  [PASS] Verification successful')
            print(f'  Name: {user_info.get("name", "N/A")}')
            print(f'  Type: {user_info.get("type", "N/A")}')
            return True, user_info
        else:
            error = result.get('error', 'Unknown')
            print(f'\n[{label}]')
            print(f'  [FAIL] {error}')
            return False, {'error': error}
    except Exception as e:
        print(f'\n[{label}]')
        print(f'  [ERROR] {str(e)}')
        return False, {'exception': str(e)}

with app.app_context():
    # Story 1: Alumni
    if users.get('alumni'):
        print('\n' + '-' * 80)
        print('[Story 1] Alumni Visit')
        user = users['alumni']
        code = generate_hmac_code(user['phone'], user['password'])
        print(f'  Code: {code}')
        success, info = test_verification(code, 'alumni', 'Story 1: Alumni Visit')
        results['Story 1 - Alumni'] = success

    # Story 2: Parent
    if users.get('parent'):
        print('\n' + '-' * 80)
        print('[Story 2] Parent Visit')
        user = users['parent']
        code = generate_hmac_code(user['phone'], user['password'])
        print(f'  Code: {code}')
        success, info = test_verification(code, 'parent-visit', 'Story 2: Parent Visit')
        results['Story 2 - Parent'] = success

    # Story 3: Student Leave
    if users.get('student'):
        print('\n' + '-' * 80)
        print('[Story 3] Student Leave')
        user = users['student']

        # Student leave uses different HMAC generation: student_id + 'STUDENT_EXIT' + today's date
        from datetime import date as dt_date, datetime
        today = dt_date.today()
        today_datetime = datetime.combine(today, datetime.min.time())
        date_timestamp = int(today_datetime.timestamp())

        # Get student_id from database
        conn = sqlite3.connect('instance/alumni_system_dev.db')
        cursor = conn.cursor()
        cursor.execute('SELECT student_id FROM users WHERE phone = ?', (user['phone'],))
        student_row = cursor.fetchone()
        conn.close()

        if student_row and student_row[0]:
            student_id = student_row[0]
            code = generate_hmac_code(student_id, 'STUDENT_EXIT', date_timestamp)
            print(f'  Student ID: {student_id}')
            print(f'  Code: {code} (using student_id + STUDENT_EXIT + today)')
            success, info = test_verification(code, 'student-leave', 'Story 3: Student Leave')
            results['Story 3 - Student'] = success
        else:
            print('  [SKIP] Student has no student_id')
            results['Story 3 - Student'] = None

    # Story 4: Visitor
    if users.get('visitor'):
        print('\n' + '-' * 80)
        print('[Story 4] Visitor')
        user = users['visitor']
        code = generate_hmac_code(user['phone'], user['password'])
        print(f'  Code: {code}')
        success, info = test_verification(code, 'visitor', 'Story 4: Visitor')
        results['Story 4 - Visitor'] = success

    # Story 5: Event Registration
    if users.get('event'):
        print('\n' + '-' * 80)
        print('[Story 5] Event Registration')
        user = users['event']
        code = generate_hmac_code(user['phone'], user['password'])
        stored_code = user.get('verification_code', 'N/A')
        print(f'  Stored verification code: {stored_code}')
        print(f'  Generated HMAC code: {code}')
        success, info = test_verification(code, 'event-registration', 'Story 5: Event Registration')
        results['Story 5 - Event'] = success
    else:
        print('\n' + '-' * 80)
        print('[Story 5] Event Registration')
        print('  [SKIP] No event registration found')
        results['Story 5 - Event'] = None

# Summary
print('\n' + '=' * 80)
print(' Test Summary')
print('=' * 80)

passed = sum(1 for v in results.values() if v is True)
failed = sum(1 for v in results.values() if v is False)
skipped = sum(1 for v in results.values() if v is None)

for story, success in results.items():
    if success is True:
        print(f'  [PASS] {story}')
    elif success is False:
        print(f'  [FAIL] {story}')
    else:
        print(f'  [SKIP] {story}')

print(f'\nPass Rate: {passed}/{passed+failed+skipped} ({passed*100//(passed+failed+skipped) if passed+failed+skipped > 0 else 0}%)')
print(f'Passed: {passed}, Failed: {failed}, Skipped: {skipped}')

# Final verdict
print('\n' + '=' * 80)
print(' Final Verdict')
print('=' * 80)

if failed == 0 and passed >= 3:
    print('  [SUCCESS] All E2E tests passed!')
    print('  All guard verifications successful (green checkmarks)')
    print('  No red X marks (verification failures)')
    exit_code = 0
elif failed > 0:
    print(f'  [FAILURE] {failed} test(s) failed')
    print('  Some guard verifications failed (red X marks)')
    exit_code = 1
else:
    print('  [WARNING] Insufficient test data in database')
    exit_code = 1

print('=' * 80)
sys.exit(exit_code)
