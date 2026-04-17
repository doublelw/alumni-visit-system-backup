"""
检查组织机构字段是否添加成功
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from sqlalchemy import text

def check_organization_fields():
    """检查组织机构字段"""
    try:
        print("=== 检查组织机构字段 ===")

        # 创建应用实例
        app = create_app()

        with app.app_context():
            print("1. 检查数据库连接...")
            try:
                db.session.execute(text("SELECT 1"))
                print("成功: 数据库连接正常")
            except Exception as e:
                print(f"失败: 数据库连接失败: {e}")
                return False

            print("\n2. 检查organizations表结构...")
            try:
                # 获取表结构信息
                result = db.session.execute(text("PRAGMA table_info(organizations)"))
                columns = [row[1] for row in result.fetchall()]
                print(f"当前字段: {', '.join(columns)}")

                # 检查新增字段
                required_fields = ["class_teacher_id", "head_teacher_id", "leader_id"]
                missing_fields = []

                for field in required_fields:
                    if field in columns:
                        print(f"成功: {field} 字段存在")
                    else:
                        print(f"失败: {field} 字段不存在")
                        missing_fields.append(field)

                if missing_fields:
                    print(f"警告: 缺少字段: {', '.join(missing_fields)}")
                    return False
                else:
                    print("成功: 所有必需字段都存在")

            except Exception as e:
                print(f"失败: 检查表结构失败: {e}")
                return False

            print("\n3. 测试Organization模型...")
            try:
                from app.models.organization import Organization

                # 尝试创建一个测试组织
                test_org = Organization(
                    name="测试班级",
                    code="TEST_CLASS",
                    org_type="class"
                )

                # 测试新字段
                test_org.class_teacher_id = None
                test_org.head_teacher_id = None
                test_org.leader_id = None

                print("成功: Organization模型新字段测试通过")

            except Exception as e:
                print(f"失败: Organization模型测试失败: {e}")
                return False

            print("\n=== 检查完成 ===")
            return True

    except Exception as e:
        print(f"失败: 检查过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = check_organization_fields()
    if success:
        print("\n组织机构字段检查通过！")
    else:
        print("\n检查发现问题，请查看上述错误信息！")
        sys.exit(1)