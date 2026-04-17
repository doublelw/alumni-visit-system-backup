# -*- coding: utf-8 -*-
"""
Create test data for statistics
"""

from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from app.models.visit_record import VisitRecord
from app.models.alumni_profile import AlumniProfile
from datetime import datetime, timedelta
import random
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = create_app()

with app.app_context():
    print('=== Starting to create test data ===\n')

    # Get admin user
    admin = User.query.filter_by(user_type='admin').first()
    if not admin:
        print('ERROR: Admin user not found')
        exit(1)

    # Get teacher users
    teachers = User.query.filter_by(user_type='teacher').all()
    if not teachers:
        print('ERROR: Teacher users not found')
        exit(1)
    print(f'[OK] Found {len(teachers)} teachers')

    # Get or create student users
    students = User.query.filter_by(user_type='student').all()
    if len(students) < 10:
        print('Creating more student users...')
        try:
            for i in range(10):
                # Skip if username already exists
                if User.query.filter_by(username=f'student{i+1:03d}').first():
                    continue

                grade = ['高一', '高二', '高三'][i % 3]
                class_id = str((i % 5) + 1)
                student = User(
                    username=f'student{i+1:03d}',
                    password_hash='pbkdf2:sha256:260000$test',
                    real_name=f'Test Student {i+1}',
                    user_type='student',
                    grade=grade,
                    class_id=class_id,
                    phone=f'138{i:04d}0000',
                    email=f'student{i+1}@test.edu.cn',
                    status='active'
                )
                db.session.add(student)
            db.session.commit()
        except Exception as e:
            print(f'Error creating students: {e}')
            db.session.rollback()
        students = User.query.filter_by(user_type='student').all()
    print(f'[OK] Student users: {len(students)}')

    # Get or create alumni users
    alumni = User.query.filter(User.user_type == 'alumni').all()
    if len(alumni) < 15:
        print('Creating more alumni users...')
        try:
            for i in range(15):
                # Skip if username already exists
                if User.query.filter_by(username=f'alumnus{i+1:03d}').first():
                    continue

                graduation_year = 1990 + ((i * 2) % 35)
                grad_int = graduation_year
                grad_str = str(grad_int)
                alumni_user = User(
                    username=f'alumnus{i+1:03d}',
                    password_hash='pbkdf2:sha256:260000$test',
                    real_name=f'Test Alumnus {i+1}',
                    user_type='alumni',
                    phone=f'139{i:04d}0000',
                    email=f'alumnus{i+1}@test.edu.cn',
                    status='active'
                )
                db.session.add(alumni_user)
                db.session.flush()

                profile = AlumniProfile(
                    user_id=alumni_user.id,
                    student_id=f'S{grad_int}{i:03d}',
                    graduation_year=grad_int,
                    class_name=f'{grad_str} Class {(i%3)+1}',
                    division='High School',
                    id_card=f'id{i:018d}',
                    contact_teacher='Test Teacher',
                    contact_teacher_phone='13800000000'
                )
                db.session.add(profile)
            db.session.commit()
        except Exception as e:
            print(f'Error creating alumni: {e}')
            db.session.rollback()
        alumni = User.query.filter(User.user_type == 'alumni').all()
    print(f'[OK] Alumni users: {len(alumni)}')

    # Add alumni profiles for those without
    for alu in alumni:
        if not hasattr(alu, 'alumni_profile') or not alu.alumni_profile:
            grad_year = 1990 + random.randint(0, 35)
            profile = AlumniProfile(
                user_id=alu.id,
                student_id=f'S{grad_year}{alu.id:03d}',
                graduation_year=grad_year,
                class_name=f'{grad_year} Class {random.randint(1, 5)}',
                division='High School',
                id_card=f'id{alu.id:018d}',
                contact_teacher='Test Teacher',
                contact_teacher_phone='13800000000'
            )
            db.session.add(profile)
    db.session.commit()

    # Delete old test data
    print('\nCleaning old data...')
    StudentExitApplication.query.delete()
    VisitRecord.query.delete()
    db.session.commit()

    # Create student leave records (last 30 days)
    print('\nCreating student leave records...')
    exit_reasons = ['Medical', 'Family', 'Competition', 'Visit', 'Other']
    destinations = ['City', 'Home', 'Hospital', 'Other City']

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

    db.session.commit()
    print(f'[OK] Created {StudentExitApplication.query.count()} student leave records')

    # Create visit records (last 30 days)
    print('\nCreating visit records...')
    visitor_types = ['alumni', 'parent', 'visitor']
    visit_purposes = [
        'Office Business',
        'Campus Visit',
        'Visit Teachers',
        'Meeting',
        'Paperwork',
        'Other'
    ]
    destinations = ['Admin Building', 'Teaching Building', 'Library', 'Lab Building', 'Gym', 'Cafeteria']

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
                verification_method=random.choice(['Face ID', 'QR Code', 'Manual'])
            )
            db.session.add(visit)

    db.session.commit()
    print(f'[OK] Created {VisitRecord.query.count()} visit records')

    # Statistics summary
    print('\n=== Test Data Summary ===')
    print(f'Total users: {User.query.count()}')
    print(f'  - Students: {User.query.filter_by(user_type="student").count()}')
    print(f'  - Alumni: {User.query.filter_by(user_type="alumni").count()}')
    print(f'  - Teachers: {User.query.filter_by(user_type="teacher").count()}')
    print(f'Student leave records: {StudentExitApplication.query.count()}')
    print(f'Visit records: {VisitRecord.query.count()}')

    # Visit records by type
    print('\nVisit records by type:')
    for vtype in ['alumni', 'parent', 'visitor']:
        count = VisitRecord.query.filter_by(visitor_type=vtype).count()
        type_names = {'alumni': 'Alumni', 'parent': 'Parent', 'visitor': 'Visitor'}
        print(f'  - {type_names.get(vtype, vtype)}: {count} visits')

    # Recent records
    print('\nLatest 5 visit records:')
    recent_visits = VisitRecord.query.order_by(VisitRecord.entry_time.desc()).limit(5).all()
    for v in recent_visits:
        user = User.query.get(v.user_id)
        visitor_name = user.real_name if user else 'Unknown'
        print(f'  - {visitor_name} ({v.visitor_type}) at {v.entry_time}, purpose: {v.visit_purpose}')

    print('\n=== Test data creation completed! ===')
