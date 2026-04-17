"""
添加5个校友测试账号
手机号：13800002001 - 13800002005
密码：统一为 88
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models.user import User
from app.models.alumni_profile import AlumniProfile

def create_test_alumni():
    """创建5个测试校友账号"""

    # 5个测试校友数据
    test_alumni = [
        {
            'phone': '13800002001',
            'real_name': '赵强',
            'graduation_year': 2018,
            'company': '腾讯',
            'employee_id': 'A2018001',
            'student_id': '20180001'
        },
        {
            'phone': '13800002002',
            'real_name': '孙丽',
            'graduation_year': 2019,
            'company': '百度',
            'employee_id': 'A2019002',
            'student_id': '20190002'
        },
        {
            'phone': '13800002003',
            'real_name': '周杰',
            'graduation_year': 2020,
            'company': '字节跳动',
            'employee_id': 'A2020003',
            'student_id': '20200003'
        },
        {
            'phone': '13800002004',
            'real_name': '吴敏',
            'graduation_year': 2021,
            'company': '美团',
            'employee_id': 'A2021004',
            'student_id': '20210004'
        },
        {
            'phone': '13800002005',
            'real_name': '郑涛',
            'graduation_year': 2022,
            'company': '京东',
            'employee_id': 'A2022005',
            'student_id': '20220005'
        }
    ]

    app = create_app()

    with app.app_context():
        created_count = 0
        updated_count = 0
        id_card_base = 11010120000101000  # 身份证号基数

        for i, alumni_data in enumerate(test_alumni):
            phone = alumni_data['phone']
            real_name = alumni_data['real_name']
            id_card = str(id_card_base + i)  # 为每个校友生成唯一身份证号

            # 检查是否已存在
            existing_user = User.query.filter_by(phone=phone).first()

            if existing_user:
                print(f"[UPDATE] User exists, updating to alumni: {real_name} ({phone})")

                # 更新为校友类型
                existing_user.user_type = 'alumni'
                existing_user.wechat_password = '88'
                existing_user.status = 'active'

                # 更新或创建校友档案
                if not existing_user.alumni_profile:
                    profile = AlumniProfile(
                        user_id=existing_user.id,
                        student_id=alumni_data['student_id'],  # 必填
                        graduation_year=alumni_data['graduation_year'],
                        class_name='高三(1)班',  # 默认班级
                        division='高中部',  # 默认学部
                        id_card=id_card,  # 唯一身份证号
                        contact_teacher='张老师',  # 默认联系老师
                        contact_teacher_phone='13800000000',  # 默认联系电话
                        work_unit=alumni_data['company'],  # 工作单位
                        position='工程师',  # 默认职位
                        approval_status='approved'  # 测试账号直接通过
                    )
                    db.session.add(profile)
                else:
                    existing_user.alumni_profile.graduation_year = alumni_data['graduation_year']
                    existing_user.alumni_profile.work_unit = alumni_data['company']

                updated_count += 1

            else:
                print(f"[CREATE] New alumni: {real_name} ({phone})")

                # 生成密码哈希（虽然是测试账号，但需要满足数据库约束）
                import hashlib
                password_hash = hashlib.sha256('test_password_123'.encode()).hexdigest()

                # 创建新用户
                user = User(
                    username=phone,  # 使用手机号作为用户名
                    password_hash=password_hash,
                    phone=phone,
                    real_name=real_name,
                    user_type='alumni',
                    wechat_password='88',  # 统一密码
                    employee_id=alumni_data.get('employee_id'),
                    status='active'
                )
                db.session.add(user)
                db.session.flush()  # 获取user.id

                # 创建校友档案
                profile = AlumniProfile(
                    user_id=user.id,
                    student_id=alumni_data['student_id'],  # 必填
                    graduation_year=alumni_data['graduation_year'],
                    class_name='高三(1)班',  # 默认班级
                    division='高中部',  # 默认学部
                    id_card=id_card,  # 唯一身份证号
                    contact_teacher='张老师',  # 默认联系老师
                    contact_teacher_phone='13800000000',  # 默认联系电话
                    work_unit=alumni_data['company'],  # 工作单位
                    position='工程师',  # 默认职位
                    approval_status='approved'  # 测试账号直接通过
                )
                db.session.add(profile)

                created_count += 1

        try:
            db.session.commit()
            print(f"\n[SUCCESS] Operation completed!")
            print(f"   Created: {created_count} users")
            print(f"   Updated: {updated_count} users")
            print(f"\n[TEST ACCOUNTS]")
            print(f"   {'Phone':<15} {'Name':<10} {'Grad Year':<10} {'Company':<15} {'Password'}")
            print(f"   {'-'*70}")
            for alumni_data in test_alumni:
                print(f"   {alumni_data['phone']:<15} {alumni_data['real_name']:<10} {alumni_data['graduation_year']:<10} {alumni_data['company']:<15} 88")
            print(f"\n[INFO] All alumni passwords: 88")

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_test_alumni()
