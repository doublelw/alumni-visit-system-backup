import sys, os
sys.path.append('backend')
from app import create_app, db
from app.models.user import User

app = create_app('development')
with app.app_context():
    print("=== 修复test_student班级关联 ===")

    # 获取test_student
    test_student = User.query.filter_by(username='test_student').first()
    if test_student:
        print(f"找到test_student: ID={test_student.id}, 姓名={test_student.real_name}")

        # 确保test_student关联到高三1班，和家长7
        test_student.class_id = "高三1班"
        test_student.grade = "高三"
        test_student.student_parent_id = 7  # 关联到张父

        db.session.commit()

        print(f"✓ 已更新test_student:")
        print(f"  - 班级: {test_student.class_id}")
        print(f"  - 年级: {test_student.grade}")
        print(f"  - 家长ID: {test_student.student_parent_id}")

    # 验证高三1班的班主任
    teacher1 = User.query.filter_by(user_type='teacher', class_id="高三1班").first()
    if teacher1:
        print(f"✓ 高三1班班主任: {teacher1.real_name} (ID: {teacher1.id})")
    else:
        print("❌ 未找到高三1班班主任")

    # 验证家长
    parent = User.query.get(7)
    if parent:
        print(f"✓ 关联家长: {parent.real_name} (ID: {parent.id})")

    # 验证完整的学生列表
    students = User.query.filter_by(user_type='student').all()
    print(f"\n=== 所有学生列表 ===")
    for student in students:
        parent_name = User.query.get(student.student_parent_id).real_name if student.student_parent_id else "无"
        print(f"- {student.real_name} (ID:{student.id}, 班级:{student.class_id}, 家长:{parent_name})")

    print("\n=== 修复完成 ===")
    print("现在可以刷新浏览器页面测试学生出校申请功能")