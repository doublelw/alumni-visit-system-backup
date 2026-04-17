"""
直接使用SQLite创建测试验证码
"""
import sqlite3
from datetime import datetime, timedelta

# 连接数据库
db_path = 'backend/instance/alumni_system_dev.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*50)
print("创建测试验证码")
print('='*50)

# 1. 创建测试用户
cursor.execute(
    "INSERT OR IGNORE INTO user_verification (username, real_name, user_type, student_no, phone, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
    ('test_user_2026', '测试学生', 'student', '2026001', '13800138000', 1)
)
print("✅ 测试用户已准备")

# 2. 检查是否已有验证码
cursor.execute("SELECT code, expires_at FROM dynamic_codes_cache WHERE code = '888888' AND expires_at > datetime('now')")
existing = cursor.fetchone()

if existing:
    print("\n" + "="*50)
    print("✅ 测试验证码已存在: 888888")
    print("="*50)
else:
    # 3. 获取用户ID
    cursor.execute("SELECT id FROM user_verification WHERE username = ?", ('test_user_2026',))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
        expires_at = (datetime.utcnow() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        # 4. 创建验证码
        cursor.execute(
            "INSERT INTO dynamic_codes_cache (code, user_id, expires_at, blacklisted, created_at) VALUES (?, ?, ?, 0, datetime('now'))",
            ('888888', user_id, expires_at)
        )
        conn.commit()
        print("\n" + "="*50)
        print("✅ 成功创建测试验证码!")
        print("="*50)

# 5. 查询验证码信息
cursor.execute("""
    SELECT dc.code, uv.real_name, uv.user_type, uv.student_no, dc.expires_at
    FROM dynamic_codes_cache dc
    JOIN user_verification uv ON dc.user_id = uv.id
    WHERE dc.code = '888888' AND dc.expires_at > datetime('now')
""")
result = cursor.fetchone()

if result:
    print(f"\n   验证码: {result[0]}")
    print(f"   姓名: {result[1]}")
    print(f"   身份: {result[2]}")
    print(f"   学号: {result[3]}")
    print(f"   过期时间: {result[4]}")
    print("="*50)
    print("\n📱 请在门卫验证页面输入: 888888")
    print("   访问: http://127.0.0.1:5000/guard-verify")
    print("="*50)

conn.close()
