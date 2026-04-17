#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug parent API response"""
import sqlite3
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'backend', 'instance', 'alumni_system_dev.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*60)
print('Debug Parent Query')
print('='*60)

# Get parent applicant_id
cursor.execute("""
    SELECT applicant_id FROM visit_applications WHERE qr_code = '222222'
""")
applicant_row = cursor.fetchone()

if not applicant_row:
    print("[ERROR] Code 222222 not found")
    exit(1)

applicant_id = applicant_row[0]
print(f"\nApplicant ID: {applicant_id}")

# Run the exact query from electronic_card.py
parent_student_query = """
    SELECT u.real_name, u.grade, u.class_id, u.student_id
    FROM users u
    WHERE u.id = (SELECT student_parent_id FROM users WHERE id = ?)
    LIMIT 1
"""

cursor.execute(parent_student_query, (applicant_id,))
student_result = cursor.fetchone()

if student_result:
    student_name, student_grade, student_class, student_id_num = student_result

    print(f"\nQuery Result:")
    print(f"  student_name: '{student_name}' (type: {type(student_name).__name__})")
    print(f"  student_grade: '{student_grade}' (type: {type(student_grade).__name__})")
    print(f"  student_class: '{student_class}' (type: {type(student_class).__name__})")
    print(f"  student_id_num: '{student_id_num}' (type: {type(student_id_num).__name__})")

    # Check condition
    if student_grade and student_class:
        child_class_name = f'{student_grade} {student_class}班'
        print(f"\n[OK] child_class_name would be: '{child_class_name}'")
    else:
        print(f"\n[FAIL] Condition check failed:")
        print(f"  student_grade is {student_grade if student_grade else 'None/Empty'}")
        print(f"  student_class is {student_class if student_class else 'None/Empty'}")
else:
    print("\n[ERROR] No student found")

conn.close()
print('\n' + '='*60)
