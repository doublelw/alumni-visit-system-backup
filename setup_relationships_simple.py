import sys, os
sys.path.append('backend')
from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication

app = create_app('development')
with app.app_context():
    print("=== Clearing test applications ===")
    applications = StudentExitApplication.query.all()
    for app in applications:
        db.session.delete(app)
    db.session.commit()
    print(f"Deleted {len(applications)} applications")

    print("\n=== Setting up relationships ===")

    # Setup teacher 1 - Class 1
    teacher1 = User.query.get(5)
    if teacher1:
        teacher1.class_id = "高三1班"
        teacher1.is_class_teacher = True
        print(f"Teacher {teacher1.real_name} assigned to 高三1班")

    # Setup teacher 2 - Class 2
    teacher2 = User.query.get(8)
    if teacher2:
        teacher2.class_id = "高三2班"
        teacher2.is_class_teacher = True
        print(f"Teacher {teacher2.real_name} assigned to 高三2班")

    # Setup students
    student1 = User.query.get(6)
    if student1:
        student1.class_id = "高三1班"
        student1.grade = "高三"
        student1.student_parent_id = 7
        print(f"Student {student1.real_name} - 高三1班")

    student2 = User.query.get(9)
    if student2:
        student2.class_id = "高三1班"
        student2.grade = "高三"
        student2.student_parent_id = 7
        print(f"Student {student2.real_name} - 高三1班")

    student3 = User.query.get(10)
    if student3:
        student3.class_id = "高三2班"
        student3.grade = "高三"
        student3.student_parent_id = 11
        print(f"Student {student3.real_name} - 高三2班")

    test_student = User.query.get(12)
    if test_student:
        test_student.class_id = "高三1班"
        test_student.grade = "高三"
        test_student.student_parent_id = 7
        print(f"Test student {test_student.real_name} - 高三1班")

    db.session.commit()
    print("\n=== Relationships setup complete ===")

    print("\n=== Creating test applications ===")
    students = User.query.filter_by(user_type='student').all()

    for i, student in enumerate(students[:3]):
        application = StudentExitApplication(
            student_id=student.id,
            applicant_id=student.id,
            exit_date="2025-11-05",
            exit_time_start="14:00",
            exit_time_end="18:00",
            exit_reason="go home study",
            destination="home",
            emergency_contact="parent",
            emergency_phone=f"1380000000{i}"
        )
        db.session.add(application)
        print(f"Created application for {student.real_name}")

    db.session.commit()
    print("\n=== Test applications created ===")

    print("\n=== Final verification ===")
    apps = StudentExitApplication.query.all()
    print(f"Total applications in database: {len(apps)}")

    for app in apps:
        student = User.query.get(app.student_id)
        print(f"App {app.id}: {student.real_name} - {app.application_status}")

    print("\n=== Account summary ===")
    students = User.query.filter_by(user_type='student').all()
    teachers = User.query.filter_by(user_type='teacher').all()
    parents = User.query.filter_by(user_type='parent').all()

    print(f"Students: {len(students)}")
    print(f"Teachers: {len(teachers)}")
    print(f"Parents: {len(parents)}")

    print("\nTest accounts:")
    print("Student: test_student / student123")
    print("Admin: admin / admin123")
    print("Teacher: teacher001 / password123")