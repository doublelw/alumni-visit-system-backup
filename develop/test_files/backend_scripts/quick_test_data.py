# -*- coding: utf-8 -*-
"""
Quick test data generator for statistics
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
    print(f'Teachers: {len(teachers)}')

    if not students or not alumni or not teachers:
        print('\nERROR: Not enough users. Please create users first.')
        exit(1)

    # Delete old test data
    print('\nCleaning old data...')
    StudentExitApplication.query.delete()
    VisitRecord.query.delete()
    db.session.commit()

    # Create student leave records (last 30 days)
    print('\nCreating student leave records...')
    exit_reasons = ['Medical', 'Family', 'Competition', 'Visit', 'Other']
    destinations = ['City', 'Home', 'Hospital', 'Other']

    total_leaves = 0
    for days_ago in range(30):
        date = datetime.now() - timedelta(days=days_ago)
        for _ in range(random.randint(1, 5)):
            student = random.choice(students)
            application = StudentExitApplication(
                student_id=student.id,
                exit_date=date.date(),
                exit_time_start=f'{8+random.randint(0,2)}:00',
                exit_time_end=f'{18+random.randint(0,2)}:00',
                exit_reason=random.choice(exit_reasons),
                destination=random.choice(destinations),
                transport_method=random.choice(['Walk', 'Bus', 'Subway', 'Car', 'Taxi']),
                application_status='approved',
                teacher_approval_time=date,
                created_at=date - timedelta(hours=random.randint(1, 24))
            )
            db.session.add(application)
            total_leaves += 1

    db.session.commit()
    print(f'[OK] Created {total_leaves} leave records')

    # Create visit records (last 30 days)
    print('\nCreating visit records...')
    visitor_types = ['alumni', 'parent', 'visitor']
    visit_purposes = ['Office', 'Visit', 'Meeting', 'Other']
    destinations = ['Admin', 'Teaching', 'Library', 'Lab']

    total_visits = 0
    for days_ago in range(30):
        date = datetime.now() - timedelta(days=days_ago)
        for _ in range(random.randint(2, 8)):
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
                destination=random.choice(destinations),
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
            total_visits += 1

    db.session.commit()
    print(f'[OK] Created {total_visits} visit records')

    # Summary
    print('\n=== Test Data Summary ===')
    print(f'Student leave records: {StudentExitApplication.query.count()}')
    print(f'Visit records: {VisitRecord.query.count()}')

    # Visit records by type
    print('\nVisit records by type:')
    for vtype in ['alumni', 'parent', 'visitor']:
        count = VisitRecord.query.filter_by(visitor_type=vtype).count()
        print(f'  {vtype}: {count}')

    print('\n=== Completed! ===')
