"""
测试新增的家长端API
"""
import sys
sys.path.insert(0, 'backend')

from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    print("=" * 60)
    print("测试家长端API数据准备")
    print("=" * 60)

    # 查找测试家长
    parent = User.query.filter_by(phone='13900002002').first()

    if not parent:
        print("\n错误：未找到测试家长（13900002002）")
        print("请先创建测试数据")
        sys.exit(1)

    print(f"\n测试家长: {parent.real_name}")
    print(f"手机号: {parent.phone}")
    print(f"密码: {parent.wechat_password}")
    print(f"关联学生ID: {parent.parent_student_id}")

    # 查找关联学生
    if parent.parent_student_id:
        student = User.query.get(parent.parent_student_id)
        if student:
            print(f"\n关联学生:")
            print(f"  姓名: {student.real_name}")
            print(f"  年级: {student.grade}")
            print(f"  班级: {student.class_id}")
            print(f"  手机号: {student.phone}")
            print(f"  密码: {student.wechat_password}")

    # 生成HMAC码测试
    print("\n" + "=" * 60)
    print("测试HMAC码生成")
    print("=" * 60)

    from app.utils.hmac_utils import generate_hmac_code
    import time

    timestamp = int(time.time())
    code = generate_hmac_code(parent.phone, parent.wechat_password, timestamp)

    print(f"\n生成的6位码: {code}")
    print(f"使用时间戳: {timestamp}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")

    # 测试API端点路径
    print("\n" + "=" * 60)
    print("API端点（需要在Flask运行时测试）")
    print("=" * 60)

    print("\n家长端API:")
    print("  POST /api/wechat/parent/generate-code")
    print("  请求体: {\"phone\": \"13900002002\", \"password\": \"88\"}")
    print(f"  预期返回: {{\"success\": true, \"data\": {{\"code\": \"{code}\"}}}}")

    print("\n  POST /api/wechat/parent/get-student-info")
    print("  请求体: {\"phone\": \"13900002002\", \"password\": \"88\"}")
    print("  预期返回: 学生信息和家长信息")

    print("\n老师特批API:")
    print("  POST /api/wechat/teacher/special-approve")
    if parent.parent_student_id:
        student = User.query.get(parent.parent_student_id)
        if student:
            print(f"  请求体: {{\"student_name\": \"{student.real_name}\", \"grade\": \"{student.grade}\", \"class_id\": \"{student.class_id}\", \"reason\": \"测试特批\"}}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 启动Flask服务器: python backend/run.py")
    print("2. 访问家长页面: http://localhost:5000/parent-simple")
    print("3. 测试生成码功能")
    print("4. 测试老师特批功能")
