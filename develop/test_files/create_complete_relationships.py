#!/usr/bin/env python3
"""
创建完整的学生-教师-家长关系数据
清空现有测试数据并建立合理的关联
"""
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.student_exit_application import StudentExitApplication

def clear_test_data():
    """清空现有的测试申请数据"""
    print("=== 清空现有测试申请数据 ===")

    # 删除所有学生出校申请
    applications = StudentExitApplication.query.all()
    for app in applications:
        db.session.delete(app)

    db.session.commit()
    print(f"已删除 {len(applications)} 个申请记录")

def create_complete_relationships():
    """创建完整的学生-教师-家长关系"""
    print("\n=== 创建完整的关系数据 ===")

    # 更新现有用户，确保关系正确

    # 1. 建立班主任与学生关系
    # 高三1班班主任 (ID: 5)
    teacher1 = User.query.get(5)
    if teacher1:
        teacher1.class_id = "高三1班"
        teacher1.is_class_teacher = True
        print(f"✓ 班主任 {teacher1.real_name} 负责 高三1班")

    # 高三2班班主任 (ID: 8)
    teacher2 = User.query.get(8)
    if teacher2:
        teacher2.class_id = "高三2班"
        teacher2.is_class_teacher = True
        print(f"✓ 班主任 {teacher2.real_name} 负责 高三2班")

    # 2. 确保学生班级和班主任关系
    # 学生1 (ID: 6) - 高三1班
    student1 = User.query.get(6)
    if student1:
        student1.class_id = "高三1班"
        student1.grade = "高三"
        # 确保有家长关联 (已有家长ID 7)
        if not student1.student_parent_id:
            student1.student_parent_id = 7
        print(f"✓ 学生 {student1.real_name} - 高三1班")

    # 学生2 (ID: 9) - 高三1班
    student2 = User.query.get(9)
    if student2:
        student2.class_id = "高三1班"
        student2.grade = "高三"
        # 确保有家长关联 (已有家长ID 7)
        if not student2.student_parent_id:
            student2.student_parent_id = 7
        print(f"✓ 学生 {student2.real_name} - 高三1班")

    # 学生3 (ID: 10) - 高三2班
    student3 = User.query.get(10)
    if student3:
        student3.class_id = "高三2班"
        student3.grade = "高三"
        # 确保有家长关联 (已有家长ID 11)
        if not student3.student_parent_id:
            student3.student_parent_id = 11
        print(f"✓ 学生 {student3.real_name} - 高三2班")

    # 3. 为测试学生(ID: 12)也建立完整关系
    test_student = User.query.get(12)
    if test_student:
        test_student.class_id = "高三1班"  # 放到高三1班
        test_student.grade = "高三"
        # 如果没有家长，为ta创建一个家长或关联现有家长
        if not test_student.student_parent_id:
            # 可以关联现有家长或创建新的
            test_student.student_parent_id = 7  # 暂时关联到家长7
        print(f"✓ 测试学生 {test_student.real_name} - 高三1班")

    # 4. 更新家长信息，确保反向关联
    parent1 = User.query.get(7)  # 家长1
    if parent1:
        parent1.user_type = 'parent'
        print(f"✓ 家长 {parent1.real_name}")

    parent2 = User.query.get(11)  # 家长2
    if parent2:
        parent2.user_type = 'parent'
        print(f"✓ 家长 {parent2.real_name}")

    db.session.commit()
    print("\n✅ 关系数据创建完成!")

def verify_relationships():
    """验证关系数据的合理性"""
    print("\n=== 验证关系数据 ===")

    students = User.query.filter_by(user_type='student').all()
    teachers = User.query.filter_by(user_type='teacher').all()
    parents = User.query.filter_by(user_type='parent').all()

    print(f"\n学生数量: {len(students)}")
    print(f"教师数量: {len(teachers)}")
    print(f"家长数量: {len(parents)}")

    # 检查每个班级
    classes = {}
    for student in students:
        class_name = student.class_id or '未分班'
        if class_name not in classes:
            classes[class_name] = {'students': [], 'parents': set()}
        classes[class_name]['students'].append(student)
        if student.student_parent_id:
            classes[class_name]['parents'].add(student.student_parent_id)

    # 检查班主任分配
    class_teachers = {}
    for teacher in teachers:
        if teacher.is_class_teacher and teacher.class_id:
            class_teachers[teacher.class_id] = teacher

    print("\n班级情况:")
    for class_name, data in classes.items():
        print(f"\n班级: {class_name}")
        print(f"  学生数: {len(data['students'])}")
        for student in data['students']:
            parent_name = User.query.get(student.student_parent_id).real_name if student.student_parent_id else "无"
            print(f"    - {student.real_name} (家长: {parent_name})")

        teacher = class_teachers.get(class_name)
        if teacher:
            print(f"  班主任: {teacher.real_name}")
        else:
            print(f"  ⚠️ 缺少班主任")

def create_test_applications():
    """创建一些测试申请数据"""
    print("\n=== 创建测试申请数据 ===")

    # 获取学生
    students = User.query.filter_by(user_type='student').all()

    for i, student in enumerate(students[:3]):  # 为前3个学生创建申请
        application = StudentExitApplication(
            student_id=student.id,
            applicant_id=student.id,  # 学生自己申请
            exit_date="2025-11-05",
            exit_time_start="14:00",
            exit_time_end="18:00",
            exit_reason="回家复习",
            destination="家里",
            emergency_contact="家长联系人",
            emergency_phone="1380000000" + str(i)
        )
        db.session.add(application)
        print(f"✓ 为学生 {student.real_name} 创建申请")

    db.session.commit()
    print("✅ 测试申请创建完成!")

def main():
    app = create_app('development')

    with app.app_context():
        try:
            # 1. 清理现有测试数据
            clear_test_data()

            # 2. 创建完整关系数据
            create_complete_relationships()

            # 3. 验证关系数据
            verify_relationships()

            # 4. 创建测试申请
            create_test_applications()

            print("\n🎉 所有操作完成!")
            print("\n现在可以使用以下账号测试:")
            print("学生账号: test_student / student123")
            print("管理员账号: admin / admin123")
            print("班主任账号: teacher001 / password123 (高三1班)")

        except Exception as e:
            print(f"❌ 操作失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == "__main__":
    main()