#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理所有数据，只保留admin初始用户
"""

import sys, os
sys.path.append('backend')
from app import create_app, db
from app.models.user import User
from app.models.visit_application import VisitApplication
from app.models.student_exit_application import StudentExitApplication

app = create_app('development')
with app.app_context():
    print("=== 清理所有数据，只保留admin用户 ===")

    # 1. 删除所有访问申请
    visit_applications = VisitApplication.query.all()
    print(f"删除 {len(visit_applications)} 个访问申请...")
    for app in visit_applications:
        db.session.delete(app)

    # 2. 删除所有学生出校申请
    exit_applications = StudentExitApplication.query.all()
    print(f"删除 {len(exit_applications)} 个学生出校申请...")
    for app in exit_applications:
        db.session.delete(app)

    # 3. 删除所有非admin用户
    users = User.query.filter(User.username != 'admin').all()
    print(f"删除 {len(users)} 个用户...")
    for user in users:
        print(f"  - 删除用户: {user.real_name} (用户名: {user.username}, 类型: {user.user_type})")
        db.session.delete(user)

    # 提交所有删除操作
    db.session.commit()

    # 4. 验证最终数据
    print("\n=== 清理后的数据验证 ===")

    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print(f"✅ 保留admin用户: {admin_user.real_name} (ID: {admin_user.id})")
    else:
        print("❌ admin用户不存在")

    remaining_users = User.query.all()
    visit_count = VisitApplication.query.count()
    exit_count = StudentExitApplication.query.count()

    print(f"✅ 剩余用户数量: {len(remaining_users)}")
    print(f"✅ 访问申请数量: {visit_count}")
    print(f"✅ 学生出校申请数量: {exit_count}")

    if len(remaining_users) == 1 and visit_count == 0 and exit_count == 0:
        print("\n🎉 数据清理完成！现在可以导入正式测试数据了")
    else:
        print("\n❌ 数据清理失败，请检查")