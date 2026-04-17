"""
Update visitor application with valid user ID
"""
import sqlite3
from datetime import datetime

# Connect to database
db_path = 'backend/instance/alumni_system_dev.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*50)
print('Update visitor application test data')
print('='*50)

# Update the visitor application to use a valid applicant_id
access_code = '666666'

cursor.execute("""
    UPDATE visit_applications
    SET applicant_id = 6
    WHERE qr_code = ?
""", (access_code,))

conn.commit()

# Verify the update
cursor.execute("""
    SELECT va.id, va.qr_code, va.applicant_id, u.real_name, u.user_type
    FROM visit_applications va
    LEFT JOIN users u ON va.applicant_id = u.id
    WHERE va.qr_code = ?
""", (access_code,))

result = cursor.fetchone()

if result:
    print("\n" + "="*50)
    print("[OK] Visitor application updated!")
    print("="*50)
    print(f"\n   Access Code: {result[1]}")
    print(f"   Applicant ID: {result[2]}")
    print(f"   Applicant Name: {result[3]}")
    print(f"   Applicant Type: {result[4]}")
    print("="*50)
    print("\n[INFO] Test with access code: 666666")
    print("        Visit: http://127.0.0.1:5000/guard-verify")
    print("="*50)

conn.close()
