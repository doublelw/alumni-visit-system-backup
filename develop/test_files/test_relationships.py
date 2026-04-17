"""
测试用户关联功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.organization import Organization

def test_relationships():
    """测试用户关联功能"""
    try:
        print("=== 测试用户关联功能 ===")

        # 创建应用实例
        app = create_app()

        with app.app_context():
            print("1. 获取现有用户...")

            # 获取老师、学生、家长用户
            teacher = User.query.filter_by(user_type='teacher').first()
            student = User.query.filter_by(user_type='student').first()
            parent = User.query.filter_by(user_type='parent').first()

            if not teacher:
                print("创建测试老师...")
                teacher = User(
                    username="test_teacher_rel",
                    real_name="测试老师",
                    email="test_teacher@example.com",
                    phone="13800020001",
                    user_type="teacher",
                    status="active"
                )
                teacher.set_password("123456")
                db.session.add(teacher)
                db.session.commit()

            if not student:
                print("创建测试学生...")
                student = User(
                    username="test_student_rel",
                    real_name="测试学生",
                    email="test_student@example.com",
                    phone="13800040001",
                    user_type="student",
                    status="active"
                )
                student.set_password("123456")
                db.session.add(student)
                db.session.commit()

            if not parent:
                print("创建测试家长...")
                parent = User(
                    username="test_parent_rel",
                    real_name="测试家长",
                    email="test_parent@example.com",
                    phone="13800030001",
                    user_type="parent",
                    status="active"
                )
                parent.set_password("123456")
                db.session.add(parent)
                db.session.commit()

            print(f"老师: {teacher.real_name} (ID: {teacher.id})")
            print(f"学生: {student.real_name} (ID: {student.id})")
            print(f"家长: {parent.real_name} (ID: {parent.id})")

            print("\n2. 创建测试组织...")

            # 创建测试班级
            test_class = Organization.query.filter_by(code="TEST_CLASS_REL").first()
            if not test_class:
                test_class = Organization(
                    name="测试班级关联",
                    code="TEST_CLASS_REL",
                    org_type="class",
                    description="用于测试关联功能的班级"
                )
                db.session.add(test_class)
                db.session.commit()

            print(f"测试班级: {test_class.name} (ID: {test_class.id})")

            print("\n3. 测试组织-用户关联...")

            # 设置班主任和年级组长
            test_class.class_teacher_id = teacher.id
            test_class.head_teacher_id = teacher.id  # 暂时设为同一个老师
            db.session.commit()

            # 验证关联
            updated_class = Organization.query.get(test_class.id)
            class_teacher = updated_class.class_teacher
            head_teacher = updated_class.head_teacher

            if class_teacher:
                print(f"班主任设置成功: {class_teacher.real_name}")
            else:
                print("失败: 班主任设置失败")

            if head_teacher:
                print(f"年级组长设置成功: {head_teacher.real_name}")
            else:
                print("失败: 年级组长设置失败")

            print("\n4. 测试家长-学生关联...")

            # 设置家长-学生关系
            parent.parent_student_id = student.id
            student.student_parent_id = parent.id
            db.session.commit()

            # 验证关联
            updated_parent = User.query.get(parent.id)
            updated_student = User.query.get(student.id)

            # 检查家长的学生
            if updated_parent.parent_students:
                for child in updated_parent.parent_students:
                    print(f"家长 {updated_parent.real_name} 的学生: {child.real_name}")
            else:
                print("失败: 家长-学生关联设置失败")

            # 检查学生的家长
            if updated_student.student_parents:
                for par in updated_student.student_parents:
                    print(f"学生 {updated_student.real_name} 的家长: {par.real_name}")
            else:
                print("失败: 学生-家长关联设置失败")

            print("\n5. 测试用户组织关联...")

            # 设置用户的组织
            student.organization_id = test_class.id
            teacher.organization_id = test_class.id
            db.session.commit()

            # 验证关联
            updated_student = User.query.get(student.id)
            updated_teacher = User.query.get(teacher.id)

            if updated_student.organization:
                print(f"学生 {updated_student.real_name} 所属组织: {updated_student.organization.name}")
            else:
                print("失败: 学生组织关联设置失败")

            if updated_teacher.organization:
                print(f"老师 {updated_teacher.real_name} 所属组织: {updated_teacher.organization.name}")
            else:
                print("失败: 老师组织关联设置失败")

            print("\n6. 测试to_dict方法包含关系信息...")

            # 测试学生的完整信息
            student_dict = updated_student.to_dict(include_sensitive=True)
            print(f"学生完整信息包含组织: {'organization' in student_dict}")
            print(f"学生完整信息包含家长: {'parents' in student_dict}")

            # 测试组织的完整信息
            org_dict = updated_class.to_dict(include_users=True)
            print(f"组织完整信息包含班主任: {'class_teacher' in org_dict}")
            print(f"组织完整信息包含年级组长: {'head_teacher' in org_dict}")

            print("\n=== 测试完成 ===")
            return True

    except Exception as e:
        print(f"失败: 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

if __name__ == "__main__":
    success = test_relationships()
    if success:
        print("\n用户关联功能测试通过！")
    else:
        print("\n测试失败，请查看上述错误信息！")
        sys.exit(1)
