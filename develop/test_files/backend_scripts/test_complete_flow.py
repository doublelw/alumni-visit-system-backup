"""
完整流程测试 - 模拟生成码和验证码
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code, verify_hmac_code
from app.models.user import User
import time

def test_complete_flow():
    """测试完整的生成和验证流程"""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("完整流程测试 - 模拟家长生成码和老师验证")
        print("=" * 70)

        # 获取一个测试用户
        user = User.query.filter_by(phone='13900002001').first()

        if not user:
            print("❌ 未找到测试用户 13900002001")
            return

        print(f"\n[INFO] 测试用户信息:")
        print(f"  姓名: {user.real_name}")
        print(f"  手机: {user.phone}")
        print(f"  类型: {user.user_type}")
        print(f"  密码: {user.wechat_password}")
        print(f"  状态: {user.status}")

        # 步骤1: 家长生成码
        print(f"\n" + "=" * 70)
        print("步骤1: 家长生成入校码")
        print("=" * 70)

        code = generate_hmac_code(user.phone, user.wechat_password)
        print(f"[OK] 生成的码: {code}")
        print(f"   使用手机: {user.phone}")
        print(f"   使用密码: {user.wechat_password}")

        # 步骤2: 立即验证（应该成功）
        print(f"\n" + "=" * 70)
        print("步骤2: 老师立即验证（应该成功）")
        print("=" * 70)

        verification = verify_hmac_code(code, user.phone, user.wechat_password, 24*60)
        print(f"验证结果: {verification}")

        if verification['valid']:
            print(f"[OK] 验证成功！")
            print(f"   时间戳: {verification['timestamp']}")
        else:
            print(f"[FAIL] 验证失败: {verification['message']}")

        # 步骤3: 等待5秒后再次验证（应该仍然成功）
        print(f"\n" + "=" * 70)
        print("步骤3: 等待5秒后再次验证（应该仍然成功）")
        print("=" * 70)

        print("[INFO] 等待5秒...")
        time.sleep(5)

        verification2 = verify_hmac_code(code, user.phone, user.wechat_password, 24*60)
        print(f"验证结果: {verification2}")

        if verification2['valid']:
            print(f"[OK] 验证成功！")
            print(f"   时间戳: {verification2['timestamp']}")
        else:
            print(f"[FAIL] 验证失败: {verification2['message']}")

        # 步骤4: 测试学生请假模式
        print(f"\n" + "=" * 70)
        print("步骤4: 测试学生请假模式（phone+STU）")
        print("=" * 70)

        stu_phone = user.phone + 'STU'
        code_stu = generate_hmac_code(stu_phone, user.wechat_password)
        print(f"[OK] 学生请假码: {code_stu}")
        print(f"   使用手机: {stu_phone}")
        print(f"   使用密码: {user.wechat_password}")

        # 验证学生请假码
        verification_stu = verify_hmac_code(code_stu, stu_phone, user.wechat_password, 24*60)
        print(f"验证结果: {verification_stu}")

        if verification_stu['valid']:
            print(f"[OK] 学生请假码验证成功！")
        else:
            print(f"[FAIL] 学生请假码验证失败: {verification_stu['message']}")

        # 步骤5: 测试错误码
        print(f"\n" + "=" * 70)
        print("步骤5: 测试错误的码（应该失败）")
        print("=" * 70)

        wrong_code = "999999"
        verification_wrong = verify_hmac_code(wrong_code, user.phone, user.wechat_password, 24*60)
        print(f"错误的码: {wrong_code}")
        print(f"验证结果: {verification_wrong}")

        if not verification_wrong['valid']:
            print(f"[OK] 正确拒绝了错误的码")
        else:
            print(f"[FAIL] 错误：错误的码竟然通过了！")

        # 步骤6: 模拟老师验证流程（遍历所有用户）
        print(f"\n" + "=" * 70)
        print("步骤6: 模拟老师验证流程（遍历所有用户）")
        print("=" * 70)

        all_users = User.query.filter(
            User.user_type.in_(['parent', 'student', 'alumni']),
            User.status == 'active'
        ).all()

        print(f"找到 {len(all_users)} 个有效用户")

        matched_user = None
        matched_timestamp = None
        code_type = None

        for test_user in all_users:
            if not test_user.phone or not test_user.wechat_password:
                continue

            # 尝试纯phone（家长入校/校友入校）
            verification_parent = verify_hmac_code(
                code, test_user.phone, test_user.wechat_password, 24*60
            )

            if verification_parent['valid']:
                matched_user = test_user
                matched_timestamp = verification_parent['timestamp']
                code_type = 'parent' if test_user.user_type in ['parent', 'alumni'] else 'student'
                print(f"[OK] 匹配成功！")
                print(f"   用户: {test_user.real_name} ({test_user.user_type})")
                print(f"   手机: {test_user.phone}")
                print(f"   类型: {code_type}")
                break

            # 尝试phone+'STU'（学生请假）
            phone_stu = test_user.phone + 'STU'
            verification_student = verify_hmac_code(
                code, phone_stu, test_user.wechat_password, 24*60
            )

            if verification_student['valid']:
                matched_user = test_user
                matched_timestamp = verification_student['timestamp']
                code_type = 'student-leave'
                print(f"[OK] 匹配成功（学生请假）！")
                print(f"   家长: {test_user.real_name}")
                print(f"   手机: {phone_stu}")
                print(f"   类型: {code_type}")
                break

        if not matched_user:
            print(f"[FAIL] 未找到匹配的用户")
        else:
            print(f"\n[SUCCESS] 完整流程测试成功！")

        print("\n" + "=" * 70)

if __name__ == '__main__':
    test_complete_flow()
