"""
HMAC动态码工具函数

用于生成和验证基于时间窗口的动态访问码
"""

import hmac
import hashlib
import time
from datetime import datetime, timedelta
from flask import current_app


def generate_hmac_code(phone: str, password: str, timestamp: int = None) -> str:
    """
    生成HMAC-SHA256动态码

    Args:
        phone: 手机号
        password: 密码
        timestamp: Unix时间戳（秒），默认使用当前时间

    Returns:
        6位数字字符串
    """
    if timestamp is None:
        timestamp = int(time.time())

    # 生成HMAC-SHA256
    secret_key = current_app.config['HMAC_SECRET_KEY']
    message = f"{phone}{password}{timestamp}"

    hmac_obj = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    hmac_digest = hmac_obj.hexdigest()

    # 取后6位数字（如果不足6位则循环使用）
    digits = ''.join(c for c in hmac_digest if c.isdigit())
    if len(digits) < 6:
        # 补足6位（循环使用）
        while len(digits) < 6:
            digits += digits
    code = digits[:6]

    return code


def verify_hmac_code(code: str, phone: str, password: str, time_window_minutes: int) -> dict:
    """
    验证HMAC动态码

    Args:
        code: 6位动态码
        phone: 手机号
        password: 密码
        time_window_minutes: 时间窗口（分钟）

    Returns:
        {
            'valid': bool,  # 是否有效
            'timestamp': int,  # 匹配的时间戳
            'message': str  # 错误信息（如果无效）
        }
    """
    import time as time_module
    current_timestamp = int(time_module.time())
    window_seconds = time_window_minutes * 60

    # 策略：先精确匹配（前60秒每秒），然后粗略匹配（每分钟）
    # 这样既能快速匹配最近的码，又能覆盖长时间窗口

    # 1. 先检查当前时间
    generated_code = generate_hmac_code(phone, password, current_timestamp)
    if generated_code == code:
        return {
            'valid': True,
            'timestamp': current_timestamp,
            'message': '验证通过'
        }

    # 2. 精确检查：前60秒内每一秒
    # 这样可以匹配几秒钟前生成的码
    for offset in range(1, min(61, window_seconds + 1)):
        test_timestamp = current_timestamp - offset
        generated_code = generate_hmac_code(phone, password, test_timestamp)

        if generated_code == code:
            return {
                'valid': True,
                'timestamp': test_timestamp,
                'message': '验证通过'
            }

    # 3. 粗略检查：从60秒开始，每60秒检查一次
    # 这样可以覆盖长窗口（24小时），但不会太慢
    for offset in range(60, window_seconds + 1, 60):
        test_timestamp = current_timestamp - offset
        generated_code = generate_hmac_code(phone, password, test_timestamp)

        if generated_code == code:
            return {
                'valid': True,
                'timestamp': test_timestamp,
                'message': '验证通过'
            }

    return {
        'valid': False,
        'timestamp': None,
        'message': f'验证失败：码无效或已过期（{time_window_minutes}分钟有效期）'
    }


def get_timestamp_info(timestamp: int) -> dict:
    """
    获取时间戳的详细信息

    Args:
        timestamp: Unix时间戳（秒）

    Returns:
        {
            'datetime': datetime对象,
            'formatted': '2026-03-27 14:30:00',
            'age_seconds': 距离现在的秒数,
            'age_minutes': 距离现在的分钟数
        }
    """
    dt = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    age = now - dt

    return {
        'datetime': dt,
        'formatted': dt.strftime('%Y-%m-%d %H:%M:%S'),
        'age_seconds': age.total_seconds(),
        'age_minutes': age.total_seconds() / 60
    }
