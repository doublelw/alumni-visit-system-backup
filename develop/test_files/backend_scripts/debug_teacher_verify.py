"""
调试老师验证码问题
"""
import sys
sys.path.insert(0, '.')

from app import create_app, db
from app.models.user import User
from app.utils.hmac_utils import generate_hmac_code, verify_hmac_code
import time

app = create_app()

with app.app_context():
    print("=" * 60)
    print("调试老师验证码问题")
    print("=" * 60)

    # 1. 测试家长码
    print("\n【测试1：家长码生成与验证】")
    parent = User.query.filter_by(phone='13900002002').first()

    if parent:
        print(f"家长信息:")
        print(f"  姓名: {parent.real_name}")
        print(f"  手机号: {parent.phone}")
        print(f"  密码: {parent.wechat_password}")

        # 生成码
        timestamp = int(time.time())
        code = generate_hmac_code(parent.phone, parent.wechat_password, timestamp)
        print(f"\n生成的6位码: {code}")
        print(f"使用时间戳: {timestamp}")

        # 立即验证（应该成功）
        verification = verify_hmac_code(code, parent.phone, parent.wechat_password, 24*60)
        print(f"\n立即验证结果:")
        print(f"  有效: {verification['valid']}")
        print(f"  消息: {verification['message']}")
        print(f"  时间戳: {verification.get('timestamp')}")

    else:
        print("未找到家长: 13900002002")

    # 2. 测试学生码
    print("\n" + "=" * 60)
    print("【测试2：学生码生成与验证】")

    # 查找学生（通过家长关联）
    if parent and parent.parent_student_id:
        student = User.query.get(parent.parent_student_id)

        if student:
            print(f"学生信息:")
            print(f"  姓名: {student.real_name}")
            print(f"  手机号: {student.phone}")
            print(f"  密码: {student.wechat_password}")

            # 生成码
            timestamp2 = int(time.time())
            code2 = generate_hmac_code(student.phone, student.wechat_password, timestamp2)
            print(f"\n生成的6位码: {code2}")
            print(f"使用时间戳: {timestamp2}")

            # 立即验证
            verification2 = verify_hmac_code(code2, student.phone, student.wechat_password, 24*60)
            print(f"\n立即验证结果:")
            print(f"  有效: {verification2['valid']}")
            print(f"  消息: {verification2['message']}")
            print(f"  时间戳: {verification2.get('timestamp')}")
        else:
            print("未找到学生")
    else:
        print("家长未关联学生")

    # 3. 测试查询所有家长
    print("\n" + "=" * 60)
    print("【测试3：查询所有家长用户】")

    parents = User.query.filter(
        User.user_type.like('%parent%'),
        User.status == 'active'
    ).all()

    print(f"找到 {len(parents)} 个家长:")
    for p in parents[:5]:  # 只显示前5个
        print(f"  - {p.real_name} | {p.phone} | 密码:{p.wechat_password}")

    # 4. 测试查询所有学生
    print("\n" + "=" * 60)
    print("【测试4：查询所有学生用户】")

    students = User.query.filter(
        User.user_type == 'student',
        User.status == 'active'
    ).all()

    print(f"找到 {len(students)} 个学生:")
    for s in students[:5]:  # 只显示前5个
        print(f"  - {s.real_name} | {s.phone} | 密码:{s.wechat_password}")

    # 5. 模拟老师验证逻辑
    print("\n" + "=" * 60)
    print("【测试5：模拟老师验证码逻辑】")

    test_code = code  # 使用刚才生成的家长码
    print(f"测试码: {test_code}")

    # 尝试匹配家长
    matched_parent = None
    for parent in parents:
        if not parent.phone or not parent.wechat_password:
            continue
        verification = verify_hmac_code(
            test_code, parent.phone, parent.wechat_password, 24*60
        )
        if verification['valid']:
            matched_parent = parent
            print(f"\n✅ 匹配到家长: {parent.real_name}")
            break

    if matched_parent:
        student = User.query.get(matched_parent.parent_student_id) if matched_parent.parent_student_id else None
        if student:
            print(f"  关联学生: {student.real_name}")
        else:
            print(f"  无关联学生")
    else:
        print("\n❌ 未匹配到任何家长")
        print("可能原因:")
        print("  1. 码已过期（超过24小时）")
        print("  2. phone或password不匹配")
        print("  3. 数据库中wechat_password为空")

    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)
