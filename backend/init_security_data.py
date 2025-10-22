"""
初始化保安端数据
创建保安测试账户和示例数据
"""

from datetime import datetime, date, time
from app import create_app, db
from app.models.user import User

def init_security_data():
    """初始化保安相关数据"""
    app = create_app()

    with app.app_context():
        print("开始初始化保安端数据...")

        # 创建保安测试账户
        security_users = [
            {
                'username': 'security01',
                'real_name': '张伟',
                'email': 'security01@example.com',
                'phone': '13800001111',
                'password': '123456'
            },
            {
                'username': 'security02',
                'real_name': '李强',
                'email': 'security02@example.com',
                'phone': '13800002222',
                'password': '123456'
            },
            {
                'username': 'security03',
                'real_name': '王磊',
                'email': 'security03@example.com',
                'phone': '13800003333',
                'password': '123456'
            },
            {
                'username': 'security04',
                'real_name': '赵敏',
                'email': 'security04@example.com',
                'phone': '13800004444',
                'password': '123456'
            },
            {
                'username': 'security05',
                'real_name': '刘洋',
                'email': 'security05@example.com',
                'phone': '13800005555',
                'password': '123456'
            }
        ]

        created_security = []

        for security_data in security_users:
            # 检查用户是否已存在
            existing_user = User.query.filter_by(username=security_data['username']).first()
            if existing_user:
                print(f"保安用户 {security_data['username']} 已存在，跳过创建")
                continue

            # 创建保安用户
            security = User(
                username=security_data['username'],
                real_name=security_data['real_name'],
                email=security_data['email'],
                phone=security_data['phone'],
                user_type='security',
                status='active'
            )
            security.set_password(security_data['password'])

            db.session.add(security)
            created_security.append(security)
            print(f"创建保安用户: {security_data['username']} ({security_data['real_name']})")

        try:
            db.session.commit()
            print("保安用户创建成功!")

            print("\n=== 保安端测试账户信息 ===")
            for security in created_security:
                print(f"用户名: {security.username}")
                print(f"姓名: {security.real_name}")
                print(f"邮箱: {security.email}")
                print(f"手机: {security.phone}")
                print(f"密码: 123456")
                print("-" * 30)

        except Exception as e:
            print(f"保存保安用户失败: {e}")
            db.session.rollback()
            return

        print("\n=== 访问地址 ===")
        print("保安专用端: http://127.0.0.1:5000/security-portal")
        print("\n初始化完成!")

if __name__ == '__main__':
    init_security_data()