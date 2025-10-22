#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
校友入校登记系统 - 数据库初始化脚本
功能: 创建数据库表结构、初始化基础数据
使用: python init_database.py
"""

import os
import sys
import hashlib
import secrets
from datetime import datetime

# 添加后端路径到系统路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.visit import Visit, VisitRecord
from app.models.system import SystemConfig

def generate_secret_key():
    """生成安全的密钥"""
    return secrets.token_hex(32)

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_database():
    """初始化数据库"""
    app = create_app()

    with app.app_context():
        print("🚀 开始初始化数据库...")

        # 删除所有表（如果存在）
        print("📋 删除现有表...")
        db.drop_all()

        # 创建所有表
        print("📋 创建数据库表...")
        db.create_all()

        print("✅ 数据库表创建完成")

        # 初始化系统配置
        print("📋 初始化系统配置...")
        init_system_config()

        # 创建默认用户
        print("📋 创建默认用户...")
        create_default_users()

        # 提交所有更改
        db.session.commit()
        print("✅ 数据库初始化完成！")

def init_system_config():
    """初始化系统配置"""
    configs = [
        {
            'config_key': 'system_name',
            'config_value': '校友入校登记系统',
            'config_type': 'string',
            'description': '系统名称'
        },
        {
            'config_key': 'system_version',
            'config_value': '1.0.0',
            'config_type': 'string',
            'description': '系统版本'
        },
        {
            'config_key': 'allow_registration',
            'config_value': 'true',
            'config_type': 'boolean',
            'description': '允许用户注册'
        },
        {
            'config_key': 'require_approval',
            'config_value': 'true',
            'config_type': 'boolean',
            'description': '预约需要审核'
        },
        {
            'config_key': 'qr_code_expire_minutes',
            'config_value': '60',
            'config_type': 'integer',
            'description': '二维码过期时间（分钟）'
        },
        {
            'config_key': 'max_visit_duration_hours',
            'config_value': '4',
            'config_type': 'integer',
            'description': '最大访问时长（小时）'
        },
        {
            'config_key': 'upload_max_size_mb',
            'config_value': '10',
            'config_type': 'integer',
            'description': '上传文件最大大小（MB）'
        },
        {
            'config_key': 'email_notifications',
            'config_value': 'false',
            'config_type': 'boolean',
            'description': '邮件通知开关'
        },
        {
            'config_key': 'sms_notifications',
            'config_value': 'false',
            'config_type': 'boolean',
            'description': '短信通知开关'
        },
        {
            'config_key': 'face_recognition_enabled',
            'config_value': 'true',
            'config_type': 'boolean',
            'description': '人脸识别功能开关'
        },
        {
            'config_key': 'maintenance_mode',
            'config_value': 'false',
            'config_type': 'boolean',
            'description': '维护模式'
        },
        {
            'config_key': 'created_at',
            'config_value': datetime.now().isoformat(),
            'config_type': 'datetime',
            'description': '系统创建时间'
        }
    ]

    for config_data in configs:
        # 检查是否已存在
        existing = SystemConfig.query.filter_by(config_key=config_data['config_key']).first()
        if not existing:
            config = SystemConfig(**config_data)
            db.session.add(config)
            print(f"  ✅ 创建配置: {config_data['config_key']}")

def create_default_users():
    """创建默认用户账户"""

    # 管理员账户
    admin = User(
        username='admin',
        real_name='系统管理员',
        email='admin@pofeclife.top',
        phone='13800138001',
        user_type='admin',
        status='active',
        created_at=datetime.now()
    )
    admin.set_password('admin123')
    db.session.add(admin)
    print("  ✅ 创建管理员账户: admin / admin123")

    # 保安账户
    security = User(
        username='security',
        real_name='保安员',
        email='security@pofeclife.top',
        phone='13900139001',
        user_type='security',
        status='active',
        created_at=datetime.now()
    )
    security.set_password('security123')
    db.session.add(security)
    print("  ✅ 创建保安账户: security / security123")

    # 测试校友账户
    alumni = User(
        username='alumni001',
        real_name='测试校友',
        email='alumni001@pofeclife.top',
        phone='13700137001',
        user_type='alumni',
        status='active',
        graduation_year='2020',
        major='计算机科学与技术',
        company='腾讯科技',
        position='软件工程师',
        created_at=datetime.now()
    )
    alumni.set_password('alumni123')
    db.session.add(alumni)
    print("  ✅ 创建校友账户: alumni001 / alumni123")

    # 教师账户
    teachers = [
        {
            'username': 'teacher001',
            'real_name': '张老师',
            'email': 'teacher001@school.edu',
            'phone': '13600136001',
            'department': '计算机学院',
            'position': '教授',
            'office': '科技楼A301'
        },
        {
            'username': 'teacher002',
            'real_name': '李老师',
            'email': 'teacher002@school.edu',
            'phone': '13600136002',
            'department': '计算机学院',
            'position': '副教授',
            'office': '科技楼A302'
        },
        {
            'username': 'teacher003',
            'real_name': '王老师',
            'email': 'teacher003@school.edu',
            'phone': '13600136003',
            'department': '信息学院',
            'position': '讲师',
            'office': '信息楼B201'
        },
        {
            'username': 'teacher004',
            'real_name': '陈老师',
            'email': 'teacher004@school.edu',
            'phone': '13600136004',
            'department': '数学学院',
            'position': '教授',
            'office': '数学楼C101'
        },
        {
            'username': 'teacher005',
            'real_name': '刘老师',
            'email': 'teacher005@school.edu',
            'phone': '13600136005',
            'department': '物理学院',
            'position': '副教授',
            'office': '物理楼D205'
        }
    ]

    for teacher_data in teachers:
        teacher = User(
            username=teacher_data['username'],
            real_name=teacher_data['real_name'],
            email=teacher_data['email'],
            phone=teacher_data['phone'],
            user_type='teacher',
            status='active',
            department=teacher_data.get('department', ''),
            position=teacher_data.get('position', ''),
            office=teacher_data.get('office', ''),
            created_at=datetime.now()
        )
        teacher.set_password('teacher123')
        db.session.add(teacher)
        print(f"  ✅ 创建教师账户: {teacher_data['username']} / teacher123 ({teacher_data['real_name']})")

    # 创建一些额外的测试校友
    alumni_users = [
        {
            'username': 'alumni002',
            'real_name='李华',
            'email': 'lihua@company.com',
            'phone': '13700137002',
            'graduation_year': '2019',
            'major': '软件工程',
            'company': '阿里巴巴',
            'position': '产品经理'
        },
        {
            'username': 'alumni003',
            'real_name='王芳',
            'email': 'wangfang@tech.com',
            'phone': '13700137003',
            'graduation_year': '2021',
            'major': '数据科学',
            'company': '字节跳动',
            'position': '数据分析师'
        }
    ]

    for alumni_data in alumni_users:
        alumni_user = User(
            username=alumni_data['username'],
            real_name=alumni_data['real_name'],
            email=alumni_data['email'],
            phone=alumni_data['phone'],
            user_type='alumni',
            status='active',
            graduation_year=alumni_data.get('graduation_year', ''),
            major=alumni_data.get('major', ''),
            company=alumni_data.get('company', ''),
            position=alumni_data.get('position', ''),
            created_at=datetime.now()
        )
        alumni_user.set_password('alumni123')
        db.session.add(alumni_user)
        print(f"  ✅ 创建校友账户: {alumni_data['username']} / alumni123 ({alumni_data['real_name']})")

def print_user_summary():
    """打印用户账户摘要"""
    app = create_app()

    with app.app_context():
        users = User.query.all()

        print("\n" + "="*60)
        print("📋 用户账户摘要")
        print("="*60)

        for user in users:
            status_icon = "✅" if user.status == 'active' else "❌"
            user_type_names = {
                'admin': '管理员',
                'security': '保安',
                'alumni': '校友',
                'teacher': '教师'
            }
            user_type_name = user_type_names.get(user.user_type, user.user_type)

            print(f"{status_icon} {user.real_name} ({user.username}) - {user_type_name}")
            print(f"   📧 {user.email}")
            print(f"   📱 {user.phone}")

            if user.user_type == 'alumni':
                print(f"   🎓 {user.major} {user.graduation_year}届")
                print(f"   🏢 {user.company} - {user.position}")
            elif user.user_type == 'teacher':
                print(f"   🏫 {user.department} - {user.position}")
                if user.office:
                    print(f"   📍 办公室: {user.office}")

            print()

        print("="*60)
        print(f"总共创建 {len(users)} 个用户账户")
        print("="*60)

def main():
    """主函数"""
    try:
        # 初始化数据库
        init_database()

        # 打印用户摘要
        print_user_summary()

        print("\n🎉 数据库初始化成功完成！")
        print("\n📱 默认登录账户:")
        print("🔐 管理员: admin / admin123")
        print("🛡️ 保安员: security / security123")
        print("👨 校友: alumni001 / alumni123")
        print("👨‍🏫 教师: teacher001-005 / teacher123")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()