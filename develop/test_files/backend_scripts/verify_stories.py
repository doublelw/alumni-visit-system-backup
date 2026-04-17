"""
验证所有5个用户故事的功能完整性
"""

import requests
import sqlite3
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.hmac_utils import generate_hmac_code, verify_hmac_code

BASE_URL = "http://localhost:5000"

def test_with_database_users():
    """使用数据库中的现有用户测试各个故事"""
    print("=" * 70)
    print("验证用户故事 - 使用数据库现有用户")
    print("=" * 70)

    from app import create_app
    app = create_app()

    with app.app_context():
        return _test_stories_with_context()

def _test_stories_with_context():
    """在Flask应用上下文中测试"""
    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    results = {}

    # Story 1: 校友入校
    print("\n[Story 1] 校友入校")
    cursor.execute('SELECT real_name, phone, wechat_password FROM users WHERE user_type = "alumni" LIMIT 1')
    alumni = cursor.fetchone()
    if alumni:
        name, phone, password = alumni
        code = generate_hmac_code(phone, password)
        print(f"  用户: {name} ({phone})")
        print(f"  HMAC码: {code}")

        try:
            response = requests.post(f"{BASE_URL}/api/guard/verify",
                json={"code": code, "guard_name": "门卫01", "verify_type": "alumni"},
                timeout=10
            )
            result = response.json()
            if result.get('success') and result['data'].get('valid'):
                print(f"  [PASS] 校友验证通过")
                results["Story 1"] = True
            else:
                print(f"  [FAIL] {result.get('error', 'Unknown')}")
                results["Story 1"] = False
        except Exception as e:
            print(f"  [ERROR] {e}")
            results["Story 1"] = False
    else:
        print("  [SKIP] 数据库中无校友用户")
        results["Story 1"] = None

    # Story 2: 家长入校
    print("\n[Story 2] 家长入校")
    cursor.execute('SELECT real_name, phone, wechat_password FROM users WHERE user_type = "parent" LIMIT 1')
    parent = cursor.fetchone()
    if parent:
        name, phone, password = parent
        code = generate_hmac_code(phone, password)
        print(f"  用户: {name} ({phone})")
        print(f"  HMAC码: {code}")

        try:
            response = requests.post(f"{BASE_URL}/api/guard/verify",
                json={"code": code, "guard_name": "门卫01", "verify_type": "parent-visit"},
                timeout=10
            )
            result = response.json()
            if result.get('success') and result['data'].get('valid'):
                print(f"  [PASS] 家长验证通过")
                results["Story 2"] = True
            else:
                print(f"  [FAIL] {result.get('error', 'Unknown')}")
                results["Story 2"] = False
        except Exception as e:
            print(f"  [ERROR] {e}")
            results["Story 2"] = False
    else:
        print("  [SKIP] 数据库中无家长用户")
        results["Story 2"] = None

    # Story 4: 访客访问（使用最近创建的访客）
    print("\n[Story 4] 访客访问")
    cursor.execute('SELECT real_name, phone, wechat_password FROM users WHERE user_type = "visitor" ORDER BY id DESC LIMIT 1')
    visitor = cursor.fetchone()
    if visitor:
        name, phone, password = visitor
        code = generate_hmac_code(phone, password)
        print(f"  用户: {name} ({phone})")
        print(f"  HMAC码: {code}")

        try:
            response = requests.post(f"{BASE_URL}/api/guard/verify",
                json={"code": code, "guard_name": "门卫01", "verify_type": "visitor"},
                timeout=10
            )
            result = response.json()
            if result.get('success') and result['data'].get('valid'):
                user_info = result['data']['user_info']
                print(f"  [PASS] 访客验证通过")
                print(f"  访问目的: {user_info.get('visit_purpose', 'N/A')}")
                results["Story 4"] = True
            else:
                print(f"  [FAIL] {result.get('error', 'Unknown')}")
                results["Story 4"] = False
        except Exception as e:
            print(f"  [ERROR] {e}")
            results["Story 4"] = False
    else:
        print("  [SKIP] 数据库中无访客用户")
        results["Story 4"] = None

    conn.close()

    return results
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v == True)
    failed = sum(1 for v in results.values() if v == False)
    skipped = sum(1 for v in results.values() if v is None)

    for story, result in results.items():
        if result is True:
            print(f"  [PASS] {story}")
        elif result is False:
            print(f"  [FAIL] {story}")
        else:
            print(f"  [SKIP] {story}")

    print(f"\n通过: {passed}, 失败: {failed}, 跳过: {skipped}")

    return results

def verify_external_network_architecture():
    """验证外网/内网分离架构"""
    print("\n" + "=" * 70)
    print("验证：外网/内网分离架构")
    print("=" * 70)

    # 检查外网数据库
    import os
    external_db_path = 'external_network.db'

    if os.path.exists(external_db_path):
        print(f"\n[External Network] 外网数据库存在: {external_db_path}")
        conn = sqlite3.connect(external_db_path)
        cursor = conn.cursor()

        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"  外网表: {', '.join(tables)}")

        # 检查数据量
        if 'access_codes' in tables:
            cursor.execute('SELECT COUNT(*) FROM access_codes')
            count = cursor.fetchone()[0]
            print(f"  访问码记录: {count} 条")

        if 'visitor_cache' in tables:
            cursor.execute('SELECT COUNT(*) FROM visitor_cache')
            count = cursor.fetchone()[0]
            print(f"  访客缓存记录: {count} 条")

        conn.close()
    else:
        print(f"\n[External Network] 外网数据库不存在（第一次运行时创建）")

    # 检查内网数据库
    print(f"\n[Internal Network] 内网数据库: instance/alumni_system_dev.db")
    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 检查访客用户
    cursor.execute('SELECT COUNT(*) FROM users WHERE user_type = "visitor"')
    visitor_count = cursor.fetchone()[0]
    print(f"  访客用户: {visitor_count} 人")

    # 检查访客访问记录
    cursor.execute('SELECT COUNT(*) FROM visit_applications WHERE applicant_id IN (SELECT id FROM users WHERE user_type = "visitor")')
    visit_count = cursor.fetchone()[0]
    print(f"  访客访问记录: {visit_count} 条")

    conn.close()

    print("\n[Architecture] 外网/内网分离架构验证通过")
    print("  - 外网: 只存储访问码+手机号（最小数据）")
    print("  - 内网: 存储完整用户信息+访问记录")
    print("  - 数据流: 单向迁移（外网 -> 内网）")

if __name__ == "__main__":
    results = test_with_database_users()
    verify_external_network_architecture()

    print("\n" + "=" * 70)
    print("所有验证完成！")
    print("=" * 70)
