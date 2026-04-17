"""
HMAC调试脚本 - 测试生成和验证
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code, verify_hmac_code
from app.models.user import User

def test_hmac():
    """测试HMAC生成和验证"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("HMAC 调试测试")
        print("=" * 60)

        # 获取测试用户
        users = User.query.filter(
            User.user_type.in_(['parent', 'student', 'alumni']),
            User.status == 'active'
        ).all()

        print(f"\n找到 {len(users)} 个有效用户:")
        print("-" * 60)

        for user in users[:5]:  # 只显示前5个
            print(f"\n用户: {user.real_name}")
            print(f"  手机: {user.phone}")
            print(f"  类型: {user.user_type}")
            print(f"  密码: {user.wechat_password}")

            if user.phone and user.wechat_password:
                # 生成码
                code = generate_hmac_code(user.phone, user.wechat_password)
                print(f"  生成的码: {code}")

                # 立即验证
                verification = verify_hmac_code(code, user.phone, user.wechat_password, 24*60)
                print(f"  验证结果: {verification}")

                if verification['valid']:
                    print(f"  ✅ 验证通过！")
                else:
                    print(f"  ❌ 验证失败: {verification['message']}")

        print("\n" + "=" * 60)
        print("测试特定场景")
        print("=" * 60)

        # 测试场景1：家长入校
        print("\n场景1: 家长入校")
        parent_phone = "13900002002"
        parent_password = "88"
        code1 = generate_hmac_code(parent_phone, parent_password)
        print(f"  手机: {parent_phone}")
        print(f"  密码: {parent_password}")
        print(f"  生成的码: {code1}")
        verify1 = verify_hmac_code(code1, parent_phone, parent_password, 24*60)
        print(f"  验证: {verify1}")

        # 测试场景2：学生请假
        print("\n场景2: 学生请假")
        stu_phone = parent_phone + "STU"
        code2 = generate_hmac_code(stu_phone, parent_password)
        print(f"  手机: {stu_phone}")
        print(f"  密码: {parent_password}")
        print(f"  生成的码: {code2}")
        verify2 = verify_hmac_code(code2, stu_phone, parent_password, 24*60)
        print(f"  验证: {verify2}")

        print("\n" + "=" * 60)

if __name__ == '__main__':
    test_hmac()
