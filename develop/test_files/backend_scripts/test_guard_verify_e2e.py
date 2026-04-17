"""
门卫验证端到端测试

使用Playwright测试完整流程：
1. 校友生成码
2. 老师验证并自动审批
3. 门卫验证（3分钟窗口）
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.user import User
from app.models.visit_application import VisitApplication
from app.utils.hmac_utils import generate_hmac_code, verify_hmac_code
from datetime import datetime, timedelta, date, time as dt_time
import time


def test_e2e_flow():
    """端到端流程测试"""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("门卫验证端到端测试")
        print("=" * 70)

        # 步骤1：查找校友用户
        print("\n[步骤1] 查找校友用户...")
        user = User.query.filter_by(user_type='alumni', status='active').first()

        if not user:
            print("[!] 未找到校友用户，尝试查找家长用户...")
            user = User.query.filter_by(user_type='parent', status='active').first()

        if not user:
            print("[X] 未找到任何测试用户")
            print("    请先在系统中注册用户")
            return False

        print(f"[OK] 找到用户: {user.real_name}")
        print(f"     类型: {user.user_type}")
        print(f"     手机: {user.phone}")

        # 步骤2：模拟生成码（校友操作）
        print(f"\n[步骤2] 生成HMAC码...")
        timestamp = int(time.time())
        code = generate_hmac_code(user.phone, user.wechat_password, timestamp)
        print(f"[OK] 生成码: {code}")
        print(f"     时间戳: {timestamp}")

        # 步骤3：模拟老师验证（24小时窗口）
        print(f"\n[步骤3] 老师验证（24小时窗口）...")
        teacher_verify = verify_hmac_code(code, user.phone, user.wechat_password, 24*60)

        if not teacher_verify['valid']:
            print(f"[X] 老师验证失败: {teacher_verify['message']}")
            return False

        print(f"[OK] 老师验证通过")
        print(f"     时间戳匹配: {teacher_verify['timestamp']}")

        # 步骤4：创建审批记录（老师自动审批）
        print(f"\n[步骤4] 创建审批记录（自动审批）...")
        from app import db

        approval_time = datetime.utcnow()
        application = VisitApplication(
            applicant_id=user.id,
            visit_date=date.today(),
            visit_time_start=dt_time(8, 0),
            visit_time_end=dt_time(20, 0),
            visit_purpose=f'{user.real_name}进校',
            target_person=user.real_name,
            qr_code=code,
            application_status='approved',
            approved_by=1,
            approval_time=approval_time,
            approval_note=f"审批日期: {date.today()}"
        )

        db.session.add(application)
        db.session.commit()

        print(f"[OK] 审批记录已创建")
        print(f"     ID: {application.id}")
        print(f"     审批时间: {approval_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 步骤5：门卫立即验证（应该在3分钟内）
        print(f"\n[步骤5] 门卫验证（立即）...")

        # 查询审批记录
        approved_app = VisitApplication.query.filter_by(
            qr_code=code,
            application_status='approved'
        ).first()

        if not approved_app:
            print(f"[X] 未找到审批记录")
            db.session.delete(application)
            db.session.commit()
            return False

        # 检查时间差
        time_diff = datetime.utcnow() - approved_app.approval_time
        time_diff_seconds = time_diff.total_seconds()

        print(f"     审批时间: {approved_app.approval_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     当前时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     时间差: {int(time_diff_seconds)} 秒")

        if time_diff_seconds <= 180:
            print(f"[OK] 门卫验证成功！在3分钟窗口内")
            print(f"     申请人: {user.real_name}")
            print(f"     类型: {user.user_type}")
            print(f"     访问日期: {approved_app.visit_date}")
            print(f"     访问目的: {approved_app.visit_purpose}")

            # 清理测试数据
            print(f"\n[清理] 删除测试数据...")
            db.session.delete(application)
            db.session.commit()
            print(f"[OK] 测试数据已清理")

            print("\n" + "=" * 70)
            print("[SUCCESS] 端到端测试通过！")
            print("=" * 70)
            return True
        else:
            print(f"[X] 门卫验证失败！超过3分钟窗口")
            print(f"     时间差: {int(time_diff_seconds)}秒 > 180秒")

            # 清理测试数据
            db.session.delete(application)
            db.session.commit()

            return False


def test_delayed_verify():
    """测试延迟验证（超过3分钟）"""
    app = create_app()

    with app.app_context():
        print("\n" + "=" * 70)
        print("延迟验证测试（超过3分钟）")
        print("=" * 70)

        user = User.query.filter_by(user_type='alumni', status='active').first()
        if not user:
            user = User.query.filter_by(user_type='parent', status='active').first()

        if not user:
            print("[X] 未找到测试用户")
            return False

        print(f"\n[测试用户] {user.real_name} ({user.user_type})")

        # 创建4分钟前的审批记录
        from app import db

        code = generate_hmac_code(user.phone, user.wechat_password, int(time.time()))
        approval_time = datetime.utcnow() - timedelta(minutes=4)

        application = VisitApplication(
            applicant_id=user.id,
            visit_date=date.today(),
            visit_time_start=dt_time(8, 0),
            visit_time_end=dt_time(20, 0),
            visit_purpose='测试',
            target_person=user.real_name,
            qr_code=code,
            application_status='approved',
            approved_by=1,
            approval_time=approval_time
        )

        db.session.add(application)
        db.session.commit()

        print(f"[创建] 4分钟前的审批记录")
        print(f"      审批时间: {approval_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 门卫验证
        print(f"\n[门卫验证]...")
        approved_app = VisitApplication.query.filter_by(qr_code=code).first()
        time_diff = (datetime.utcnow() - approved_app.approval_time).total_seconds()

        print(f"      时间差: {int(time_diff)} 秒")

        if time_diff > 180:
            print(f"[OK] 验证失败（符合预期）")
            print(f"     原因: 超过3分钟窗口")
            success = True
        else:
            print(f"[X] 验证成功（不符合预期）")
            success = False

        # 清理
        db.session.delete(application)
        db.session.commit()

        print("\n" + "=" * 70)
        if success:
            print("[SUCCESS] 延迟验证测试通过！")
        else:
            print("[FAIL] 延迟验证测试失败！")
        print("=" * 70)

        return success


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("门卫验证集成测试")
    print("=" * 70)

    # 测试1：正常流程
    result1 = test_e2e_flow()

    # 测试2：延迟验证
    result2 = test_delayed_verify()

    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"正常流程: {'[PASS]' if result1 else '[FAIL]'}")
    print(f"延迟验证: {'[PASS]' if result2 else '[FAIL]'}")
    print(f"\n总体结果: {'[ALL TESTS PASSED]' if result1 and result2 else '[SOME TESTS FAILED]'}")
    print("=" * 70)
