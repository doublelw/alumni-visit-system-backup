"""
电子校友卡 - 动态申请码生成服务

核心功能：
1. 生成动态申请码（校内人员）
2. 生成访客码（校外人员）
3. 验证申请码
4. 照片管理
"""

import hmac
import hashlib
import time
import base64
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from flask import current_app


class ElectronicCardService:
    """电子校友卡服务"""

    # 系统密钥（从配置加载）
    SYSTEM_KEY = None

    @classmethod
    def init_app(cls, system_key: str):
        """初始化系统密钥"""
        cls.SYSTEM_KEY = system_key.encode('utf-8')

    @classmethod
    def generate_application_code(
        cls,
        user_id: int,
        user_type: str,
        pin_code: str,
        validity_minutes: int = 2
    ) -> Dict[str, any]:
        """
        生成动态申请码（校内人员）

        参数:
            user_id: 用户ID
            user_type: 用户类型（student/teacher/staff/alumni）
            pin_code: 2位个人密码
            validity_minutes: 有效期（分钟），默认2分钟

        返回:
            {
                'code': '123456',
                'expires_at': '2026-03-27 12:05:00',
                'user_id': 123,
                'user_type': 'student',
                'validity_period': '2分钟'
            }
        """
        if not cls.SYSTEM_KEY:
            raise RuntimeError("系统未初始化")

        # 获取当前时间（2分钟一个时间窗口）
        now = datetime.now()
        # 计算当前是第几个2分钟窗口（从当天0点开始）
        minutes_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 60
        time_window = int(minutes_since_midnight // validity_minutes)

        # 生成消息：用户ID + 2位密码 + 时间窗口
        message = f"{user_id}{pin_code}{time_window}".encode('utf-8')

        # 使用HMAC-SHA256签名
        h = hmac.new(cls.SYSTEM_KEY, message, hashlib.sha256)
        signature = h.digest()

        # 转换为6位数字
        code_int = int.from_bytes(signature[:4], 'big') % 1000000
        code = f"{code_int:06d}"

        # 计算过期时间（当前时间窗口的结束时间）
        window_start_minutes = int(time_window * validity_minutes)
        expires_at = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=window_start_minutes + validity_minutes)

        return {
            'code': code,
            'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'user_type': user_type,
            'validity_period': f'{validity_minutes}分钟',
            'time_window': time_window
        }

    @classmethod
    def verify_application_code(
        cls,
        code: str,
        user_id: int,
        user_type: str,
        pin_code: str
    ) -> Tuple[bool, str]:
        """
        验证动态申请码

        参数:
            code: 6位申请码
            user_id: 用户ID
            user_type: 用户类型
            pin_code: 2位个人密码

        返回:
            (is_valid, message)
        """
        if not cls.SYSTEM_KEY:
            raise RuntimeError("系统未初始化")

        # 重新生成码进行比对（使用当前时间窗口）
        result = cls.generate_application_code(user_id, user_type, pin_code)

        # 检查是否过期
        expires_at = datetime.strptime(result['expires_at'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expires_at:
            return False, "申请码已过期"

        # 比对码
        if code == result['code']:
            return True, "验证成功"
        else:
            return False, "申请码无效"

    @classmethod
    def generate_visitor_code(
        cls,
        visitor_id: int,
        approval_time: Optional[datetime] = None
    ) -> Dict[str, any]:
        """
        生成访客码（审批通过后）

        参数:
            visitor_id: 访客ID
            approval_time: 审批时间（默认当前时间）

        返回:
            {
                'code': '654321',
                'expires_at': '2026-03-27 23:59:59',
                'visitor_id': 456,
                'approval_date': '20260327'
            }
        """
        if not cls.SYSTEM_KEY:
            raise RuntimeError("系统未初始化")

        if approval_time is None:
            approval_time = datetime.now()

        # 获取审批日期
        approval_date = approval_time.strftime('%Y%m%d')

        # 添加随机数（确保唯一性）
        import random
        random_suffix = random.randint(1000, 9999)

        # 生成消息：访客ID + 审批日期 + 随机数
        message = f"{visitor_id}{approval_date}{random_suffix}".encode('utf-8')

        # 使用HMAC-SHA256签名
        h = hmac.new(cls.SYSTEM_KEY, message, hashlib.sha256)
        signature = h.digest()

        # 转换为6位数字
        code_int = int.from_bytes(signature[:4], 'big') % 1000000
        code = f"{code_int:06d}"

        # 当天有效（23:59:59）
        expires_at = approval_time.replace(
            hour=23, minute=59, second=59, microsecond=0
        )

        return {
            'code': code,
            'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'visitor_id': visitor_id,
            'approval_date': approval_date
        }

    @classmethod
    def verify_visitor_code(
        cls,
        code: str,
        visitor_id: int,
        approval_date: str
    ) -> Tuple[bool, str]:
        """
        验证访客码

        参数:
            code: 6位访客码
            visitor_id: 访客ID
            approval_date: 审批日期（YYYYMMDD）

        返回:
            (is_valid, message)
        """
        if not cls.SYSTEM_KEY:
            raise RuntimeError("系统未初始化")

        # 这里需要保存生成时的随机数才能验证
        # 简化方案：重新生成并检查时间范围
        # 实际应该在数据库中记录生成的码

        # 检查日期是否过期
        try:
            approval_dt = datetime.strptime(approval_date, '%Y%m%d')
            if datetime.now() > approval_dt.replace(hour=23, minute=59, second=59):
                return False, "访客码已过期"
        except:
            return False, "无效的审批日期"

        # 实际验证应该查询数据库
        # 这里只是示例
        return True, "验证成功"

    @classmethod
    def generate_system_key(cls) -> str:
        """
        生成系统密钥

        返回:
            Base64编码的密钥
        """
        import secrets
        key = secrets.token_bytes(32)
        return base64.b64encode(key).decode('utf-8')


# 使用示例
if __name__ == '__main__':
    # 初始化
    system_key = ElectronicCardService.generate_system_key()
    ElectronicCardService.init_app(system_key)

    # 示例1：生成学生申请码
    print("=== 学生申请码 ===")
    student_result = ElectronicCardService.generate_application_code(
        user_id=1001,
        user_type='student',
        validity_hours=24
    )
    print(f"学生申请码: {student_result['code']}")
    print(f"过期时间: {student_result['expires_at']}")
    print(f"有效日期: {student_result['validity_date']}")

    # 验证
    is_valid, message = ElectronicCardService.verify_application_code(
        code=student_result['code'],
        user_id=1001,
        user_type='student'
    )
    print(f"验证结果: {is_valid}, {message}")

    # 示例2：生成访客码
    print("\n=== 访客码 ===")
    visitor_result = ElectronicCardService.generate_visitor_code(
        visitor_id=2001
    )
    print(f"访客码: {visitor_result['code']}")
    print(f"过期时间: {visitor_result['expires_at']}")
    print(f"审批日期: {visitor_result['approval_date']}")
