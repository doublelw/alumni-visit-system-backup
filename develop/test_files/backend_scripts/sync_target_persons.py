#!/usr/bin/env python
"""
同步TargetPerson表和User表的数据
确保教师用户在target_persons表中有对应的记录
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.target_person import TargetPerson
from app.models.user import User
from app.models.organization import Organization

def sync_target_persons_with_users():
    """同步TargetPerson表和User表的数据"""

    app = create_app()
    with app.app_context():
        print("开始同步TargetPerson表和User表的数据...")

        # 获取所有教师用户
        teachers = User.query.filter_by(user_type='teacher', status='active').all()
        print(f"找到 {len(teachers)} 个教师用户")

        # 创建一个映射，记录哪些work_id已经被处理
        existing_work_ids = set()
        updated_count = 0
        created_count = 0

        # 处理每个教师用户
        for teacher in teachers:
            # 使用employee_id作为work_id
            work_id = teacher.employee_id
            if not work_id:
                print(f"跳过没有employee_id的教师: {teacher.real_name}")
                continue

            # 检查是否已存在该work_id的记录
            existing_person = TargetPerson.query.filter_by(work_id=work_id).first()

            # 获取组织信息作为部门
            department = "未知部门"
            if teacher.organization:
                if teacher.organization.org_type == 'class':
                    # 如果组织是班级，获取其父组织信息
                    grad_year = Organization.query.get(teacher.organization.parent_id)
                    if grad_year:
                        department = f"{grad_year.name} {teacher.organization.name}"
                elif teacher.organization.org_type == 'office':
                    department = teacher.organization.name
                elif teacher.organization.org_type == 'campus':
                    department = f"{teacher.organization.name}教职工"
                else:
                    department = teacher.organization.name

            person_data = {
                'work_id': work_id,
                'name': teacher.real_name,
                'department': department,
                'position': '教师',
                'email': teacher.email,
                'phone': teacher.phone,
                'is_active': True
            }

            if existing_person:
                # 更新现有记录
                existing_person.name = person_data['name']
                existing_person.department = person_data['department']
                existing_person.position = person_data['position']
                existing_person.email = person_data['email']
                existing_person.phone = person_data['phone']
                existing_person.is_active = person_data['is_active']
                updated_count += 1
                print(f"更新: {work_id} - {teacher.real_name}")
            else:
                # 创建新记录
                new_person = TargetPerson(**person_data)
                db.session.add(new_person)
                created_count += 1
                print(f"创建: {work_id} - {teacher.real_name}")

            existing_work_ids.add(work_id)

        # 检查是否需要停用一些target_persons记录（对应的用户已不存在）
        all_target_persons = TargetPerson.query.filter_by(is_active=True).all()
        deactivated_count = 0

        for tp in all_target_persons:
            # 检查这个work_id是否在用户表中存在且是活跃的教师
            corresponding_user = User.query.filter_by(
                employee_id=tp.work_id,
                user_type='teacher',
                status='active'
            ).first()

            if not corresponding_user:
                # 停用这个target_person记录
                tp.is_active = False
                deactivated_count += 1
                print(f"停用: {tp.work_id} - {tp.name} (对应的用户不存在或非活跃教师)")

        try:
            db.session.commit()
            print(f"\n=== 同步完成 ===")
            print(f"创建新记录: {created_count}")
            print(f"更新现有记录: {updated_count}")
            print(f"停用记录: {deactivated_count}")

            # 显示最终统计
            active_count = TargetPerson.query.filter_by(is_active=True).count()
            total_count = TargetPerson.query.count()
            print(f"TargetPerson表统计: 活跃 {active_count}/{total_count}")

        except Exception as e:
            db.session.rollback()
            print(f"\n同步失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return

def show_current_status():
    """显示当前状态"""

    app = create_app()
    with app.app_context():
        print("=== 当前状态 ===")

        # 统计用户表中的教师
        teachers = User.query.filter_by(user_type='teacher').all()
        active_teachers = [t for t in teachers if t.status == 'active']
        print(f"用户表 - 教师总数: {len(teachers)}, 活跃: {len(active_teachers)}")

        # 统计TargetPerson表
        all_target_persons = TargetPerson.query.all()
        active_target_persons = [tp for tp in all_target_persons if tp.is_active]
        print(f"TargetPerson表 - 总数: {len(all_target_persons)}, 活跃: {len(active_target_persons)}")

        # 找出不匹配的记录
        teacher_work_ids = {t.employee_id for t in active_teachers if t.employee_id}
        target_person_work_ids = {tp.work_id for tp in active_target_persons}

        missing_in_target = teacher_work_ids - target_person_work_ids
        extra_in_target = target_person_work_ids - teacher_work_ids

        if missing_in_target:
            print(f"\n用户表中有但TargetPerson表中缺失的work_id: {len(missing_in_target)}")
            for work_id in sorted(missing_in_target):
                teacher = next((t for t in active_teachers if t.employee_id == work_id), None)
                if teacher:
                    print(f"  {work_id}: {teacher.real_name}")

        if extra_in_target:
            print(f"\nTargetPerson表中多余或用户表缺失的work_id: {len(extra_in_target)}")
            for work_id in sorted(extra_in_target):
                tp = next((tp for tp in active_target_persons if tp.work_id == work_id), None)
                if tp:
                    print(f"  {work_id}: {tp.name}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        show_current_status()
    else:
        sync_target_persons_with_users()
        print("\n" + "="*50)
        show_current_status()