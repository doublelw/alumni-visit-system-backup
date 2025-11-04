#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空所有申请记录
"""

import sys, os
sys.path.append('backend')
from app import create_app, db
from app.models.visit_application import VisitApplication
from app.models.student_exit_application import StudentExitApplication

app = create_app('development')
with app.app_context():
    print("=== 清空所有申请记录 ===")

    # 1. 删除所有访问申请
    visit_applications = VisitApplication.query.all()
    print(f"找到 {len(visit_applications)} 个访问申请")
    for app_data in visit_applications:
        db.session.delete(app_data)
    print(f"已删除 {len(visit_applications)} 个访问申请")

    # 2. 删除所有学生出校申请
    exit_applications = StudentExitApplication.query.all()
    print(f"找到 {len(exit_applications)} 个学生出校申请")
    for app_data in exit_applications:
        db.session.delete(app_data)
    print(f"已删除 {len(exit_applications)} 个学生出校申请")

    # 提交删除操作
    db.session.commit()

    # 验证清理结果
    visit_count = VisitApplication.query.count()
    exit_count = StudentExitApplication.query.count()

    print(f"\n=== 清理结果验证 ===")
    print(f"访问申请剩余数量: {visit_count}")
    print(f"学生出校申请剩余数量: {exit_count}")

    if visit_count == 0 and exit_count == 0:
        print("\n✅ 所有申请记录已成功清空！")
        print("现在可以重新开始测试，提交新的申请记录。")
    else:
        print("\n❌ 清理失败，请检查数据库连接")