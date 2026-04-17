"""
简单测试组织关联功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.organization import Organization

def test_simple_relationships():
    """简单测试组织关联功能"""
    try:
        print("=== 简单测试组织关联功能 ===")

        # 创建应用实例
        app = create_app()

        with app.app_context():
            print("1. 测试组织模型...")

            # 创建测试组织
            test_org = Organization.query.filter_by(code="SIMPLE_TEST").first()
            if not test_org:
                test_org = Organization(
                    name="简单测试组织",
                    code="SIMPLE_TEST",
                    org_type="class",
                    description="用于简单测试的组织"
                )
                db.session.add(test_org)
                db.session.commit()
                print(f"创建测试组织: {test_org.name} (ID: {test_org.id})")

            print("2. 测试用户关联...")

            # 获取一个老师用户
            teacher = User.query.filter_by(user_type='teacher').first()
            if not teacher:
                print("没有找到老师用户，跳过测试")
                return True

            print(f"找到老师: {teacher.real_name} (ID: {teacher.id})")

            # 设置老师为班主任
            test_org.class_teacher_id = teacher.id
            db.session.commit()

            print("3. 验证关联...")

            # 验证班主任关联
            updated_org = Organization.query.get(test_org.id)
            if updated_org.class_teacher:
                print(f"班主任设置成功: {updated_org.class_teacher.real_name}")
            else:
                print("失败: 班主任设置失败")
                return False

            # 设置用户的组织
            teacher.organization_id = test_org.id
            db.session.commit()

            # 验证用户组织关联
            updated_teacher = User.query.get(teacher.id)
            if updated_teacher.organization:
                print(f"老师所属组织: {updated_teacher.organization.name}")
            else:
                print("失败: 用户组织关联设置失败")
                return False

            print("4. 测试to_dict方法...")

            # 测试组织的to_dict方法
            org_dict = updated_org.to_dict(include_users=True)
            print(f"组织信息包含班主任: {'class_teacher' in org_dict}")
            if 'class_teacher' in org_dict and org_dict['class_teacher']:
                print(f"班主任信息: {org_dict['class_teacher']['real_name']}")

            # 测试用户的to_dict方法
            user_dict = updated_teacher.to_dict()
            print(f"用户信息包含组织: {'organization' in user_dict}")
            if 'organization' in user_dict and user_dict['organization']:
                print(f"组织信息: {user_dict['organization']['name']}")

            print("\n=== 简单测试完成 ===")
            return True

    except Exception as e:
        print(f"失败: 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_relationships()
    if success:
        print("\n简单组织关联功能测试通过！")
    else:
        print("\n测试失败，请查看上述错误信息！")
        sys.exit(1)
