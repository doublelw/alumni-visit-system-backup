"""
校园访问码系统 - 核心服务

提供动态码生成、验证、密钥管理等功能
"""

import hmac
import hashlib
import time
import base64
import secrets
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional


class AccessCodeService:
    """校园访问码系统 - 安全隔离版本"""

    # 系统密钥（从配置加载，实际使用时应该从环境变量或配置文件读取）
    SYSTEM_KEY = None  # 将在初始化时设置

    @classmethod
    def init_app(cls, system_key: str):
        """初始化系统密钥"""
        cls.SYSTEM_KEY = base64.b64decode(system_key)

    @staticmethod
    def hash_pin(pin_2digit: str) -> str:
        """
        对2位PIN进行单向哈希

        参数:
            pin_2digit: 2位私人密码（例如：'88'）

        返回:
            SHA256哈希值（十六进制字符串）
        """
        if not pin_2digit or len(pin_2digit) != 2:
            raise ValueError("PIN必须是2位数字")

        if not pin_2digit.isdigit():
            raise ValueError("PIN必须只包含数字")

        return hashlib.sha256(pin_2digit.encode('utf-8')).hexdigest()

    @classmethod
    def generate_user_key_pair(cls) -> Tuple[str, str]:
        """
        生成用户密钥对

        返回:
            (private_key_b64, public_key_b64) - Base64编码的密钥对
        """
        # 生成32字节随机密钥
        key_bytes = secrets.token_bytes(32)

        # 对称密钥方案：客户端和服务端使用相同的密钥
        private_key_b64 = base64.b64encode(key_bytes).decode('utf-8')
        public_key_b64 = base64.b64encode(key_bytes).decode('utf-8')

        return private_key_b64, public_key_b64

    @classmethod
    def generate_dynamic_code(
        cls,
        user_key: str,
        phone: str,
        pin_2digit: str
    ) -> Dict[str, any]:
        """
        生成6位动态访问码

        参数:
            user_key: 用户密钥（Base64）
            phone: 手机号
            pin_2digit: 2位私人密码

        返回:
            {
                'code': '123456',           # 6位数字码
                'timestamp': 1234567890,    # 分钟级时间戳
                'expires_at': '2026-03-27 12:05:00',  # 过期时间
                'valid_minutes': 5          # 有效分钟数
            }
        """
        if not cls.SYSTEM_KEY:
            raise RuntimeError("系统未初始化，请先调用init_app()")

        # 解码用户密钥
        try:
            key = base64.b64decode(user_key)
        except Exception:
            raise ValueError("无效的用户密钥")

        # 获取当前时间戳（分钟级）
        timestamp = int(time.time()) // 60

        # 构造消息：手机号 + PIN哈希 + 时间戳
        pin_hash = cls.hash_pin(pin_2digit)
        message = f"{phone}{pin_hash}{timestamp}".encode('utf-8')

        # 使用用户密钥进行HMAC-SHA256
        h = hmac.new(key, message, hashlib.sha256)
        digest = h.digest()

        # 转换为6位数字
        code_int = int.from_bytes(digest[:4], 'big') % 1000000
        code = f"{code_int:06d}"

        # 计算过期时间（5分钟后）
        expires_at = datetime.fromtimestamp((timestamp + 5) * 60)

        return {
            'code': code,
            'timestamp': timestamp,
            'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'valid_minutes': 5
        }

    @classmethod
    def verify_dynamic_code(
        cls,
        user_key: str,
        phone: str,
        pin_hash: str,
        code: str,
        timestamp: int
    ) -> Tuple[bool, str]:
        """
        验证6位动态访问码

        参数:
            user_key: 用户密钥（Base64）
            phone: 手机号
            pin_hash: PIN的哈希（SHA256）
            code: 6位访问码
            timestamp: 时间戳（分钟级）

        返回:
            (is_valid, message)
        """
        if not cls.SYSTEM_KEY:
            raise RuntimeError("系统未初始化，请先调用init_app()")

        # 解码用户密钥
        try:
            key = base64.b64decode(user_key)
        except Exception:
            return False, "无效的用户密钥"

        # 检查时间戳（5分钟窗口）
        current_timestamp = int(time.time()) // 60
        if abs(current_timestamp - timestamp) > 5:
            return False, "访问码已过期"

        # 重新计算动态码
        message = f"{phone}{pin_hash}{timestamp}".encode('utf-8')
        h = hmac.new(key, message, hashlib.sha256)
        digest = h.digest()
        code_int = int.from_bytes(digest[:4], 'big') % 1000000
        expected_code = f"{code_int:06d}"

        # 恒定时间比较，防止时序攻击
        if hmac.compare_digest(code.encode('utf-8'), expected_code.encode('utf-8')):
            return True, "验证成功"
        else:
            return False, "访问码错误"

    @classmethod
    def generate_visit_code(cls) -> str:
        """
        生成访客通行码（6位随机数字）

        返回:
            6位数字字符串
        """
        return f"{secrets.randbelow(1000000):06d}"

    @classmethod
    def generate_leave_pass_code(cls) -> str:
        """
        生成离校通行码（6位随机数字）

        返回:
            6位数字字符串
        """
        return f"{secrets.randbelow(1000000):06d}"

    @classmethod
    def generate_parent_verify_code(cls) -> str:
        """
        生成家长验证码（6位随机数字）

        返回:
            6位数字字符串
        """
        return f"{secrets.randbelow(1000000):06d}"

    @classmethod
    def check_key_expiry(cls, expires_at: Optional[datetime]) -> Tuple[bool, int]:
        """
        检查密钥是否过期

        参数:
            expires_at: 过期时间（datetime对象）

        返回:
            (is_expired, days_until_expiry)
            - is_expired: 是否已过期
            - days_until_expiry: 距离过期的天数（负数表示已过期）
        """
        if expires_at is None:
            return False, 999  # 永不过期

        now = datetime.utcnow()
        delta = expires_at - now
        days = delta.days

        is_expired = days < 0
        return is_expired, days

    @classmethod
    def calculate_next_expiry(cls) -> datetime:
        """
        计算下一次密钥过期时间（6个月后）

        返回:
            datetime对象
        """
        return datetime.utcnow() + timedelta(days=180)


# 使用示例
if __name__ == '__main__':
    # 初始化系统密钥（实际使用时应该从配置读取）
    import os
    system_key = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    AccessCodeService.init_app(system_key)

    # 生成用户密钥对
    private_key, public_key = AccessCodeService.generate_user_key_pair()
    print(f"用户密钥: {private_key}")

    # 用户注册时设置2位PIN
    pin = "88"
    pin_hash = AccessCodeService.hash_pin(pin)
    print(f"PIN哈希: {pin_hash}")

    # 生成动态码
    phone = "13800138000"
    result = AccessCodeService.generate_dynamic_code(private_key, phone, pin)
    print(f"\n生成的动态码:")
    print(f"  码: {result['code']}")
    print(f"  时间戳: {result['timestamp']}")
    print(f"  过期时间: {result['expires_at']}")

    # 验证动态码
    is_valid, message = AccessCodeService.verify_dynamic_code(
        public_key,
        phone,
        pin_hash,
        result['code'],
        result['timestamp']
    )
    print(f"\n验证结果: {is_valid}, 消息: {message}")

    # 生成访客通行码
    visit_code = AccessCodeService.generate_visit_code()
    print(f"\n访客通行码: {visit_code}")

    # 生成离校通行码
    leave_code = AccessCodeService.generate_leave_pass_code()
    print(f"离校通行码: {leave_code}")

    # 生成家长验证码
    parent_code = AccessCodeService.generate_parent_verify_code()
    print(f"家长验证码: {parent_code}")

    # 检查密钥过期
    expires_at = AccessCodeService.calculate_next_expiry()
    is_expired, days = AccessCodeService.check_key_expiry(expires_at)
    print(f"\n密钥过期检查:")
    print(f"  过期时间: {expires_at.strftime('%Y-%m-%d')}")
    print(f"  是否过期: {is_expired}")
    print(f"  剩余天数: {days}")
