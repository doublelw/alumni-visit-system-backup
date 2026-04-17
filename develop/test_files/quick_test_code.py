"""
快速创建测试验证码
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

os.environ['FLASK_ENV'] = 'development'

from backend.app import create_app, db
from backend.app.models.dynamic_code_cache import DynamicCodeCache
from backend.app.models.user_verification import UserVerification
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # 查找或创建测试用户
    test_user = UserVerification.query.filter_by(username='test_user_2026').first()

    if not test_user:
        # 创建测试用户
        test_user = UserVerification(
            username='test_user_2026',
            real_name='测试学生',
            user_type='student',
            student_no='2026001',
            is_active=True,
            phone='13800138000'
        )
        db.session.add(test_user)
        db.session.commit()
        print(f"✅ 创建测试用户: {test_user.real_name}")
    else:
        print(f"✅ 使用现有测试用户: {test_user.real_name}")

    # 检查是否已有有效验证码
    existing_code = DynamicCodeCache.query.filter_by(
        user_id=test_user.id
    ).filter(
        DynamicCodeCache.expires_at > datetime.utcnow()
    ).first()

    if existing_code:
        print(f"\n{'='*50}")
        print(f"✅ 已有有效验证码: {existing_code.code}")
        print(f"   用户: {test_user.real_name}")
        print(f"   身份: {test_user.user_type}")
        print(f"   学号: {test_user.student_no}")
        print(f"   过期时间: {existing_code.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        print(f"\n📱 请在门卫验证页面输入: {existing_code.code}")
        print(f"   访问 http://127.0.0.1:5000/guard-verify")
        exit(0)

    # 生成新的6位验证码
    code = f"{random.randint(100000, 999999)}"

    # 创建验证码记录，有效期24小时
    cache_entry = DynamicCodeCache(
        code=code,
        user_id=test_user.id,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        blacklisted=False
    )

    db.session.add(cache_entry)
    db.session.commit()

    print(f"\n{'='*50}")
    print(f"✅ 成功创建测试验证码!")
    print(f"{'='*50}")
    print(f"   验证码: {code}")
    print(f"   用户: {test_user.real_name}")
    print(f"   身份: {test_user.user_type}")
    print(f"   学号: {test_user.student_no}")
    print(f"   过期时间: {cache_entry.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    print(f"\n📱 请在门卫验证页面输入: {code}")
    print(f"   访问 http://127.0.0.1:5000/guard-verify")
