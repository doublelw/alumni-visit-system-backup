#!/usr/bin/env python3
"""
简单的数据库初始化脚本 - 直接使用SQL创建表和用户
"""

import sqlite3
import os
import hashlib

def hash_password(password):
    """简单密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """初始化数据库"""
    db_path = 'alumni_system_dev.db'

    # 如果数据库文件存在，先删除
    if os.path.exists(db_path):
        print(f"删除现有数据库文件: {db_path}")
        os.remove(db_path)

    try:
        print("创建新数据库...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建用户表
        print("创建用户表...")
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid VARCHAR(36) UNIQUE NOT NULL,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                real_name VARCHAR(80) NOT NULL,
                phone VARCHAR(20),
                user_type VARCHAR(20) NOT NULL DEFAULT 'student',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                employee_id VARCHAR(50) UNIQUE,
                student_id VARCHAR(50) UNIQUE,
                graduation_year INTEGER,
                major VARCHAR(100),
                company VARCHAR(100),
                position VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建访问申请表
        print("创建访问申请表...")
        cursor.execute('''
            CREATE TABLE visit_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid VARCHAR(36) UNIQUE NOT NULL,
                applicant_name VARCHAR(80) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(120) NOT NULL,
                visit_date DATE NOT NULL,
                visit_time TIME NOT NULL,
                purpose TEXT NOT NULL,
                escort_name VARCHAR(80),
                escort_phone VARCHAR(20),
                status VARCHAR(20) DEFAULT 'pending',
                approval_time TIMESTAMP,
                approver_id INTEGER,
                qr_code_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (approver_id) REFERENCES users (id)
            )
        ''')

        # 创建管理员用户
        print("创建管理员用户...")
        admin_password_hash = hash_password('admin123')

        cursor.execute('''
            INSERT INTO users (
                uuid, username, email, password_hash, real_name,
                phone, user_type, status, employee_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'admin-uuid-12345',
            'admin',
            'admin@school.edu.cn',
            admin_password_hash,
            '系统管理员',
            '13800000000',
            'admin',
            'active',
            'ADMIN001'
        ))

        # 创建测试校友用户
        print("创建测试校友用户...")
        alumni_password_hash = hash_password('test123')

        cursor.execute('''
            INSERT INTO users (
                uuid, username, email, password_hash, real_name,
                phone, user_type, status, student_id, graduation_year, major
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'alumni-uuid-12345',
            'test_alumni',
            'alumni@test.com',
            alumni_password_hash,
            '张校友',
            '13900000001',
            'alumni',
            'active',
            '2020001',
            2020,
            '计算机科学'
        ))

        # 提交事务
        conn.commit()
        print("✅ 数据库初始化成功!")
        print("✅ 管理员用户创建成功!")
        print("   用户名: admin")
        print("   密码: admin123")
        print("   用户类型: admin")
        print()
        print("✅ 测试校友用户创建成功!")
        print("   用户名: test_alumni")
        print("   密码: test123")
        print("   用户类型: alumni")

        return True

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verify_admin_user():
    """验证管理员用户"""
    db_path = 'alumni_system_dev.db'

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询admin用户
        cursor.execute('''
            SELECT id, username, user_type, status, employee_id
            FROM users
            WHERE username = 'admin'
        ''')

        admin_user = cursor.fetchone()

        if admin_user:
            user_id, username, user_type, status, employee_id = admin_user
            print("✅ 管理员用户验证成功:")
            print(f"   ID: {user_id}")
            print(f"   用户名: {username}")
            print(f"   用户类型: {user_type}")
            print(f"   状态: {status}")
            print(f"   员工编号: {employee_id}")

            if user_type == 'admin':
                print("✅ 管理员权限正确!")
                return True
            else:
                print(f"❌ 管理员权限错误: 期望 'admin', 实际 '{user_type}'")
                return False
        else:
            print("❌ 未找到管理员用户")
            return False

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== 数据库初始化 ===")
    print()

    # 初始化数据库
    success = init_database()

    if success:
        print()
        print("=== 验证管理员用户 ===")
        print()
        verify_admin_user()

        print()
        print("=== 完成 ===")
        print("现在可以使用管理员账户登录系统:")
        print("用户名: admin")
        print("密码: admin123")
        print()
        print("请重新启动服务器并测试管理功能")
    else:
        print()
        print("=== 初始化失败 ===")
        print("请检查错误信息并重试")