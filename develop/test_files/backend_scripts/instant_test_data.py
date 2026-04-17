# -*- coding: utf-8 -*-
"""
Ultra-fast test data generator using direct SQL
"""

from app import create_app, db
from app.models.user import User
from sqlalchemy import text
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    print('=== Creating Test Data (Fast Mode) ===\n')

    # Get user IDs
    student_ids = [u.id for u in User.query.filter_by(user_type='student').all()]
    alumni_ids = [u.id for u in User.query.filter_by(user_type='alumni').all()]
    teacher_data = [(u.id, u.real_name) for u in User.query.filter_by(user_type='teacher').all()]

    print(f'Students: {len(student_ids)}')
    print(f'Alumni: {len(alumni_ids)}')
    print(f'Teachers: {len(teacher_data)}')

    if not student_ids or not alumni_ids or not teacher_data:
        print('\nERROR: Not enough users')
        exit(1)

    # Delete old data using SQL
    print('\nCleaning old data...')
    db.session.execute(text('DELETE FROM student_exit_applications'))
    db.session.execute(text('DELETE FROM visit_records'))
    db.session.commit()

    # Insert student leave records using SQL
    print('\nInserting leave records...')
    exit_reasons = ['Medical', 'Family', 'Competition', 'Visit', 'Other']
    destinations = ['City', 'Home', 'Hospital', 'Other']
    transports = ['Walk', 'Bus', 'Subway', 'Car', 'Taxi']

    leave_values = []
    for days_ago in range(30):
        date = datetime.now() - timedelta(days=days_ago)
        date_str = date.strftime('%Y-%m-%d')
        time_str = date.strftime('%Y-%m-%d %H:%M:%S')

        for _ in range(random.randint(1, 5)):
            student_id = random.choice(student_ids)
            leave_values.append(f"""
                ({student_id}, {student_id},
                 '{date_str}', '{8+random.randint(0,2)}:00:00', '{18+random.randint(0,2)}:00:00',
                 '{random.choice(exit_reasons)}', '{random.choice(destinations)}', '{random.choice(transports)}',
                 'approved', 'approved', '{time_str}', 'approved', '{time_str}', '{time_str}')
            """)

    # Split into batches to avoid query size limits
    batch_size = 50
    for i in range(0, len(leave_values), batch_size):
        batch = leave_values[i:i+batch_size]
        sql = f"""
            INSERT INTO student_exit_applications
            (student_id, applicant_id, exit_date, exit_time_start, exit_time_end,
             exit_reason, destination, transport_method, application_status,
             parent_approval_status, parent_approval_time, teacher_approval_status,
             teacher_approval_time, created_at)
            VALUES {','.join(batch)}
        """
        db.session.execute(text(sql))
        db.session.commit()
        print(f'  Progress: {min(i+batch_size, len(leave_values))}/{len(leave_values)}', end='\r')

    total_leaves = db.session.execute(text('SELECT COUNT(*) FROM student_exit_applications')).scalar()
    print(f'\n[OK] Total leave records: {total_leaves}')

    # Insert visit records using SQL
    print('\nInserting visit records...')
    visitor_types = ['alumni', 'parent', 'visitor']
    visit_purposes = ['Office', 'Visit', 'Meeting', 'Other']
    destinations_list = ['Admin', 'Teaching', 'Library', 'Lab']
    verifications = ['Face', 'QR', 'Manual']

    visit_values = []
    for days_ago in range(30):
        date = datetime.now() - timedelta(days=days_ago)
        date_str = date.strftime('%Y-%m-%d')

        for _ in range(random.randint(2, 8)):
            vtype = random.choice(visitor_types)
            teacher_id, teacher_name = random.choice(teacher_data)

            if vtype == 'alumni':
                user_id = random.choice(alumni_ids)
            else:
                user_id = random.choice(student_ids)

            hour = random.randint(8, 17)
            minute = random.randint(0, 59)
            time_str = f'{date_str} {hour:02d}:{minute:02d}:{random.randint(0,59):02d}'

            visit_values.append(f"""
                ({user_id}, '{vtype}', '{random.choice(visit_purposes)}', '{random.choice(destinations_list)}',
                 {teacher_id}, '{teacher_name.replace("'", "''")}',
                 '{time_str}', 'Guard {random.randint(1, 5)}', '{random.choice(verifications)}')
            """)

    # Split into batches
    for i in range(0, len(visit_values), batch_size):
        batch = visit_values[i:i+batch_size]
        sql = f"""
            INSERT INTO visit_records
            (user_id, visitor_type, visit_purpose, destination, host_person_id, host_person,
             entry_time, guard_name, verification_method)
            VALUES {','.join(batch)}
        """
        db.session.execute(text(sql))
        db.session.commit()
        print(f'  Progress: {min(i+batch_size, len(visit_values))}/{len(visit_values)}', end='\r')

    total_visits = db.session.execute(text('SELECT COUNT(*) FROM visit_records')).scalar()
    print(f'\n[OK] Total visit records: {total_visits}')

    # Summary
    print('\n=== Summary ===')
    print(f'Student leave records: {total_leaves}')
    print(f'Visit records: {total_visits}')

    for vtype in ['alumni', 'parent', 'visitor']:
        count = db.session.execute(text(f"SELECT COUNT(*) FROM visit_records WHERE visitor_type='{vtype}'")).scalar()
        print(f'  {vtype}: {count}')

    print('\n=== Done! ===')
