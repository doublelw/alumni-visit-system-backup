"""
外网服务器模拟（flag服务器）
只存储验证码和基本联系信息，不存储详细个人信息
模拟腾讯云托管的临时缓存功能
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict

class ExternalNetworkStorage:
    """外网存储 - 模拟腾讯云托管"""

    def __init__(self, db_path='external_network.db'):
        """初始化外网存储"""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化外网数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建访客临时信息表（只存储最小信息）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visitor_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_code TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'pending',
                used_at TIMESTAMP NULL,
                FOREIGN KEY (access_code) REFERENCES access_codes(code)
            )
        ''')

        # 创建访问码表（只存码本身，不存详细信息）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                code_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active'
            )
        ''')

        conn.commit()
        conn.close()

    def store_access_code(self, code: str, code_type: str, expiry_hours: int = 24) -> bool:
        """
        存储访问码到外网
        只存储码本身和类型，不存储个人信息

        Args:
            code: 访问码
            code_type: 码类型 ('visitor', 'parent-visit', 'student-leave', 'alumni')
            expiry_hours: 有效期（小时）

        Returns:
            bool: 是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=expiry_hours)

            cursor.execute('''
                INSERT INTO access_codes (code, code_type, created_at, expires_at, status)
                VALUES (?, ?, ?, ?, 'active')
            ''', (code, code_type, created_at, expires_at))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[外网存储错误] 存储访问码失败: {e}")
            return False

    def store_visitor_info(self, access_code: str, phone: str, expiry_hours: int = 24) -> bool:
        """
        存储访客临时信息到外网
        只存储验证码和手机号，不存储姓名、身份证等敏感信息

        Args:
            access_code: 访问码
            phone: 手机号
            expiry_hours: 有效期（小时）

        Returns:
            bool: 是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=expiry_hours)

            cursor.execute('''
                INSERT INTO visitor_cache (access_code, phone, created_at, expires_at, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (access_code, phone, created_at, expires_at))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[外网存储错误] 存储访客信息失败: {e}")
            return False

    def get_visitor_info(self, access_code: str) -> Optional[Dict]:
        """
        从外网获取访客信息
        只返回基本信息（手机号），不包含敏感信息

        Args:
            access_code: 访问码

        Returns:
            dict: 访客基本信息 {'phone': '', 'created_at': '', 'expires_at': ''} 或 None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT phone, created_at, expires_at, status
                FROM visitor_cache
                WHERE access_code = ? AND status = 'pending' AND expires_at > datetime('now')
                ORDER BY created_at DESC
                LIMIT 1
            ''', (access_code,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'phone': result[0],
                    'created_at': result[1],
                    'expires_at': result[2],
                    'status': result[3]
                }
            return None
        except Exception as e:
            print(f"[外网存储错误] 获取访客信息失败: {e}")
            return None

    def mark_visitor_used(self, access_code: str) -> bool:
        """
        标记访客码已使用（教师验证后调用）

        Args:
            access_code: 访问码

        Returns:
            bool: 是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE visitor_cache
                SET status = 'used', used_at = datetime('now')
                WHERE access_code = ?
            ''', (access_code,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[外网存储错误] 标记访客使用失败: {e}")
            return False

    def verify_access_code(self, code: str, code_type: str = None) -> bool:
        """
        验证访问码是否有效（外网验证）

        Args:
            code: 访问码
            code_type: 码类型（可选，用于类型匹配验证）

        Returns:
            bool: 是否有效
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = '''
                SELECT status, expires_at
                FROM access_codes
                WHERE code = ? AND status = 'active' AND expires_at > datetime('now')
            '''
            params = [code]

            if code_type:
                query += ' AND code_type = ?'
                params.append(code_type)

            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.close()

            return result is not None
        except Exception as e:
            print(f"[外网存储错误] 验证访问码失败: {e}")
            return False

    def cleanup_expired(self):
        """清理过期的访问码和访客信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 删除过期的访问码
            cursor.execute('''
                DELETE FROM access_codes
                WHERE expires_at < datetime('now')
            ''')

            # 删除过期的访客缓存
            cursor.execute('''
                DELETE FROM visitor_cache
                WHERE expires_at < datetime('now')
            ''')

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            return deleted_count
        except Exception as e:
            print(f"[外网存储错误] 清理过期数据失败: {e}")
            return 0


# 全局实例
external_storage = ExternalNetworkStorage()

if __name__ == '__main__':
    # 测试代码
    print("=== 外网存储测试 ===")

    # 测试存储访问码
    test_code = "123456"
    if external_storage.store_access_code(test_code, 'visitor'):
        print(f"[OK] 访问码 {test_code} 存储成功")

    # 测试验证
    if external_storage.verify_access_code(test_code, 'visitor'):
        print(f"[OK] 访问码 {test_code} 验证成功")

    # 测试访客信息存储
    if external_storage.store_visitor_info(test_code, '13900000000'):
        print(f"[OK] 访客信息存储成功")

    # 测试获取访客信息
    info = external_storage.get_visitor_info(test_code)
    if info:
        print(f"[OK] 获取访客信息成功: {info}")

    # 测试标记使用
    if external_storage.mark_visitor_used(test_code):
        print(f"[OK] 标记访客使用成功")

    print("\n外网存储测试完成！")
