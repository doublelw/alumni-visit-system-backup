import sys, os
sys.path.append('backend')
from app import create_app, db
from app.models.user import User

app = create_app('development')
with app.app_context():
    print("=== 设置核心账号密码 ===")

    # 设置student001密码
    student001 = User.query.filter_by(username='student001').first()
    if student001:
        student001.set_password('student123')
        print(f"✓ student001密码设置完成")

    # 设置teacher001密码
    teacher001 = User.query.filter_by(username='teacher001').first()
    if teacher001:
        teacher001.set_password('teacher123')
        print(f"✓ teacher001密码设置完成")

    # 设置parent001密码
    parent001 = User.query.filter_by(username='parent001').first()
    if parent001:
        parent001.set_password('parent123')
        print(f"✓ parent001密码设置完成")

    db.session.commit()
    print("\n=== 账号设置完成 ===")
    print("现在可以使用以下账号登录:")
    print("学生: student001 / student123")
    print("教师: teacher001 / teacher123")
    print("家长: parent001 / parent123")