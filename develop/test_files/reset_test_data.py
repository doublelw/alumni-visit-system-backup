"""
清空并重新生成测试数据
"""
import sys
import os

# 添加backend路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from datetime import datetime

def reset_database():
    """清空并重新生成测试数据"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Reset and Generate Test Data")
        print("=" * 60)

        # 清空users表
        print("\n1. Clearing users table...")
        User.query.delete()
        db.session.commit()
        print("   [OK] Cleared")

        # 生成测试数据
        print("\n2. Generating test data...")

        # ==================== 老师（班主任）====================
        teachers = [
            {
                'username': 'teacher_wang',
                'real_name': '王老师',
                'phone': '13800000001',
                'wechat_password': '1234',
                'grade': '高一',
                'class_id': '1班',
                'is_class_teacher': True
            },
            {
                'username': 'teacher_li',
                'real_name': '李老师',
                'phone': '13800000002',
                'wechat_password': '1234',
                'grade': '高一',
                'class_id': '2班',
                'is_class_teacher': True
            }
        ]

        teacher_records = []
        for t in teachers:
            teacher = User(
                username=t['username'],
                password_hash='hashed_password',  # 临时值
                real_name=t['real_name'],
                phone=t['phone'],
                wechat_password=t['wechat_password'],
                email=t['username'] + '@school.edu',
                user_type='teacher',
                status='active',
                grade=t['grade'],
                class_id=t['class_id'],
                is_class_teacher=t['is_class_teacher'],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            teacher.set_password('123456')  # 设置管理员密码
            db.session.add(teacher)
            db.session.flush()  # 获取ID
            teacher_records.append(teacher)
            print(f"   [OK] Teacher: {t['real_name']} ({t['phone']}) - Password: {t['wechat_password']}")

        # ==================== 门卫 ====================
        security = User(
            username='security_zhang',
            password_hash='hashed_password',
            real_name='张保安',
            phone='13900000000',
            wechat_password='1234',
            email='security@school.edu',
            user_type='security',
            status='active',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        security.set_password('123456')
        db.session.add(security)
        print(f"   [OK] Security: Zhang (13900000000) - Password: 1234")

        # ==================== 学生和家长 ====================
        students_data = [
            # 王老师班的学生（1班）
            {
                'student': {
                    'username': 'student_001',
                    'real_name': '张明',
                    'phone': '13900001001',
                    'student_id': '2024001',
                    'grade': '高一',
                    'class_id': '1班',
                    'wechat_password': '88'
                },
                'parent': {
                    'username': 'parent_001',
                    'real_name': '张明爸爸',
                    'phone': '13900002001',
                    'wechat_password': '88'
                },
                'teacher_id': teacher_records[0].id
            },
            {
                'student': {
                    'username': 'student_002',
                    'real_name': '李华',
                    'phone': '13900001002',
                    'student_id': '2024002',
                    'grade': '高一',
                    'class_id': '1班',
                    'wechat_password': '88'
                },
                'parent': {
                    'username': 'parent_002',
                    'real_name': '李华妈妈',
                    'phone': '13900002002',
                    'wechat_password': '88'
                },
                'teacher_id': teacher_records[0].id
            },
            {
                'student': {
                    'username': 'student_003',
                    'real_name': '王芳',
                    'phone': '13900001003',
                    'student_id': '2024003',
                    'grade': '高一',
                    'class_id': '1班',
                    'wechat_password': '88'
                },
                'parent': {
                    'username': 'parent_003',
                    'real_name': '王芳爸爸',
                    'phone': '13900002003',
                    'wechat_password': '88'
                },
                'teacher_id': teacher_records[0].id
            },
            # 李老师班的学生（2班）
            {
                'student': {
                    'username': 'student_004',
                    'real_name': '赵强',
                    'phone': '13900001004',
                    'student_id': '2024004',
                    'grade': '高一',
                    'class_id': '2班',
                    'wechat_password': '88'
                },
                'parent': {
                    'username': 'parent_004',
                    'real_name': '赵强妈妈',
                    'phone': '13900002004',
                    'wechat_password': '88'
                },
                'teacher_id': teacher_records[1].id
            },
            {
                'student': {
                    'username': 'student_005',
                    'real_name': '刘洋',
                    'phone': '13900001005',
                    'student_id': '2024005',
                    'grade': '高一',
                    'class_id': '2班',
                    'wechat_password': '88'
                },
                'parent': {
                    'username': 'parent_005',
                    'real_name': '刘洋爸爸',
                    'phone': '13900002005',
                    'wechat_password': '88'
                },
                'teacher_id': teacher_records[1].id
            }
        ]

        for data in students_data:
            # 创建家长
            parent = User(
                username=data['parent']['username'],
                password_hash='hashed_password',
                real_name=data['parent']['real_name'],
                phone=data['parent']['phone'],
                wechat_password=data['parent']['wechat_password'],
                email=data['parent']['username'] + '@family.edu',
                user_type='parent',
                status='active',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            parent.set_password('123456')
            db.session.add(parent)
            db.session.flush()  # 获取家长ID

            # 创建学生，关联家长
            student = User(
                username=data['student']['username'],
                password_hash='hashed_password',
                real_name=data['student']['real_name'],
                phone=data['student']['phone'],
                wechat_password=data['student']['wechat_password'],
                email=data['student']['username'] + '@student.edu',
                user_type='student',
                status='active',
                student_id=data['student']['student_id'],
                grade=data['student']['grade'],
                class_id=data['student']['class_id'],
                student_parent_id=parent.id,  # 关联家长
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            student.set_password('123456')
            db.session.add(student)
            db.session.flush()  # 获取学生ID

            # 更新家长，关联学生
            parent.parent_student_id = student.id

            print(f"   [OK] Student: {data['student']['real_name']} ({data['student']['grade']} {data['student']['class_id']}) - Password: {data['student']['wechat_password']}")
            print(f"       Parent: {data['parent']['real_name']} ({data['parent']['phone']}) - Password: {data['parent']['wechat_password']}")

        # ==================== 校友 ====================
        alumni_data = [
            {
                'username': 'alumni_001',
                'real_name': '陈建国',
                'phone': '13800001001',
                'wechat_password': '88',
                'student_id': '2010001',
                'graduate_year': '2010'
            },
            {
                'username': 'alumni_002',
                'real_name': '周梅',
                'phone': '13800001002',
                'wechat_password': '88',
                'student_id': '2011002',
                'graduate_year': '2011'
            },
            {
                'username': 'alumni_003',
                'real_name': '吴磊',
                'phone': '13800001003',
                'wechat_password': '88',
                'student_id': '2012003',
                'graduate_year': '2012'
            },
            {
                'username': 'alumni_004',
                'real_name': '郑丽',
                'phone': '13800001004',
                'wechat_password': '88',
                'student_id': '2013004',
                'graduate_year': '2013'
            },
            {
                'username': 'alumni_005',
                'real_name': '孙伟',
                'phone': '13800001005',
                'wechat_password': '88',
                'student_id': '2014005',
                'graduate_year': '2014'
            }
        ]

        for data in alumni_data:
            alumni = User(
                username=data['username'],
                password_hash='hashed_password',
                real_name=data['real_name'],
                phone=data['phone'],
                wechat_password=data['wechat_password'],
                email=data['username'] + '@alumni.edu',
                user_type='alumni',
                status='active',
                student_id=data['student_id'],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            alumni.set_password('123456')
            db.session.add(alumni)
            print(f"   [OK] Alumni: {data['real_name']} ({data['phone']}) - Password: {data['wechat_password']}")

        # 提交所有更改
        db.session.commit()

        print("\n" + "=" * 60)
        print("[SUCCESS] Data generation completed!")
        print("=" * 60)

if __name__ == '__main__':
    reset_database()
