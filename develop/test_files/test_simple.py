import sys, os
sys.path.append('backend')
from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from datetime import datetime, date, time

app = create_app('development')
with app.app_context():
    student = User.query.filter_by(username='test_student').first()
    print('Student found:', student.real_name if student else 'None')

    if student:
        try:
            application = StudentExitApplication(
                student_id=student.id,
                applicant_id=student.id,
                exit_date=date(2025, 11, 5),
                exit_time_start=time(14, 0),
                exit_time_end=time(18, 0),
                exit_reason='回家复习',
                destination='家里'
            )
            db.session.add(application)
            db.session.commit()
            print('SUCCESS: Application created with ID:', application.id)
        except Exception as e:
            print('ERROR:', str(e))
            import traceback
            traceback.print_exc()
            db.session.rollback()