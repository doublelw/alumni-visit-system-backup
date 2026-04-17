"""
创建临时测试验证码
"""
from backend.app import create_app, db
from backend.app.models.dynamic_code_cache import DynamicCodeCache
from backend.app.models.user_verification import UserVerification
from datetime import datetime, timedelta

def create_test_code():
    """创建一个临时测试验证码"""
    app = create_app()

    with app.app_context():
        # 查找或创建测试用户
        test_user = UserVerification.query.filter_by(username='test_user').first()

        if not test_user:
            # 创建测试用户
            test_user = UserVerification(
                username='test_user',
                real_name='张三',
                user_type='student',
                student_no='2024001',
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
            print(f"\n✅ 已有有效验证码: {existing_code.code}")
            print(f"   过期时间: {existing_code.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   用户: {test_user.real_name} ({test_user.user_type})")
            return existing_code.code

        # 生成新的6位验证码
        import random
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

        print(f"\n✅ 成功创建测试验证码!")
        print(f"   验证码: {code}")
        print(f"   用户: {test_user.real_name} ({test_user.user_type})")
        print(f"   学号: {test_user.student_no}")
        print(f"   过期时间: {cache_entry.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📱 请在门卫验证页面输入: {code}")

        return code

if __name__ == '__main__':
    create_test_code()
