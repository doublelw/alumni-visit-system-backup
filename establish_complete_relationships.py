import sys, os
sys.path.append('backend')
from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication
from datetime import date, time

app = create_app('development')
with app.app_context():
    print("=== 建立student001、teacher001、parent001完整关联关系 ===")

    # 获取三个核心用户
    student001 = User.query.filter_by(username='student001').first()  # ID: 6
    teacher001 = User.query.filter_by(username='teacher001').first()  # ID: 5
    parent001 = User.query.filter_by(username='parent001').first()   # ID: 7

    print(f"找到用户:")
    print(f"  - 学生: {student001.real_name} (ID: {student001.id})")
    print(f"  - 教师: {teacher001.real_name} (ID: {teacher001.id})")
    print(f"  - 家长: {parent001.real_name} (ID: {parent001.id})")

    # 1. 建立学生-教师关联 (班级和班主任关系)
    # 将student001分配到teacher001的班级，并确保teacher001是班主任
    student001.class_id = "高三1班"
    student001.grade = "高三"
    student001.student_id = "STU001"  # 确保学号唯一

    teacher001.class_id = "高三1班"
    teacher001.is_class_teacher = True
    teacher001.employee_id = "TCH001"

    # 2. 建立学生-家长关联
    student001.student_parent_id = parent001.id

    # 3. 确保家长信息完整
    parent001.phone = "13800000007"
    parent001.email = "parent001@example.com"

    db.session.commit()

    print(f"\n✅ 关联关系已建立:")
    print(f"  - 学生 {student001.real_name} 属于 {student001.class_id}")
    print(f"  - 班主任 {teacher001.real_name} 负责 {teacher001.class_id}")
    print(f"  - 家长 {parent001.real_name} 是 {student001.real_name} 的家长")

    # 4. 清理重复的测试数据
    print(f"\n=== 清理重复的测试数据 ===")

    # 删除test_student (它与student001重复)
    test_student = User.query.filter_by(username='test_student').first()
    if test_student:
        print(f"删除重复学生: {test_student.real_name} (ID: {test_student.id})")
        # 删除相关的申请记录
        applications = StudentExitApplication.query.filter_by(student_id=test_student.id).all()
        for app in applications:
            db.session.delete(app)
            print(f"  - 删除申请记录 ID: {app.id}")
        db.session.delete(test_student)

    db.session.commit()

    # 5. 验证最终关联关系
    print(f"\n=== 最终验证 ===")
    print(f"学生 {student001.real_name}:")
    print(f"  - 班级: {student001.class_id}")
    print(f"  - 年级: {student001.grade}")
    print(f"  - 学号: {student001.student_id}")
    print(f"  - 家长ID: {student001.student_parent_id}")
    print(f"  - 家长姓名: {User.query.get(student001.student_parent_id).real_name}")

    print(f"\n班主任 {teacher001.real_name}:")
    print(f"  - 负责班级: {teacher001.class_id}")
    print(f"  - 是否班主任: {teacher001.is_class_teacher}")

    # 查看该班级的所有学生
    class_students = User.query.filter_by(
        user_type='student',
        class_id='高三1班'
    ).all()

    print(f"\n高三1班的所有学生:")
    for student in class_students:
        parent = User.query.get(student.student_parent_id) if student.student_parent_id else None
        parent_name = parent.real_name if parent else "无"
        print(f"  - {student.real_name} (学号: {student.student_id}, 家长: {parent_name})")

    print(f"\n=== 设置完成 ===")
    print(f"现在可以使用以下账号测试:")
    print(f"学生: student001 / student123")
    print(f"教师: teacher001 / teacher123")
    print(f"家长: parent001 / parent123")