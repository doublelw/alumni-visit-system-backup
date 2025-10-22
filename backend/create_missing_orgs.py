#!/usr/bin/env python
"""
创建缺失的组织结构 - 简化版本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app import create_app, db
from app.models.organization import Organization
from app.models.user import User

def create_offices_and_clubs():
    """创建办公室和社团"""

    app = create_app()
    with app.app_context():
        with db.session.no_autoflush:
            # 获取学校
            school = Organization.query.filter_by(code='SCHOOL_HIGH').first()
            if not school:
                print("未找到学校组织")
                return

            # 创建办公室
            offices_data = [
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

            for office_data in offices_data:
                existing = Organization.query.filter_by(code=office_data['code']).first()
                if not existing:
                    office = Organization(
                        name=office_data['name'],
                        code=office_data['code'],
                        description=office_data['description'],
                        parent_id=school.id,
                        level=2,
                        path=f'/{school.id}',
                        org_type='office',
                        status='active',
                        sort_order=100
                    )
                    db.session.add(office)
                    print(f"创建办公室: {office_data['name']}")
                else:
                    print(f"办公室已存在: {office_data['name']}")

            # 创建社团
            clubs_data = [
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

            for club_data in clubs_data:
                existing = Organization.query.filter_by(code=club_data['code']).first()
                if not existing:
                    club = Organization(
                        name=club_data['name'],
                        code=club_data['code'],
                        description=club_data['description'],
                        parent_id=school.id,
                        level=2,
                        path=f'/{school.id}',
                        org_type='club',
                        status='active',
                        sort_order=200
                    )
                    db.session.add(club)
                    print(f"创建社团: {club_data['name']}")
                else:
                    print(f"社团已存在: {club_data['name']}")

            try:
                db.session.commit()
                print("成功创建办公室和社团")
            except Exception as e:
                db.session.rollback()
                print(f"创建失败: {e}")
                return

            # 更新路径
            all_new_orgs = Organization.query.filter(
                Organization.path == f'/{school.id}',
                Organization.org_type.in_(['office', 'club'])
            ).all()

            for org in all_new_orgs:
                org.path = f'/{school.id}/{org.id}'

            db.session.commit()
            print("路径更新完成")

def update_user_organizations():
    """更新用户组织归属"""

    app = create_app()
    with app.app_context():
        users = User.query.filter(User.organization_id.is_(None)).all()
        if not users:
            print("所有用户都已有组织归属")
            return

        print(f"需要更新 {len(users)} 个用户的组织归属")

        # 获取组织
        main_campus = Organization.query.filter_by(code='MAIN_CAMPUS').first()
        security_office = Organization.query.filter_by(code='OFFICE_SECURITY').first()
        alumni_office = Organization.query.filter_by(code='OFFICE_ALUMNI').first()
        principal_office = Organization.query.filter_by(code='OFFICE_PRINCIPAL').first()

        if not main_campus:
            print("未找到主校区，无法更新用户组织")
            return

        current_year = datetime.now().year

        for user in users:
            if user.user_type == 'alumni':
                # 校友分配到主校区
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
        print(f"更新了 {len(users)} 个用户的组织归属")

def show_final_stats():
    """显示最终统计"""

    app = create_app()
    with app.app_context():
        total_orgs = Organization.query.count()
        schools = Organization.query.filter_by(org_type='school').count()
        campuses = Organization.query.filter_by(org_type='campus').count()
        grad_years = Organization.query.filter_by(org_type='graduation_year').count()
        classes = Organization.query.filter_by(org_type='class').count()
        clubs = Organization.query.filter_by(org_type='club').count()
        offices = Organization.query.filter_by(org_type='office').count()

        print(f"\n=== 最终统计 ===")
        print(f"总组织数: {total_orgs}")
        print(f"学校: {schools}")
        print(f"校区: {campuses}")
        print(f"毕业年份: {grad_years}")
        print(f"班级: {classes}")
        print(f"社团: {clubs}")
        print(f"办公室: {offices}")

        # 显示用户统计
        users_with_org = User.query.filter(User.organization_id.isnot(None)).count()
        users_total = User.query.count()
        print(f"用户总数: {users_total}")
        print(f"有组织归属的用户: {users_with_org}")

if __name__ == '__main__':
    try:
        print("开始创建缺失的组织结构...")
        create_offices_and_clubs()
        update_user_organizations()
        show_final_stats()
        print("\n[SUCCESS] 组织结构完善完成！")
    except Exception as e:
        print(f"\n[FATAL] 脚本执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)