#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check parent student relationship"""
import sqlite3
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'backend', 'instance', 'alumni_system_dev.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*60)
print('Checking Parent-Student Relationships')
print('='*60)

# Find parent with code 222222
cursor.execute("""
    SELECT va.applicant_id, u.real_name, u.user_type, u.parent_student_id
    FROM visit_applications va
    LEFT JOIN users u ON va.applicant_id = u.id
    WHERE va.qr_code = '222222'
""")

result = cursor.fetchone()

if result:
    applicant_id, parent_name, user_type, parent_student_id = result
    print(f"\nParent: {parent_name}")
    print(f"Type: {user_type}")
    print(f"Linked Student ID: {parent_student_id}")

    if parent_student_id:
        # Get student info
        cursor.execute("""
            SELECT real_name, grade, class_id, student_id
            FROM users
            WHERE id = ?
        """, (parent_student_id,))

        student = cursor.fetchone()
        if student:
            student_name, student_grade, student_class, student_id_num = student
            print(f"\nLinked Student:")
            print(f"  Name: {student_name}")
            print(f"  Grade: {student_grade}")
            print(f"  Class: {student_class}")
            print(f"  Student ID: {student_id_num}")

            if student_grade and student_class:
                print(f"  Child Class Name: {student_grade} {student_class}班")
        else:
            print("\n[ERROR] Student not found in database")
    else:
        print("\n[ERROR] Parent has no linked student")
else:
    print("\n[ERROR] Parent with code 222222 not found")

print('\n' + '='*60)
conn.close()
