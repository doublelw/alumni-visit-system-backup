"""
门卫验证修复测试

完整流程测试：
1. 家长/校友生成码
2. 老师验证（24小时窗口，自动审批）
3. 门卫验证（3分钟窗口）
"""
import sys
import os
import time

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code
from app.models.user import User
from app.models.visit_application import VisitApplication


def test_complete_flow():
    """测试完整流程：生成 → 老师审批 → 门卫验证"""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("门卫验证完整流程测试")
        print("=" * 70)

        # 步骤1：获取校友用户
        user = User.query.filter_by(
            phone='13900002001',
            user_type='alumni',
            status='active'
        ).first()

        if not user:
            print("\n[X] 未找到测试用户，请先创建校友账号")
            return

        print(f"\n[OK] 找到用户: {user.real_name} ({user.user_type})")
        print(f"   手机: {user.phone}")
        print(f"   密码: {user.wechat_password[:3]}***")

        # 步骤2：生成HMAC码（模拟家长/校友操作）
        timestamp = int(time.time())
        code = generate_hmac_code(user.phone, user.wechat_password, timestamp)

        print(f"\n[步骤1] 生成动态码")
        print(f"   时间戳: {timestamp}")
        print(f"   6位码: {code}")

        # 步骤3：老师验证（24小时窗口）
        print(f"\n[步骤2] 老师验证（24小时窗口）")
        from app.utils.hmac_utils import verify_hmac_code

        teacher_result = verify_hmac_code(code, user.phone, user.wechat_password, 24*60)
        print(f"   验证结果: {teacher_result['valid']}")
        print(f"   消息: {teacher_result['message']}")

        if not teacher_result['valid']:
            print(f"\n[X] 老师验证失败，无法继续")
            return

        # 步骤4：创建审批记录（模拟老师自动审批）
        from datetime import datetime, date, time as dt_time

        approval_time = datetime.now()
        application = VisitApplication(
            applicant_id=user.id,
            visit_date=date.today(),
            visit_time_start=dt_time(8, 0),
            visit_time_end=dt_time(20, 0),
            visit_purpose='校友进校',
            target_person=user.real_name,
            qr_code=code,
            application_status='approved',
            approved_by=1,  # 假设老师ID是1
            approval_time=approval_time,
            approval_note=f"审批日期: {date.today()}"
        )

        from app import db
        db.session.add(application)
        db.session.commit()

        print(f"   [OK] 审批记录已创建")
        print(f"   审批时间: {approval_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 步骤5：门卫验证（3分钟窗口）
        print(f"\n[步骤3] 门卫验证（3分钟窗口）")

        # 查询审批记录
        approved_app = VisitApplication.query.filter_by(
            qr_code=code,
            application_status='approved'
        ).first()

        if not approved_app:
            print(f"   [X] 未找到审批记录")
            return

        # 检查时间差
        time_diff = datetime.utcnow() - approved_app.approval_time
        time_diff_seconds = time_diff.total_seconds()

        print(f"   审批时间: {approved_app.approval_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   当前时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   时间差: {int(time_diff_seconds)} 秒")

        if time_diff_seconds <= 180:
            print(f"   [OK] 验证成功！在3分钟窗口内")
            print(f"   申请人: {user.real_name}")
            print(f"   类型: {user.user_type}")
            print(f"   访问日期: {approved_app.visit_date}")
            print(f"   访问目的: {approved_app.visit_purpose}")
        else:
            print(f"   [X] 验证失败！超过3分钟窗口")

        # 清理测试数据
        print(f"\n[清理] 测试数据")
        db.session.delete(application)
        db.session.commit()
        print(f"   [OK] 测试数据已清理")

        print("\n" + "=" * 70)
        print("测试完成")
        print("=" * 70)


def test_guard_verify_boundary():
    """测试边界情况：刚好3分钟、超过3分钟"""
    app = create_app()

    with app.app_context():
        print("\n" + "=" * 70)
        print("边界测试：3分钟时间窗口")
        print("=" * 70)

        user = User.query.filter_by(phone='13900002001').first()
        if not user:
            print("[X] 未找到测试用户")
            return

        from app import db
        from datetime import datetime, timedelta, date, time as dt_time

        # 测试1: 刚好在3分钟内
        print("\n[测试1] 审批后2分钟（应该成功）")
        code = generate_hmac_code(user.phone, user.wechat_password, int(time.time()))

        approval_time_2min = datetime.utcnow() - timedelta(minutes=2)
        app1 = VisitApplication(
            applicant_id=user.id,
            visit_date=date.today(),
            visit_time_start=dt_time(8, 0),
            visit_time_end=dt_time(20, 0),
            visit_purpose='测试',
            target_person=user.real_name,
            qr_code=code,
            application_status='approved',
            approved_by=1,
            approval_time=approval_time_2min
        )
        db.session.add(app1)
        db.session.commit()

        time_diff = (datetime.utcnow() - approval_time_2min).total_seconds()
        print(f"   时间差: {int(time_diff)} 秒")
        print(f"   结果: {'[OK] 成功' if time_diff <= 180 else '[X] 失败'}")

        db.session.delete(app1)
        db.session.commit()

        # 测试2: 超过3分钟
        print("\n[测试2] 审批后4分钟（应该失败）")
        code = generate_hmac_code(user.phone, user.wechat_password, int(time.time()))

        approval_time_4min = datetime.utcnow() - timedelta(minutes=4)
        app2 = VisitApplication(
            applicant_id=user.id,
            visit_date=date.today(),
            visit_time_start=dt_time(8, 0),
            visit_time_end=dt_time(20, 0),
            visit_purpose='测试',
            target_person=user.real_name,
            qr_code=code,
            application_status='approved',
            approved_by=1,
            approval_time=approval_time_4min
        )
        db.session.add(app2)
        db.session.commit()

        time_diff = (datetime.utcnow() - approval_time_4min).total_seconds()
        print(f"   时间差: {int(time_diff)} 秒")
        print(f"   结果: {'[OK] 成功' if time_diff <= 180 else '[X] 失败（预期）'}")

        db.session.delete(app2)
        db.session.commit()

        # 测试3: 刚好3分钟
        print("\n[测试3] 审批后3分钟（边界情况）")
        code = generate_hmac_code(user.phone, user.wechat_password, int(time.time()))

        approval_time_3min = datetime.utcnow() - timedelta(seconds=180)
        app3 = VisitApplication(
            applicant_id=user.id,
            visit_date=date.today(),
            visit_time_start=dt_time(8, 0),
            visit_time_end=dt_time(20, 0),
            visit_purpose='测试',
            target_person=user.real_name,
            qr_code=code,
            application_status='approved',
            approved_by=1,
            approval_time=approval_time_3min
        )
        db.session.add(app3)
        db.session.commit()

        time_diff = (datetime.utcnow() - approval_time_3min).total_seconds()
        print(f"   时间差: {int(time_diff)} 秒")
        print(f"   结果: {'[OK] 成功（边界）' if time_diff <= 180 else '[X] 失败'}")

        db.session.delete(app3)
        db.session.commit()

        print("\n" + "=" * 70)
        print("边界测试完成")
        print("=" * 70)


if __name__ == '__main__':
    test_complete_flow()
    test_guard_verify_boundary()
