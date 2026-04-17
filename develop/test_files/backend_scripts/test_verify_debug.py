"""
验证码调试 - 详细版本
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code, verify_hmac_code
from app.models.user import User
import time

def test_verify_debug():
    """详细测试验证逻辑"""
    app = create_app()

    with app.app_context():
        user = User.query.filter_by(phone='13900002001').first()

        print("=" * 70)
        print("详细验证测试")
        print("=" * 70)

        # 生成码
        timestamp1 = int(time.time())
        code1 = generate_hmac_code(user.phone, user.wechat_password, timestamp1)

        print(f"\n步骤1: 生成码")
        print(f"  时间戳: {timestamp1}")
        print(f"  生成的码: {code1}")

        # 立即验证
        print(f"\n步骤2: 立即验证")
        result2 = verify_hmac_code(code1, user.phone, user.wechat_password, 24*60)
        print(f"  结果: {result2}")

        # 等待5秒
        print(f"\n步骤3: 等待5秒...")
        time.sleep(5)

        timestamp3 = int(time.time())
        print(f"  当前时间戳: {timestamp3}")
        print(f"  时间差: {timestamp3 - timestamp1} 秒")

        # 再次验证（应该成功，因为在24小时窗口内）
        print(f"\n步骤4: 5秒后验证")
        result4 = verify_hmac_code(code1, user.phone, user.wechat_password, 24*60)
        print(f"  结果: {result4}")

        # 手动检查：用原始时间戳生成的码
        print(f"\n步骤5: 手动检查")
        code_check = generate_hmac_code(user.phone, user.wechat_password, timestamp1)
        print(f"  用原始时间戳({timestamp1})生成的码: {code_check}")
        print(f"  原始码: {code1}")
        print(f"  是否一致: {code_check == code1}")

        # 检查：用当前时间戳生成的码
        code_current = generate_hmac_code(user.phone, user.wechat_password, timestamp3)
        print(f"\n步骤6: 对比")
        print(f"  用当前时间戳({timestamp3})生成的码: {code_current}")
        print(f"  原始码: {code1}")
        print(f"  是否一致: {code_current == code1}")

        # 尝试不同的时间戳
        print(f"\n步骤7: 穷举测试")
        for offset in range(0, 20):
            test_ts = timestamp3 - offset
            test_code = generate_hmac_code(user.phone, user.wechat_password, test_ts)
            match = "✓" if test_code == code1 else " "
            print(f"  offset={offset:2d}, ts={test_ts}, code={test_code} {match}")

if __name__ == '__main__':
    test_verify_debug()
