"""
测试HMAC动态码生成和验证
"""
import sys
sys.path.insert(0, 'backend')

from app import create_app
from app.models.user import User
from app.utils.hmac_utils import generate_hmac_code, verify_hmac_code, get_timestamp_info

app = create_app()

with app.app_context():
    print("=" * 60)
    print("HMAC动态码测试")
    print("=" * 60)

    # 获取一个家长用户
    parent = User.query.filter_by(phone='13900002002').first()

    if not parent:
        print("错误：未找到测试家长（13900002002）")
        sys.exit(1)

    print(f"\n测试家长: {parent.real_name}")
    print(f"手机号: {parent.phone}")
    print(f"密码: {parent.wechat_password}")

    # 生成HMAC码
    import time
    timestamp = int(time.time())
    code = generate_hmac_code(parent.phone, parent.wechat_password, timestamp)

    print(f"\n生成的6位码: {code}")
    print(f"使用时间戳: {timestamp}")
    print(f"时间: {get_timestamp_info(timestamp)['formatted']}")

    # 验证HMAC码（24小时窗口）
    print("\n" + "=" * 60)
    print("验证HMAC码（24小时窗口）")
    print("=" * 60)

    verification = verify_hmac_code(code, parent.phone, parent.wechat_password, 24 * 60)

    print(f"验证结果: {verification['valid']}")
    print(f"消息: {verification['message']}")

    if verification['valid']:
        ts_info = get_timestamp_info(verification['timestamp'])
        print(f"匹配时间戳: {verification['timestamp']}")
        print(f"时间: {ts_info['formatted']}")
        print(f"距离现在: {ts_info['age_minutes']:.1f} 分钟")
