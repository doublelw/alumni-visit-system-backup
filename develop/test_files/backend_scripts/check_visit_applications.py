"""
检查访问申请的详细信息
"""

import sqlite3

conn = sqlite3.connect('instance/alumni_system_dev.db')
cursor = conn.cursor()

print("=" * 80)
print("  检查访问申请数据")
print("=" * 80)

# 检查最近创建的几个访问申请
cursor.execute('''
    SELECT va.id, va.applicant_id, u.real_name, u.user_type, u.phone, u.wechat_password,
           va.access_code, va.visit_date, va.application_status
    FROM visit_applications va
    LEFT JOIN users u ON va.applicant_id = u.id
    ORDER BY va.id DESC
    LIMIT 10
''')

applications = cursor.fetchall()

print(f"\n最近10个访问申请:")
print(f"{'ID':<5} {'申请人ID':<10} {'姓名':<20} {'类型':<15} {'访问码':<10} {'状态':<15}")
print("-" * 80)

for app in applications:
    app_id = app[0]
    applicant_id = app[1]
    real_name = app[2] if app[2] else "N/A"
    user_type = app[3] if app[3] else "N/A"
    phone = app[4] if app[4] else "N/A"
    wechat_password = app[5] if app[5] else "N/A"
    access_code = app[6] if app[6] else "NULL"
    visit_date = app[7]
    status = app[8]

    print(f"{app_id:<5} {applicant_id:<10} {real_name:<20} {user_type:<15} {access_code:<10} {status:<15}")

# 检查申请ID 117的详细信息（之前失败的测试）
print("\n" + "=" * 80)
print("  检查申请ID 117的详细信息")
print("=" * 80)

cursor.execute('''
    SELECT va.id, va.applicant_id, u.real_name, u.user_type, u.phone, u.wechat_password,
           va.access_code, va.visit_date, va.application_status
    FROM visit_applications va
    LEFT JOIN users u ON va.applicant_id = u.id
    WHERE va.id = 117
''')

result = cursor.fetchone()
if result:
    print(f"\n申请ID: {result[0]}")
    print(f"申请人ID: {result[1]}")
    print(f"申请人姓名: {result[2]}")
    print(f"申请人类型: {result[3]}")
    print(f"手机号: {result[4]}")
    print(f"微信密码: {result[5]}")
    print(f"访问码: {result[6]}")
    print(f"访问日期: {result[7]}")
    print(f"申请状态: {result[8]}")

    # 检查这个用户是否还是校友类型
    if result[3] == 'alumni':
        print("\n[INFO] 申请人是校友类型，应该使用HMAC验证")
    else:
        print(f"\n[WARNING] 申请人类型是 {result[3]}，不是校友！")

        # 如果不是校友，找第一个校友对比
        cursor.execute('SELECT id, real_name, phone, wechat_password FROM users WHERE user_type = "alumni" LIMIT 1')
        alumni = cursor.fetchone()
        if alumni:
            print(f"\n第一个校友用户:")
            print(f"  ID: {alumni[0]}")
            print(f"  姓名: {alumni[1]}")
            print(f"  手机号: {alumni[2]}")
            print(f"  微信密码: {alumni[3]}")
else:
    print("\n[ERROR] 申请ID 117不存在")

conn.close()

print("\n" + "=" * 80)
