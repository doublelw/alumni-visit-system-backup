# -*- coding: utf-8 -*-
"""
Simple test data generator - batch commits
"""

from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from app.models.visit_record import VisitRecord
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    print('=== Creating Test Data ===\n')

    # Get users
    students = User.query.filter_by(user_type='student').all()
    alumni = User.query.filter_by(user_type='alumni').all()
    teachers = User.query.filter_by(user_type='teacher').all()

    print(f'Students: {len(students)}')
    print(f'Alumni: {len(alumni)}')
    print(f'Teachers: {len(teachers)}\n')

    # Delete old test data
    print('Cleaning old data...')
    StudentExitApplication.query.delete()
    VisitRecord.query.delete()
    db.session.commit()

    # Create student leave records - batch by day
    print('Creating student leave records...')
    exit_reasons = ['Medical', 'Family', 'Competition', 'Visit', 'Other']
    destinations = ['City', 'Home', 'Hospital', 'Other']

    for days_ago in range(30):
        date = datetime.now() - timedelta(days=days_ago)
        count = random.randint(1, 5)

        for _ in range(count):
            student = random.choice(students)
            application = StudentExitApplication(
                student_id=student.id,
                applicant_id=student.id,  # Required field
                exit_date=date.date(),
                exit_time_start=f'{8+random.randint(0,2)}:00',
                exit_time_end=f'{18+random.randint(0,2)}:00',
                exit_reason=random.choice(exit_reasons),
                destination=random.choice(destinations),
                transport_method=random.choice(['Walk', 'Bus', 'Subway', 'Car', 'Taxi']),
                application_status='approved',
                parent_approval_status='approved',
                parent_approval_time=date,
                teacher_approval_status='approved',
                teacher_approval_time=date,
                created_at=date - timedelta(hours=random.randint(1, 24))
            )
            db.session.add(application)

        # Commit every day
        db.session.commit()
        print(f'  Day {days_ago}: {count} records', end='\r')

    total_leaves = StudentExitApplication.query.count()
    print(f'\n[OK] Total leave records: {total_leaves}')

    # Create visit records - batch by day
    print('\nCreating visit records...')
    visitor_types = ['alumni', 'parent', 'visitor']
    visit_purposes = ['Office', 'Visit', 'Meeting', 'Other']
    destinations_list = ['Admin', 'Teaching', 'Library', 'Lab']

    for days_ago in range(30):
        date = datetime.now() - timedelta(days=days_ago)
        count = random.randint(2, 8)

        for _ in range(count):
            vtype = random.choice(visitor_types)
            host = random.choice(teachers)

            if vtype == 'alumni':
                visitor = random.choice(alumni)
            else:
                visitor = random.choice(students)

            visit = VisitRecord(
                user_id=visitor.id,
                visitor_type=vtype,
                visit_purpose=random.choice(visit_purposes),
                destination=random.choice(destinations_list),
                host_person_id=host.id,
                host_person=host.real_name,
                entry_time=date + timedelta(
                    hours=random.randint(8, 17),
                    minutes=random.randint(0, 59)
                ),
                guard_name=f'Guard {random.randint(1, 5)}',
                verification_method=random.choice(['Face', 'QR', 'Manual'])
            )
            db.session.add(visit)

        # Commit every day
        db.session.commit()
        print(f'  Day {days_ago}: {count} records', end='\r')

    total_visits = VisitRecord.query.count()
    print(f'\n[OK] Total visit records: {total_visits}')

    # Summary
    print('\n=== Summary ===')
    print(f'Student leave records: {total_leaves}')
    print(f'Visit records: {total_visits}')

    for vtype in ['alumni', 'parent', 'visitor']:
        count = VisitRecord.query.filter_by(visitor_type=vtype).count()
        print(f'  {vtype}: {count}')

    print('\n=== Done! ===')
