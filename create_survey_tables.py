#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建问卷相关数据表
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, os.path.join(project_root, 'backend'))

from backend.app.models import db
from backend.app import create_app

def create_tables():
    """创建问卷相关数据表"""
    app = create_app()

    with app.app_context():
        # 导入问卷模型
        from backend.app.models.survey import Survey, SurveyQuestion, SurveyResponse

        # 创建表
        print("创建问卷相关数据表...")
        db.create_all()

        # 检查表是否创建成功
        inspector = db.inspect(db.engine)

        tables = inspector.get_table_names()
        required_tables = ['surveys', 'survey_questions', 'survey_responses']

        for table in required_tables:
            if table in tables:
                print(f"✅ 表 '{table}' 创建成功")
            else:
                print(f"❌ 表 '{table}' 创建失败")

        print("✅ 问卷相关数据表创建完成")

if __name__ == '__main__':
    create_tables()