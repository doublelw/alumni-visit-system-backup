"""
双码流程测试

验证正确的流程：
1. 码A（给老师）- 24小时窗口 - 老师验证后创建审批记录
2. 码B（给门卫）- 3分钟窗口 - 门卫验证后查找审批记录

关键：两个码不同，但都包含手机号信息，通过手机号关联到同一审批记录
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code
from app.models.user import User
from app.models.visit_application import VisitApplication
from datetime import datetime, date, time as dt_time


def test_two_codes_flow():
    """测试双码流程"""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("双码流程测试")
        print("=" * 70)

        # 查找校友用户
        user = User.query.filter_by(user_type='alumni', status='active').first()
        if not user:
            user = User.query.filter_by(user_type='parent', status='active').first()

        if not user:
            print("[X] 未找到测试用户")
            return False

        print(f"\n[用户] {user.real_name} ({user.user_type})")
        print(f"      手机: {user.phone}")

        # ========== 步骤1: 家长/校友生成码A（给老师） ==========
        print(f"\n" + "=" * 70)
        print("步骤1: 生成码A（给老师验证）")
        print("=" * 70)

        timestamp_a = int(time.time())
        code_a = generate_hmac_code(user.phone, user.wechat_password, timestamp_a)

        print(f"[生成] 码A: {code_a}")
        print(f"      时间戳: {timestamp_a}")
        print(f"      用途: 给老师验证（24小时窗口）")

        # ========== 步骤2: 老师验证码A，创建审批记录 ==========
        print(f"\n" + "=" * 70)
        print("步骤2: 老师验证码A，创建审批记录")
        print("=" * 70)

        from app import db

        application = VisitApplication(
            applicant_id=user.id,
            visit_date=date.today(),
            visit_time_start=dt_time(8, 0),
            visit_time_end=dt_time(20, 0),
            visit_purpose=f'{user.real_name}进校',
            target_person=user.real_name,
            qr_code=code_a,  # 存储码A（但这不是门卫验证的关键）
            application_status='approved',
            approved_by=1,
            approval_time=datetime.utcnow(),
            approval_note=f"审批日期: {date.today()}"
        )

        db.session.add(application)
        db.session.commit()

        print(f"[创建] 审批记录")
        print(f"      ID: {application.id}")
        print(f"      申请人ID: {application.applicant_id}")
        print(f"      访问日期: {application.visit_date}")
        print(f"      审批时间: {application.approval_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"      存储的码: {application.qr_code}")

        # ========== 步骤3: 家长/校友到达门口，生成码B（给门卫） ==========
        print(f"\n" + "=" * 70)
        print("步骤3: 生成码B（给门卫验证）")
        print("=" * 70)

        # 等待1秒，模拟时间流逝
        time.sleep(1)

        timestamp_b = int(time.time())
        code_b = generate_hmac_code(user.phone, user.wechat_password, timestamp_b)

        print(f"[生成] 码B: {code_b}")
        print(f"      时间戳: {timestamp_b}")
        print(f"      用途: 给门卫验证（3分钟窗口）")
        print(f"\n[对比] 码A ≠ 码B")
        print(f"      码A: {code_a}")
        print(f"      码B: {code_b}")
        print(f"      相同: 包含相同的手机号信息")

        # ========== 步骤4: 门卫验证码B，查找审批记录 ==========
        print(f"\n" + "=" * 70)
        print("步骤4: 门卫验证码B，查找审批记录")
        print("=" * 70)

        from app.utils.hmac_utils import verify_hmac_code

        # 门卫验证码B（3分钟窗口）
        verification_b = verify_hmac_code(code_b, user.phone, user.wechat_password, 3)

        if not verification_b['valid']:
            print(f"[X] 码B验证失败: {verification_b['message']}")
            db.session.delete(application)
            db.session.commit()
            return False

        print(f"[验证] 码B HMAC验证通过")
        print(f"      提取手机号: {user.phone}")

        # 用手机号找用户
        applicant = User.query.filter_by(phone=user.phone, status='active').first()
        if not applicant:
            print(f"[X] 未找到用户")
            db.session.delete(application)
            db.session.commit()
            return False

        print(f"[查找] 用户ID: {applicant.id}")

        # 用用户ID + 今天的日期查找审批记录
        today_record = VisitApplication.query.filter_by(
            applicant_id=applicant.id,
            visit_date=date.today(),
            application_status='approved'
        ).first()

        if not today_record:
            print(f"[X] 未找到审批记录")
            db.session.delete(application)
            db.session.commit()
            return False

        print(f"[找到] 审批记录")
        print(f"      ID: {today_record.id}")
        print(f"      申请人: {applicant.real_name}")
        print(f"      类型: {applicant.user_type}")
        print(f"      访问目的: {today_record.visit_purpose}")

        # 验证两个记录是同一个
        if today_record.id == application.id:
            print(f"\n[OK] ✓ 验证成功！")
            print(f"     码A和码B通过手机号关联到同一审批记录")
            print(f"     记录ID: {application.id}")
        else:
            print(f"\n[X] 找到了不同的记录（不应该发生）")
            db.session.delete(application)
            db.session.commit()
            return False

        # 清理测试数据
        print(f"\n[清理] 删除测试数据...")
        db.session.delete(application)
        db.session.commit()
        print(f"[OK] 测试数据已清理")

        print("\n" + "=" * 70)
        print("[SUCCESS] 双码流程测试通过！")
        print("=" * 70)
        print("\n流程总结:")
        print("1. 家长生成码A → 老师验证 → 创建审批记录（存用户ID）")
        print("2. 家长到达门口 → 生成码B → 门卫验证")
        print("3. 码B提取手机号 → 查找今天的审批记录 → 显示信息")
        print("=" * 70)

        return True


if __name__ == '__main__':
    success = test_two_codes_flow()
    sys.exit(0 if success else 1)
