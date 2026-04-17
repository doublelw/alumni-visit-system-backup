"""
HMAC诊断测试 - 找出为什么验证失败
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.hmac_utils import generate_hmac_code, verify_hmac_code, get_timestamp_info
from app.models.user import User
import time

def main():
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("  HMAC验证诊断测试")
        print("=" * 80)

        # 获取一个校友用户
        alumni = User.query.filter(
            User.user_type == 'alumni',
            User.status == 'active'
        ).first()

        if not alumni:
            print("\n[ERROR] 数据库中没有校友用户")
            return

        print(f"\n测试用户:")
        print(f"  姓名: {alumni.real_name}")
        print(f"  手机号: {alumni.phone}")
        print(f"  微信密码: {alumni.wechat_password}")

        # 生成HMAC码（使用当前时间戳）
        current_timestamp = int(time.time())
        print(f"\n生成HMAC码:")
        print(f"  时间戳: {current_timestamp}")
        print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_timestamp))}")

        code = generate_hmac_code(alumni.phone, alumni.wechat_password, current_timestamp)
        print(f"  生成的码: {code}")

        # 立即验证（使用当前时间）
        print(f"\n立即验证:")
        verify_timestamp = int(time.time())
        print(f"  验证时间戳: {verify_timestamp}")
        print(f"  验证时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(verify_timestamp))}")
        print(f"  时间差: {verify_timestamp - current_timestamp}秒")

        result = verify_hmac_code(code, alumni.phone, alumni.wechat_password, 3)
        print(f"\n验证结果:")
        print(f"  valid: {result['valid']}")
        print(f"  timestamp: {result.get('timestamp')}")
        print(f"  message: {result.get('message')}")

        if result['valid']:
            match_timestamp = result['timestamp']
            time_diff = verify_timestamp - match_timestamp
            print(f"  匹配时间戳: {match_timestamp}")
            print(f"  匹配时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(match_timestamp))}")
            print(f"  实际时间差: {time_diff}秒")
        else:
            print("\n[FAIL] 验证失败！")
            print("\n尝试手动验证时间窗口内的各个时间戳:")

            # 手动测试当前时间及前60秒
            for offset in [0, 1, 2, 3, 5, 10, 30, 60, 90, 120, 180]:
                test_timestamp = verify_timestamp - offset
                test_code = generate_hmac_code(alumni.phone, alumni.wechat_password, test_timestamp)
                match = "✓ MATCH" if test_code == code else "  ✗"
                print(f"  T-{offset:3d}s: {test_code} {match}")

        # 测试不传递时间戳的情况（使用默认当前时间）
        print(f"\n使用默认时间戳生成HMAC码:")
        code_auto = generate_hmac_code(alumni.phone, alumni.wechat_password)
        print(f"  生成的码: {code_auto}")
        print(f"  当前时间戳: {int(time.time())}")

        result_auto = verify_hmac_code(code_auto, alumni.phone, alumni.wechat_password, 3)
        print(f"\n验证结果:")
        print(f"  valid: {result_auto['valid']}")
        print(f"  message: {result_auto.get('message')}")

        print("\n" + "=" * 80)
        print("  诊断完成")
        print("=" * 80)

if __name__ == "__main__":
    main()
