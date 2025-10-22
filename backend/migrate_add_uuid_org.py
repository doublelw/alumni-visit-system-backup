#!/usr/bin/env python
"""
数据库迁移脚本 - 添加UUID和组织字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uuid
from datetime import datetime
from sqlalchemy import text
from app import create_app, db
from app.models.user import User
from app.models.organization import Organization, UserRole, UserRoleAssignment

def create_default_organizations():
    """创建默认组织架构"""

    # 检查是否已有组织数据
    if Organization.query.count() > 0:
        print("组织架构已存在，跳过创建...")
        # 返回现有组织的ID
        school = Organization.query.filter_by(code='SCHOOL_MAIN').first()
        if not school:
            school = Organization.query.first()

        org_ids = {}
        for org in Organization.query.all():
            if org.code == 'SCHOOL_MAIN':
                org_ids['school'] = org.id
            elif org.code == 'MAIN_CAMPUS':
                org_ids['campus'] = org.id
            elif org.code == 'COLLEGE_CS':
                org_ids['college1'] = org.id
            elif org.code == 'COLLEGE_IE':
                org_ids['college2'] = org.id
            elif org.code == 'COLLEGE_MGMT':
                org_ids['college3'] = org.id
            elif org.code == 'DEPT_CS':
                org_ids['dept1'] = org.id
            elif org.code == 'DEPT_SE':
                org_ids['dept2'] = org.id
            elif org.code == 'OFFICE_ADMIN':
                org_ids['admin_office'] = org.id
            elif org.code == 'OFFICE_SECURITY':
                org_ids['security_office'] = org.id
            elif org.code == 'OFFICE_ALUMNI':
                org_ids['alumni_office'] = org.id
            elif org.code == 'CLASS_CS2020':
                org_ids['class1'] = org.id
            elif org.code == 'CLASS_SE2021':
                org_ids['class2'] = org.id

        return org_ids

    # 创建根级组织 - 学校
    school = Organization(
        name='示范大学',
        code='SCHOOL_MAIN',
        description='示范大学主校区',
        org_type='school',
        level=1,
        path='/1',
        status='active',
        sort_order=1
    )
    db.session.add(school)
    db.session.flush()  # 获取ID

    # 创建校区
    campus = Organization(
        name='主校区',
        code='MAIN_CAMPUS',
        description='示范大学主校区',
        parent_id=school.id,
        level=2,
        path=f'/{school.id}/2',
        org_type='campus',
        status='active',
        sort_order=1
    )
    db.session.add(campus)
    db.session.flush()

    # 创建学院
    college1 = Organization(
        name='计算机科学与技术学院',
        code='COLLEGE_CS',
        description='计算机科学与技术学院',
        parent_id=campus.id,
        level=3,
        path=f'/{school.id}/{campus.id}/3',
        org_type='college',
        status='active',
        sort_order=1
    )

    college2 = Organization(
        name='信息工程学院',
        code='COLLEGE_IE',
        description='信息工程学院',
        parent_id=campus.id,
        level=3,
        path=f'/{school.id}/{campus.id}/4',
        org_type='college',
        status='active',
        sort_order=2
    )

    college3 = Organization(
        name='管理学院',
        code='COLLEGE_MGMT',
        description='管理学院',
        parent_id=campus.id,
        level=3,
        path=f'/{school.id}/{campus.id}/5',
        org_type='college',
        status='active',
        sort_order=3
    )

    db.session.add_all([college1, college2, college3])
    db.session.flush()

    # 创建部门
    dept1 = Organization(
        name='计算机科学系',
        code='DEPT_CS',
        description='计算机科学系',
        parent_id=college1.id,
        level=4,
        path=f'/{school.id}/{campus.id}/{college1.id}/6',
        org_type='department',
        status='active',
        sort_order=1
    )

    dept2 = Organization(
        name='软件工程系',
        code='DEPT_SE',
        description='软件工程系',
        parent_id=college1.id,
        level=4,
        path=f'/{school.id}/{campus.id}/{college1.id}/7',
        org_type='department',
        status='active',
        sort_order=2
    )

    admin_office = Organization(
        name='行政办公室',
        code='OFFICE_ADMIN',
        description='行政办公室',
        parent_id=school.id,
        level=2,
        path=f'/{school.id}/8',
        org_type='office',
        status='active',
        sort_order=2
    )

    security_office = Organization(
        name='保卫处',
        code='OFFICE_SECURITY',
        description='保卫处',
        parent_id=school.id,
        level=2,
        path=f'/{school.id}/9',
        org_type='office',
        status='active',
        sort_order=3
    )

    alumni_office = Organization(
        name='校友办公室',
        code='OFFICE_ALUMNI',
        description='校友办公室',
        parent_id=school.id,
        level=2,
        path=f'/{school.id}/10',
        org_type='office',
        status='active',
        sort_order=4
    )

    db.session.add_all([dept1, dept2, admin_office, security_office, alumni_office])
    db.session.flush()

    # 创建班级
    class1 = Organization(
        name='计算机科学2020届',
        code='CLASS_CS2020',
        description='计算机科学专业2020届毕业生',
        parent_id=dept1.id,
        level=5,
        path=f'/{school.id}/{campus.id}/{college1.id}/{dept1.id}/11',
        org_type='class',
        status='active',
        sort_order=1
    )

    class2 = Organization(
        name='软件工程2021届',
        code='CLASS_SE2021',
        description='软件工程专业2021届毕业生',
        parent_id=dept2.id,
        level=5,
        path=f'/{school.id}/{campus.id}/{college1.id}/{dept2.id}/12',
        org_type='class',
        status='active',
        sort_order=1
    )

    db.session.add_all([class1, class2])

    return {
        'school': school.id,
        'campus': campus.id,
        'college1': college1.id,
        'college2': college2.id,
        'college3': college3.id,
        'dept1': dept1.id,
        'dept2': dept2.id,
        'admin_office': admin_office.id,
        'security_office': security_office.id,
        'alumni_office': alumni_office.id,
        'class1': class1.id,
        'class2': class2.id
    }

def migrate_database():
    """执行数据库迁移"""

    app = create_app()
    with app.app_context():

        print("开始数据库迁移...")

        # 检查是否已经有uuid字段
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]

        # 添加新字段（如果不存在）
        if 'uuid' not in columns:
            print("添加uuid字段...")
            db.session.execute(text("""
                ALTER TABLE users ADD COLUMN uuid VARCHAR(36)
            """))

        if 'organization_id' not in columns:
            print("添加organization_id字段...")
            db.session.execute(text("""
                ALTER TABLE users ADD COLUMN organization_id INTEGER
            """))

        if 'student_id' not in columns:
            print("添加student_id字段...")
            db.session.execute(text("""
                ALTER TABLE users ADD COLUMN student_id VARCHAR(50)
            """))

        if 'employee_id' not in columns:
            print("添加employee_id字段...")
            db.session.execute(text("""
                ALTER TABLE users ADD COLUMN employee_id VARCHAR(50)
            """))

        # 创建组织表（如果不存在）
        print("创建组织架构表...")
        Organization.__table__.create(db.engine, checkfirst=True)
        UserRole.__table__.create(db.engine, checkfirst=True)
        UserRoleAssignment.__table__.create(db.engine, checkfirst=True)

        db.session.commit()

        # 创建默认组织架构
        print("创建默认组织架构...")
        org_ids = create_default_organizations()
        db.session.commit()

        # 为现有用户生成UUID和分配组织
        print("为现有用户生成UUID和分配组织...")
        users = User.query.all()

        for user in users:
            # 生成UUID（如果还没有）
            if not user.uuid:
                user.uuid = str(uuid.uuid4())

            # 根据用户类型分配组织和ID
            if user.user_type == 'alumni':
                # 校友分配到相关学院或班级
                if '2020' in user.username or 'alumni2020' in user.username:
                    user.organization_id = org_ids['class1']
                elif '2021' in user.username or 'alumni2021' in user.username:
                    user.organization_id = org_ids['class2']
                else:
                    user.organization_id = org_ids['college1']  # 默认分配到计算机学院

                # 生成学号
                if not user.student_id:
                    user.student_id = f"STU{user.id:06d}"

            elif user.user_type == 'teacher':
                # 教师分配到相关学院
                if 'teacher001' in user.username or 'teacher002' in user.username:
                    user.organization_id = org_ids['dept1']  # 计算机科学系
                elif 'teacher003' in user.username:
                    user.organization_id = org_ids['dept2']  # 软件工程系
                else:
                    user.organization_id = org_ids['college1']  # 默认分配到计算机学院

                # 生成工号
                if not user.employee_id:
                    user.employee_id = f"EMP{user.id:06d}"

            elif user.user_type == 'admin':
                # 管理员分配到行政办公室
                user.organization_id = org_ids['admin_office']
                if not user.employee_id:
                    user.employee_id = f"ADM{user.id:06d}"

            elif user.user_type == 'security':
                # 保安分配到保卫处
                user.organization_id = org_ids['security_office']
                if not user.employee_id:
                    user.employee_id = f"SEC{user.id:06d}"

        db.session.commit()

        # 创建默认角色
        print("创建默认角色...")

        # 检查是否已有角色
        if UserRole.query.count() == 0:
            roles = [
                UserRole(
                    name='super_admin',
                    display_name='超级管理员',
                    description='系统超级管理员，拥有所有权限',
                    permissions='["user_management", "org_management", "visit_approval", "system_settings", "data_export", "audit_logs"]'
                ),
                UserRole(
                    name='org_admin',
                    display_name='组织管理员',
                    description='组织管理员，管理本组织和下属组织',
                    permissions='["user_management", "org_management", "visit_approval", "data_export"]'
                ),
                UserRole(
                    name='security_admin',
                    display_name='安全管理员',
                    description='安全管理员，负责访问审核和安全监控',
                    permissions='["visit_approval", "security_monitoring", "emergency_contact"]'
                ),
                UserRole(
                    name='alumni_admin',
                    display_name='校友管理员',
                    description='校友管理员，负责校友服务和管理',
                    permissions='["alumni_management", "event_management", "data_export"]'
                ),
                UserRole(
                    name='teacher',
                    display_name='教师',
                    description='教师用户',
                    permissions='["class_management", "student_communication"]'
                ),
                UserRole(
                    name='alumni',
                    display_name='校友',
                    description='校友用户',
                    permissions='["profile_management", "visit_application", "event_registration"]'
                )
            ]

            for role in roles:
                db.session.add(role)

            db.session.commit()

        print("数据库迁移完成！")

        # 显示迁移结果
        print("\n=== 迁移结果统计 ===")
        print(f"总用户数: {User.query.count()}")
        print(f"组织总数: {Organization.query.count()}")
        print(f"角色总数: {UserRole.query.count()}")

        print("\n=== 用户组织分配情况 ===")
        for org_type in ['school', 'college', 'department', 'office', 'class']:
            orgs = Organization.query.filter_by(org_type=org_type).all()
            for org in orgs:
                user_count = User.query.filter_by(organization_id=org.id).count()
                if user_count > 0:
                    print(f"{org.name} ({org.org_type}): {user_count} 个用户")

        print("\n=== 教师用户信息 ===")
        teachers = User.query.filter_by(user_type='teacher').all()
        for teacher in teachers:
            org_name = teacher.organization.name if teacher.organization else "未分配"
            print(f"教师: {teacher.real_name} ({teacher.username}) - 组织: {org_name}, 工号: {teacher.employee_id}, UUID: {teacher.uuid}")

if __name__ == '__main__':
    try:
        migrate_database()
        print("\n[SUCCESS] 数据库迁移成功完成！")
    except Exception as e:
        print(f"\n[ERROR] 数据库迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)