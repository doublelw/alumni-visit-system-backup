"""
测试优化后的门卫验证逻辑

直接调用 verify_visit_application_internal 函数
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code
from app.models.user import User
from app.models.visit_application import VisitApplication
from app.routes.guard_verify import verify_visit_application_internal
from datetime import datetime, date, time as dt_time


def test_optimized_guard_verify():
    """测试优化后的门卫验证"""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("优化后的门卫验证测试")
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

        # 步骤1: 创建审批记录（模拟老师审批）
        print(f"\n[步骤1] 创建审批记录（模拟老师审批）...")

        from app import db

        application = VisitApplication(
            applicant_id=user.id,
            visit_date=date.today(),
            visit_time_start=dt_time(8, 0),
            visit_time_end=dt_time(20, 0),
            visit_purpose=f'{user.real_name}进校',
            target_person=user.real_name,
            qr_code='dummy_code_a',  # 存储一个假码A
            application_status='approved',
            approved_by=1,
            approval_time=datetime.utcnow(),
            approval_note=f"审批日期: {date.today()}"
        )

        db.session.add(application)
        db.session.commit()

        print(f"[OK] 审批记录已创建")
        print(f"     ID: {application.id}")
        print(f"     申请人ID: {application.applicant_id}")

        # 步骤2: 生成码B（门卫验证用）
        print(f"\n[步骤2] 生成码B（门卫验证用）...")

        time.sleep(1)  # 等待1秒
        code_b = generate_hmac_code(user.phone, user.wechat_password, int(time.time()))

        print(f"[OK] 码B: {code_b}")
        print(f"     用途: 门卫验证（3分钟窗口）")

        # 步骤3: 调用优化后的门卫验证函数
        print(f"\n[步骤3] 调用优化后的门卫验证函数...")

        result = verify_visit_application_internal(code_b)

        if result['valid']:
            print(f"\n[SUCCESS] 验证成功！")
            print(f"     申请人: {result['applicant_info']['name']}")
            print(f"     类型: {result['applicant_info']['type']}")
            print(f"     手机: {result['applicant_info']['phone']}")
            print(f"     访问日期: {result['applicant_info']['visit_date']}")
            print(f"     访问目的: {result['applicant_info']['visit_purpose']}")

            # 验证是否找到刚创建的记录
            if result['application_id'] == application.id:
                print(f"\n[OK] 正确找到了刚创建的审批记录（ID={application.id}）")
                success = True
            else:
                print(f"\n[X] 找到了错误的记录（expected={application.id}, got={result['application_id']}）")
                success = False
        else:
            print(f"\n[X] 验证失败: {result['message']}")
            success = False

        # 清理测试数据
        print(f"\n[清理] 删除测试数据...")
        db.session.delete(application)
        db.session.commit()
        print(f"[OK] 测试数据已清理")

        print("\n" + "=" * 70)
        if success:
            print("[SUCCESS] 优化后的门卫验证测试通过！")
            print("\n性能提升:")
            print("- 优化前: 遍历所有用户（可能有1000+个）")
            print("- 优化后: 只遍历今天已审批的记录（通常只有几个到几十个）")
        else:
            print("[FAIL] 测试失败")
        print("=" * 70)

        return success


if __name__ == '__main__':
    success = test_optimized_guard_verify()
    sys.exit(0 if success else 1)
