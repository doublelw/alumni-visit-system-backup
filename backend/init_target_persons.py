#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化拜访对象测试数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app import db

def init_target_persons():
    """初始化拜访对象测试数据"""
    app = create_app()

    with app.app_context():
        try:
            # 导入模型
            from app.models.target_person import TargetPerson

            # 检查是否已存在测试数据
            existing_count = TargetPerson.query.count()
            if existing_count >= 10:
                print(f"测试数据已存在（{existing_count}条），跳过初始化")
                return

            # 插入测试数据
            test_data = [
                {
                    'work_id': 'EMP001',
                    'name': '张伟',
                    'department': '计算机科学与技术学院',
                    'position': '教授',
                    'email': 'zhangwei@university.edu.cn',
                    'phone': '13800138001'
                },
                {
                    'work_id': 'EMP002',
                    'name': '李娜',
                    'department': '软件学院',
                    'position': '副教授',
                    'email': 'lina@university.edu.cn',
                    'phone': '13800138002'
                },
                {
                    'work_id': 'EMP003',
                    'name': '王强',
                    'department': '信息工程学院',
                    'position': '讲师',
                    'email': 'wangqiang@university.edu.cn',
                    'phone': '13800138003'
                },
                {
                    'work_id': 'EMP004',
                    'name': '刘芳',
                    'department': '数学学院',
                    'position': '教授',
                    'email': 'liufang@university.edu.cn',
                    'phone': '13800138004'
                },
                {
                    'work_id': 'EMP005',
                    'name': '陈明',
                    'department': '物理学院',
                    'position': '副教授',
                    'email': 'chenming@university.edu.cn',
                    'phone': '13800138005'
                }
            ]

            for data in test_data:
                person = TargetPerson(**data)
                db.session.add(person)

            db.session.commit()
            print(f"成功创建 {len(test_data)} 条拜访对象测试数据")

        except Exception as e:
            db.session.rollback()
            print(f"创建测试数据失败: {e}")

if __name__ == '__main__':
    init_target_persons()