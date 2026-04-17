import sys, os
sys.path.append('backend')
from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from datetime import date, time

app = create_app('development')
with app.app_context():
    print("=== Creating test applications with proper date types ===")

    students = User.query.filter_by(user_type='student').all()

    for i, student in enumerate(students[:3]):
        application = StudentExitApplication(
            student_id=student.id,
            applicant_id=student.id,
            exit_date=date(2025, 11, 5),  # Proper date object
            exit_time_start=time(14, 0),  # Proper time object
            exit_time_end=time(18, 0),    # Proper time object
            exit_reason="go home study",
            destination="home",
            emergency_contact="parent",
            emergency_phone=f"1380000000{i}"
        )
        db.session.add(application)
        print(f"Created application for {student.real_name}")

    db.session.commit()
    print("\n=== Test applications created successfully ===")

    print("\n=== Verification ===")
    apps = StudentExitApplication.query.all()
    print(f"Total applications: {len(apps)}")

    for app in apps:
        student = User.query.get(app.student_id)
        print(f"App {app.id}: {student.real_name} - {app.application_status} - {app.exit_date}")

    print("\n=== Final Account Summary ===")
    students = User.query.filter_by(user_type='student').all()
    teachers = User.query.filter_by(user_type='teacher').all()
    parents = User.query.filter_by(user_type='parent').all()

    print(f"Students: {len(students)}")
    print(f"Teachers: {len(teachers)}")
    print(f"Parents: {len(parents)}")

    print("\n=== Class Structure ===")
    classes = {}
    for student in students:
        class_name = student.class_id or '未分班'
        if class_name not in classes:
            classes[class_name] = []
        classes[class_name].append(student)

    for class_name, class_students in classes.items():
        print(f"\n{class_name}:")
        print(f"  Students: {len(class_students)}")
        for student in class_students:
            parent = User.query.get(student.student_parent_id) if student.student_parent_id else None
            parent_name = parent.real_name if parent else "No parent"
            print(f"    - {student.real_name} (Parent: {parent_name})")

    print("\n=== Test Accounts ===")
    print("Student: test_student / student123")
    print("Admin: admin / admin123")
    print("Teacher: teacher001 / password123")