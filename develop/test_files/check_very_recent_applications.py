#!/usr/bin/env python3
"""
检查最近几分钟内提交的申请
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.student_exit_application import StudentExitApplication
from app.models.user import User
from datetime import datetime, timedelta

def check_very_recent_applications():
    app = create_app()
    with app.app_context():
        # 获取当前时间
        now = datetime.now()

        # 检查最近5分钟内的申请
        five_minutes_ago = now - timedelta(minutes=5)
        very_recent_apps = StudentExitApplication.query.filter(
            StudentExitApplication.created_at >= five_minutes_ago
        ).order_by(StudentExitApplication.created_at.desc()).all()

        print(f'当前时间: {now}')
        print(f'最近5分钟内的申请: {len(very_recent_apps)} 个')

        for app in very_recent_apps:
            time_diff = now - app.created_at
            print(f'- 申请ID: {app.id}')
            print(f'  创建时间: {app.created_at}')
            print(f'  距离现在: {time_diff.total_seconds():.1f} 秒')
            print(f'  出校原因: {app.exit_reason}')
            print(f'  状态: {app.application_status}')
            print('---')

        # 检查最近30分钟内的申请
        thirty_minutes_ago = now - timedelta(minutes=30)
        recent_apps = StudentExitApplication.query.filter(
            StudentExitApplication.created_at >= thirty_minutes_ago
        ).order_by(StudentExitApplication.created_at.desc()).all()

        print(f'\n最近30分钟内的申请: {len(recent_apps)} 个')
        for app in recent_apps:
            time_diff = now - app.created_at
            print(f'- {app.exit_reason} (提交时间: {app.created_at.strftime("%H:%M:%S")}, 距离现在: {time_diff.total_seconds():.0f}秒)')

        # 检查所有申请，按时间排序
        all_apps = StudentExitApplication.query.order_by(StudentExitApplication.created_at.desc()).all()
        print(f'\n数据库中所有申请 (共{len(all_apps)}个):')
        for i, app in enumerate(all_apps, 1):
            time_diff = now - app.created_at
            print(f'{i}. ID:{app.id} - {app.exit_reason} - {app.created_at.strftime("%m-%d %H:%M:%S")} ({time_diff.total_seconds():.0f}秒前)')

if __name__ == '__main__':
    check_very_recent_applications()