"""
检查用户不匹配问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from app import create_app
from app.models.user import User
from app.utils.hmac_utils import generate_hmac_code
import time

def main():
    # 从SQLite直接查询第一个校友
    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "alumni" LIMIT 1')
    result = cursor.fetchone()
    conn.close()

    if not result:
        print("[ERROR] SQLite中没有校友用户")
        return

    sqlite_user = {
        'id': result[0],
        'real_name': result[1],
        'phone': result[2],
        'wechat_password': result[3]
    }

    print("=" * 80)
    print("  用户数据对比测试")
    print("=" * 80)

    print("\n[SQLite直接查询结果]")
    print(f"  ID: {sqlite_user['id']}")
    print(f"  姓名: {sqlite_user['real_name']}")
    print(f"  手机号: {sqlite_user['phone']}")
    print(f"  微信密码: {sqlite_user['wechat_password']}")

    # 使用Flask ORM查询
    app = create_app()
    with app.app_context():
        orm_user = User.query.filter(
            User.user_type == 'alumni',
            User.status == 'active'
        ).first()

        if not orm_user:
            print("\n[ERROR] ORM中没有校友用户")
            return

        print("\n[Flask ORM查询结果]")
        print(f"  ID: {orm_user.id}")
        print(f"  姓名: {orm_user.real_name}")
        print(f"  手机号: {orm_user.phone}")
        print(f"  微信密码: {orm_user.wechat_password}")
        print(f"  状态: {orm_user.status}")

        # 检查是否是同一个用户
        print("\n[Comparison Result]")
        if sqlite_user['id'] == orm_user.id:
            print("  [OK] Same user")
        else:
            print("  [FAIL] Different users!")
            print(f"    SQLite user ID: {sqlite_user['id']}")
            print(f"    ORM user ID: {orm_user.id}")

        # 生成HMAC码
        print(f"\n[HMAC Code Generation Test]")
        timestamp = int(time.time())
        print(f"  Timestamp: {timestamp}")

        code_sqlite = generate_hmac_code(sqlite_user['phone'], sqlite_user['wechat_password'], timestamp)
        code_orm = generate_hmac_code(orm_user.phone, orm_user.wechat_password, timestamp)

        print(f"  Code from SQLite data: {code_sqlite}")
        print(f"  Code from ORM data: {code_orm}")

        if code_sqlite == code_orm:
            print("  [OK] Codes match")
        else:
            print("  [FAIL] Codes different!")

        # 测试验证流程
        print(f"\n[Guard Verification Flow Simulation]")

        # 模拟门卫验证端点
        print(f"\n1. Generate code from SQLite data and verify:")
        test_code = code_sqlite
        print(f"  Test code: {test_code}")

        alumni_users = User.query.filter(
            User.user_type == 'alumni',
            User.status == 'active'
        ).all()

        print(f"  Alumni count from ORM: {len(alumni_users)}")

        for idx, alumni in enumerate(alumni_users):
            from app.utils.hmac_utils import verify_hmac_code
            verification = verify_hmac_code(test_code, alumni.phone, alumni.wechat_password, 3)

            if verification['valid']:
                print(f"  [OK] [{idx+1}] {alumni.real_name} (ID={alumni.id}) - Verification passed!")
                print(f"    Phone: {alumni.phone}")
                print(f"    Time diff: {int(time.time()) - verification['timestamp']}s")
                break
        else:
            print(f"  [FAIL] No alumni verified")
            print(f"\n  Manual check of first 3 alumni:")
            for idx, alumni in enumerate(alumni_users[:3]):
                test_code_for_alumni = generate_hmac_code(alumni.phone, alumni.wechat_password, timestamp)
                match = "[OK]" if test_code_for_alumni == test_code else "[FAIL]"
                print(f"    [{idx+1}] {alumni.real_name}: {test_code_for_alumni} {match}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
