#!/usr/bin/env python
"""
完善高中组织架构 - 创建缺失的班级、社团和办公室
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy import text
from app import create_app, db
from app.models.organization import Organization, UserRole, UserRoleAssignment
from app.models.user import User

def create_missing_classes():
    """创建缺失的班级"""

    print("创建班级...")

    # 获取学校
    school = Organization.query.filter_by(code='SCHOOL_HIGH').first()
    if not school:
        print("未找到学校组织")
        return

    # 获取所有毕业年份
    grad_years = Organization.query.filter_by(org_type='graduation_year').all()
    print(f"找到 {len(grad_years)} 个毕业年份")

    classes_created = 0
    for grad_year in grad_years:
        # 检查是否已有班级
        existing_classes = Organization.query.filter_by(parent_id=grad_year.id, org_type='class').count()
        if existing_classes > 0:
            print(f"毕业年份 {grad_year.name} 已有 {existing_classes} 个班级，跳过")
            continue

        year = grad_year.name.replace('届', '')
        campus_code = grad_year.code.split('_')[-1] if '_' in grad_year.code else 'MAIN_CAMPUS'

        # 创建班级
        class_list = [
            {
                'name': f'{year}届1班',
                'code': f'CLASS_{year}_1_{campus_code}',
                'description': f'{year}届1班'
            },
            {
                'name': f'{year}届2班',
                'code': f'CLASS_{year}_2_{campus_code}',
                'description': f'{year}届2班'
            },
            {
                'name': f'{year}届3班',
                'code': f'CLASS_{year}_3_{campus_code}',
                'description': f'{year}届3班'
            },
            {
                'name': f'{year}届4班',
                'code': f'CLASS_{year}_4_{campus_code}',
                'description': f'{year}届4班'
            },
            {
                'name': f'{year}届重点班',
                'code': f'CLASS_{year}_HONOR_{campus_code}',
                'description': f'{year}届重点班'
            },
            {
                'name': f'{year}届实验班',
                'code': f'CLASS_{year}_EXPERIMENT_{campus_code}',
                'description': f'{year}届实验班'
            }
        ]

        for class_data in class_list:
            class_org = Organization(
                name=class_data['name'],
                code=class_data['code'],
                description=class_data['description'],
                parent_id=grad_year.id,
                level=4,
                path=f'{grad_year.path}',  # 临时路径
                org_type='class',
                status='active',
                sort_order=int(class_data['code'].split('_')[-2]) if class_data['code'].split('_')[-2].isdigit() else 99
            )
            db.session.add(class_org)
            classes_created += 1

    db.session.flush()

    # 更新班级路径
    all_classes = Organization.query.filter_by(org_type='class').all()
    for class_org in all_classes:
        parent = Organization.query.get(class_org.parent_id)
        if parent:
            class_org.path = f'{parent.path}/{class_org.id}'

    db.session.commit()
    print(f"创建了 {classes_created} 个班级")

def create_missing_offices():
    """创建缺失的办公室"""

    print("创建行政部门...")

    # 获取学校
    school = Organization.query.filter_by(code='SCHOOL_HIGH').first()
    if not school:
        print("未找到学校组织")
        return

    # 检查是否已有办公室
    existing_offices = Organization.query.filter_by(org_type='office').count()
    if existing_offices > 0:
        print(f"已有 {existing_offices} 个办公室，跳过")
        return

    admin_departments = [
        {
            'name': '校长办公室',
            'code': 'OFFICE_PRINCIPAL',
            'description': '校长办公室'
        },
        {
            'name': '教务处',
            'code': 'OFFICE_ACADEMIC',
            'description': '教务处'
        },
        {
            'name': '学生处',
            'code': 'OFFICE_STUDENT',
            'description': '学生处'
        },
        {
            'name': '保卫处',
            'code': 'OFFICE_SECURITY',
            'description': '保卫处'
        },
        {
            'name': '校友办公室',
            'code': 'OFFICE_ALUMNI',
            'description': '校友办公室'
        }
    ]

    for dept_data in admin_departments:
        dept = Organization(
            name=dept_data['name'],
            code=dept_data['code'],
            description=dept_data['description'],
            parent_id=school.id,
            level=2,
            path=f'/{school.id}',  # 临时路径
            org_type='office',
            status='active',
            sort_order=len(admin_departments) + 10
        )
        db.session.add(dept)

    db.session.flush()

    # 更新办公室路径
    all_offices = Organization.query.filter_by(org_type='office').all()
    for office in all_offices:
        office.path = f'/{school.id}/{office.id}'

    db.session.commit()
    print(f"创建了 {len(admin_departments)} 个办公室")

def create_simple_clubs():
    """创建简单的社团结构"""

    print("创建社团...")

    # 获取学校
    school = Organization.query.filter_by(code='SCHOOL_HIGH').first()
    if not school:
        print("未找到学校组织")
        return

    # 检查是否已有社团
    existing_clubs = Organization.query.filter_by(org_type='club').count()
    if existing_clubs > 0:
        print(f"已有 {existing_clubs} 个社团，跳过")
        return

    # 简单的社团列表
    clubs = [
        {
            'name': '篮球社',
            'code': 'CLUB_BASKETBALL',
            'description': '篮球社'
        },
        {
            'name': '文学社',
            'code': 'CLUB_LITERATURE',
            'description': '文学社'
        },
        {
            'name': '音乐社',
            'code': 'CLUB_MUSIC',
            'description': '音乐社'
        },
        {
            'name': '美术社',
            'code': 'CLUB_ART',
            'description': '美术社'
        },
        {
            'name': '计算机社',
            'code': 'CLUB_COMPUTER',
            'description': '计算机社'
        },
        {
            'name': '志愿者协会',
            'code': 'CLUB_VOLUNTEER',
            'description': '志愿者协会'
        }
    ]

    for club_data in clubs:
        club = Organization(
            name=club_data['name'],
            code=club_data['code'],
            description=club_data['description'],
            parent_id=school.id,
            level=2,
            path=f'/{school.id}',  # 临时路径
            org_type='club',
            status='active',
            sort_order=200
        )
        db.session.add(club)

    db.session.flush()

    # 更新社团路径
    all_clubs = Organization.query.filter_by(org_type='club').all()
    for club in all_clubs:
        club.path = f'/{school.id}/{club.id}'

    db.session.commit()
    print(f"创建了 {len(clubs)} 个社团")

def update_existing_users():
    """更新现有用户的组织归属"""

    print("更新用户组织归属...")

    users = User.query.all()
    current_year = datetime.now().year

    # 获取相关组织
    main_campus = Organization.query.filter_by(code='MAIN_CAMPUS').first()
    security_office = Organization.query.filter_by(code='OFFICE_SECURITY').first()
    alumni_office = Organization.query.filter_by(code='OFFICE_ALUMNI').first()
    principal_office = Organization.query.filter_by(code='OFFICE_PRINCIPAL').first()

    if not main_campus:
        print("未找到主校区，跳过用户更新")
        return

    updated_users = 0
    for user in users:
        if user.organization_id is None:
            if user.user_type == 'alumni':
                # 校友分配到对应的毕业年份
                graduation_year = None
                if '2020' in user.username:
                    graduation_year = 2020
                elif '2021' in user.username:
                    graduation_year = 2021
                elif '2022' in user.username:
                    graduation_year = 2022
                elif '2023' in user.username:
                    graduation_year = 2023
                elif '2024' in user.username:
                    graduation_year = 2024
                else:
                    graduation_year = current_year - 1  # 默认去年毕业

                # 查找对应的毕业年组织
                grad_year = Organization.query.filter_by(
                    name=f'{graduation_year}届',
                    parent_id=main_campus.id,
                    org_type='graduation_year'
                ).first()

                if grad_year:
                    # 查找对应的班级（默认分配到1班）
                    target_class = Organization.query.filter_by(
                        parent_id=grad_year.id,
                        org_type='class'
                    ).order_by(Organization.sort_order).first()

                    if target_class:
                        user.organization_id = target_class.id
                    else:
                        user.organization_id = grad_year.id
                else:
                    user.organization_id = main_campus.id

            elif user.user_type == 'teacher':
                # 教师分配到主校区
                user.organization_id = main_campus.id

            elif user.user_type == 'admin':
                # 管理员分配到校长办公室
                if principal_office:
                    user.organization_id = principal_office.id
                else:
                    user.organization_id = main_campus.id

            elif user.user_type == 'security':
                # 保安分配到保卫处
                if security_office:
                    user.organization_id = security_office.id
                else:
                    user.organization_id = main_campus.id

            updated_users += 1

    db.session.commit()
    print(f"更新了 {updated_users} 个用户的组织归属")

def complete_organization_structure():
    """完善组织架构"""

    app = create_app()
    with app.app_context():
        print("开始完善高中组织架构...")

        try:
            # 创建缺失的班级
            create_missing_classes()

            # 创建缺失的办公室
            create_missing_offices()

            # 创建简单的社团结构
            create_simple_clubs()

            # 更新现有用户的组织归属
            update_existing_users()

            # 显示统计信息
            total_orgs = Organization.query.count()
            schools = Organization.query.filter_by(org_type='school').count()
            campuses = Organization.query.filter_by(org_type='campus').count()
            grad_years = Organization.query.filter_by(org_type='graduation_year').count()
            classes = Organization.query.filter_by(org_type='class').count()
            clubs = Organization.query.filter_by(org_type='club').count()
            offices = Organization.query.filter_by(org_type='office').count()

            print(f"\n=== 完成后的统计 ===")
            print(f"总组织数: {total_orgs}")
            print(f"学校: {schools}")
            print(f"校区: {campuses}")
            print(f"毕业年份: {grad_years}")
            print(f"班级: {classes}")
            print(f"社团: {clubs}")
            print(f"办公室: {offices}")

            print(f"\n=== 组织架构 ===")
            print("学校 -> 校区 -> 毕业年份 -> 班级")
            print("行政部门: 校长办公室、教务处、学生处、保卫处、校友办公室")
            print("社团: 篮球社、文学社、音乐社、美术社、计算机社、志愿者协会")

            print("\n[SUCCESS] 组织架构完善完成！")

        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] 完善失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    try:
        complete_organization_structure()
    except Exception as e:
        print(f"\n[FATAL] 脚本执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)