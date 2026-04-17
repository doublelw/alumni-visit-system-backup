#!/usr/bin/env python
"""
高中模式组织架构迁移脚本
调整组织架构为：学校->校区->毕业年->班级
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy import text
from app import create_app, db
from app.models.organization import Organization, UserRole, UserRoleAssignment
from app.models.user import User

def create_high_school_organizations():
    """创建高中模式组织架构"""

    # 检查是否已存在学校
    school = Organization.query.filter_by(code='SCHOOL_HIGH').first()
    if school:
        print("高中组织架构已存在，跳过基础结构创建...")
        return {
            'school': school.id,
            'campuses': {},
            'total_orgs': Organization.query.count()
        }

    # 创建根级组织 - 学校
    school = Organization(
        name='示范高级中学',
        code='SCHOOL_HIGH',
        description='示范高级中学主校区',
        org_type='school',
        level=1,
        path='/1',
        status='active',
        sort_order=1
    )
    db.session.add(school)
    db.session.flush()

    # 创建校区
    campuses = [
        {
            'name': '主校区',
            'code': 'MAIN_CAMPUS',
            'description': '示范高级中学主校区',
            'sort_order': 1
        },
        {
            'name': '东校区',
            'code': 'EAST_CAMPUS',
            'description': '示范高级中学东校区',
            'sort_order': 2
        },
        {
            'name': '南校区',
            'code': 'SOUTH_CAMPUS',
            'description': '示范高级中学南校区',
            'sort_order': 3
        }
    ]

    campus_ids = {}
    for campus_data in campuses:
        campus = Organization(
            name=campus_data['name'],
            code=campus_data['code'],
            description=campus_data['description'],
            parent_id=school.id,
            level=2,
            path=f'/{school.id}',  # 临时路径，后面会更新
            org_type='campus',
            status='active',
            sort_order=campus_data['sort_order']
        )
        db.session.add(campus)
        db.session.flush()
        # 更新路径
        campus.path = f'/{school.id}/{campus.id}'
        db.session.commit()
        campus_ids[campus_data['code']] = campus.id

    # 创建毕业年份（从2010年到2025年）
    graduation_years = []
    current_year = datetime.now().year
    for year in range(2010, current_year + 1):
        for campus_code, campus_id in campus_ids.items():
            grad_year = Organization(
                name=f'{year}届',
                code=f'GRAD_{year}_{campus_code.upper()}',
                description=f'{year}届毕业生',
                parent_id=campus_id,
                level=3,
                path=f'/{school.id}/{campus_id}',  # 临时路径
                org_type='graduation_year',
                status='active',
                sort_order=current_year - year  # 最近年份排在前面
            )
            db.session.add(grad_year)
            graduation_years.append(grad_year)

    db.session.flush()

    # 更新毕业年份路径
    for grad_year in graduation_years:
        grad_year.path = f'/{school.id}/{grad_year.parent_id}/{grad_year.id}'
    db.session.commit()

    # 创建班级（每个毕业年份创建若干班级）
    for i, grad_year in enumerate(graduation_years):
        year = grad_year.name.replace('届', '')
        campus_code = grad_year.code.split('_')[-1]

        # 为每个毕业年份创建班级
        classes = [
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

        for class_data in classes:
            class_org = Organization(
                name=class_data['name'],
                code=class_data['code'],
                description=class_data['description'],
                parent_id=grad_year.id,
                level=4,
                path=grad_year.path,  # 临时路径
                org_type='class',
                status='active',
                sort_order=int(class_data['code'].split('_')[-2]) if class_data['code'].split('_')[-2].isdigit() else 99
            )
            db.session.add(class_org)

    # 更新班级路径
    all_classes = Organization.query.filter_by(org_type='class').all()
    for class_org in all_classes:
        parent = Organization.query.get(class_org.parent_id)
        if parent:
            class_org.path = f'{parent.path}/{class_org.id}'
    db.session.commit()

    # 创建行政部门
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
            path=f'/{school.id}/{dept.id}',
            org_type='office',
            status='active',
            sort_order=len(admin_departments) + 10
        )
        db.session.add(dept)

    db.session.commit()

    return {
        'school': school.id,
        'campuses': campus_ids,
        'total_orgs': Organization.query.count()
    }

def create_club_organizations():
    """创建社团组织"""

    print("创建社团组织...")

    # 获取学校组织
    school = Organization.query.filter_by(code='SCHOOL_HIGH').first()
    if not school:
        print("未找到学校组织，跳过社团创建")
        return

    # 社团类别
    club_categories = {
        'academic': ['学术类', [
            {'name': '数学社', 'code': 'CLUB_MATH'},
            {'name': '物理社', 'code': 'CLUB_PHYSICS'},
            {'name': '化学社', 'code': 'CLUB_CHEMISTRY'},
            {'name': '生物社', 'code': 'CLUB_BIOLOGY'},
            {'name': '文学社', 'code': 'CLUB_LITERATURE'},
            {'name': '英语社', 'code': 'CLUB_ENGLISH'}
        ]],
        'sports': ['体育类', [
            {'name': '篮球社', 'code': 'CLUB_BASKETBALL'},
            {'name': '足球社', 'code': 'CLUB_FOOTBALL'},
            {'name': '羽毛球社', 'code': 'CLUB_BADMINTON'},
            {'name': '乒乓球社', 'code': 'CLUB_TABLE_TENNIS'},
            {'name': '田径社', 'code': 'CLUB_TRACK_FIELD'},
            {'name': '游泳社', 'code': 'CLUB_SWIMMING'}
        ]],
        'arts': ['艺术类', [
            {'name': '音乐社', 'code': 'CLUB_MUSIC'},
            {'name': '美术社', 'code': 'CLUB_ART'},
            {'name': '舞蹈社', 'code': 'CLUB_DANCE'},
            {'name': '戏剧社', 'code': 'CLUB_DRAMA'},
            {'name': '摄影社', 'code': 'CLUB_PHOTOGRAPHY'},
            {'name': '书法社', 'code': 'CLUB_CALLIGRAPHY'}
        ]],
        'technology': ['科技类', [
            {'name': '计算机社', 'code': 'CLUB_COMPUTER'},
            {'name': '机器人社', 'code': 'CLUB_ROBOTICS'},
            {'name': '航模社', 'code': 'CLUB_AEROMODEL'},
            {'name': '科学社', 'code': 'CLUB_SCIENCE'}
        ]],
        'volunteer': ['志愿类', [
            {'name': '志愿者协会', 'code': 'CLUB_VOLUNTEER'},
            {'name': '环保社', 'code': 'CLUB_ENVIRONMENT'},
            {'name': '爱心社', 'code': 'CLUB_CHARITY'}
        ]],
        'culture': ['文化类', [
            {'name': '汉服社', 'code': 'CLUB_HANFU'},
            {'name': '古诗词社', 'code': 'CLUB_POETRY'},
            {'name': '棋社', 'code': 'CLUB_CHESS'}
        ]]
    }

    # 创建社团类别组织
    club_category_orgs = {}
    for category_key, (category_name, _) in club_categories.items():
        category_org = Organization(
            name=category_name,
            code=f'CLUB_CATEGORY_{category_key.upper()}',
            description=f'{category_name}社团',
            parent_id=school.id,
            level=2,
            path=f'/{school.id}/{dept.id}',
            org_type='club_category',
            status='active',
            sort_order=100
        )
        db.session.add(category_org)
        db.session.flush()
        club_category_orgs[category_key] = category_org.id

    # 创建具体社团
    current_year = datetime.now().year
    for category_key, (category_name, clubs) in club_categories.items():
        category_id = club_category_orgs[category_key]

        for club_data in clubs:
            # 为每个社团创建不同年份的分社
            for year in range(current_year - 10, current_year + 1):
                club = Organization(
                    name=f'{club_data["name"]} ({year}年)',
                    code=f'{club_data["code"]}_{year}',
                    description=f'{club_data["name"]} {year}年分社',
                    parent_id=category_id,
                    level=3,
                    path=f'/{school.id}/{category_id}/{club_data["code"]}_{year}',
                    org_type='club',
                    status='active',
                    sort_order=current_year - year
                )
                db.session.add(club)

    db.session.commit()

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

    for user in users:
        if user.user_type == 'alumni':
            # 校友分配到对应的毕业年份和班级
            # 根据用户名推测毕业年份
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

    db.session.commit()

def migrate_to_high_school():
    """执行高中模式迁移"""

    app = create_app()
    with app.app_context():
        print("开始高中模式组织架构迁移...")

        try:
            # 创建高中模式组织架构
            result = create_high_school_organizations()
            print(f"✅ 创建了 {result['total_orgs']} 个组织")

            # 创建社团组织
            create_club_organizations()
            print("✅ 创建了社团组织架构")

            # 更新现有用户的组织归属
            update_existing_users()
            print("✅ 更新了用户组织归属")

            # 显示统计信息
            total_orgs = Organization.query.count()
            schools = Organization.query.filter_by(org_type='school').count()
            campuses = Organization.query.filter_by(org_type='campus').count()
            grad_years = Organization.query.filter_by(org_type='graduation_year').count()
            classes = Organization.query.filter_by(org_type='class').count()
            clubs = Organization.query.filter_by(org_type='club').count()
            offices = Organization.query.filter_by(org_type='office').count()

            print(f"\n=== 迁移完成统计 ===")
            print(f"总组织数: {total_orgs}")
            print(f"学校: {schools}")
            print(f"校区: {campuses}")
            print(f"毕业年份: {grad_years}")
            print(f"班级: {classes}")
            print(f"社团: {clubs}")
            print(f"办公室: {offices}")

            print(f"\n=== 组织架构 ===")
            print("学校 -> 校区 -> 毕业年份 -> 班级")
            print("社团: 按类别管理，支持不同年份分社")

            print("\n[SUCCESS] 高中模式组织架构迁移完成！")

        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    try:
        migrate_to_high_school()
    except Exception as e:
        print(f"\n[FATAL] 迁移脚本执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)