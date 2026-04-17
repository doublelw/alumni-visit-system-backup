#!/usr/bin/env python3
"""
设置教师用户为可拜访对象
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User

def set_teachers_visitable():
    """设置所有活跃教师为可拜访对象"""

    app = create_app()
    with app.app_context():
        print("正在设置教师用户为可拜访对象...")

        # 获取所有活跃的教师
        teachers = User.query.filter_by(
            user_type='teacher',
            status='active'
        ).all()

        updated_count = 0
        for teacher in teachers:
            if not teacher.is_visitable:
                teacher.is_visitable = True
                updated_count += 1
                print(f"设置教师: {teacher.real_name} ({teacher.employee_id}) 为可拜访对象")

        try:
            db.session.commit()
            print(f"\n完成！共更新了 {updated_count} 个教师用户")
            print(f"现在有 {len(teachers)} 个教师用户可作为拜访对象")

        except Exception as e:
            db.session.rollback()
            print(f"更新失败: {str(e)}")
            return

if __name__ == '__main__':
    set_teachers_visitable()