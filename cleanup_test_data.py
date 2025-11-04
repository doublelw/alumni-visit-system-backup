import sys, os
sys.path.append('backend')
from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication

app = create_app('development')
with app.app_context():
    print("=== 清理重复测试数据 ===")

    # 删除test_student及其相关申请
    test_student = User.query.filter_by(username='test_student').first()
    if test_student:
        print(f"删除学生: {test_student.real_name} (ID: {test_student.id})")

        # 删除相关的申请记录
        applications = StudentExitApplication.query.filter_by(student_id=test_student.id).all()
        for app in applications:
            print(f"  - 删除申请记录 ID: {app.id}")
            db.session.delete(app)

        db.session.delete(test_student)
        db.session.commit()
        print("test_student及相关申请已删除")

    # 解决学号重复问题 -李小华和测试学生都使用STU001
    lixiaohua = User.query.filter_by(username='student002').first()
    if lixiaohua and lixiaohua.student_id == 'STU001':
        lixiaohua.student_id = 'STU002'
        db.session.commit()
        print("李小华学号已更新为STU002")

    # 验证最终数据
    print("\n=== 最终用户列表 ===")
    users = User.query.all()
    for user in users:
        if user.user_type in ['student', 'teacher', 'parent']:
            print(f"{user.user_type}: {user.real_name} (ID:{user.id}, 用户名:{user.username})")
            if user.user_type == 'student':
                print(f"  - 班级: {user.class_id}, 学号: {user.student_id}, 家长ID: {user.student_parent_id}")
            elif user.user_type == 'teacher':
                print(f"  - 班级: {user.class_id}, 班主任: {user.is_class_teacher}")

    # 验证高三1班的完整关联
    print("\n=== 高三1班完整关联验证 ===")
    class_students = User.query.filter_by(
        user_type='student',
        class_id='高三1班'
    ).all()

    teacher = User.query.filter_by(
        user_type='teacher',
        class_id='高三1班',
        is_class_teacher=True
    ).first()

    if teacher:
        print(f"班主任: {teacher.real_name} (ID: {teacher.id})")
        print("班级学生:")
        for student in class_students:
            parent = User.query.get(student.student_parent_id) if student.student_parent_id else None
            parent_name = parent.real_name if parent else "无"
            print(f"  - {student.real_name} (学号:{student.student_id}, 家长:{parent_name})")

    print("\n=== 清理完成 ===")
    print("核心关联关系:")
    print("- student001 (张小明) ← teacher001 (李老师) ← parent001 (张父)")