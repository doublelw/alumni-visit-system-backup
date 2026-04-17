#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
校友入校登记系统 - 启动脚本
使用: python run.py
"""

import os
import sys

# 添加后端路径（获取backend目录，而不是scripts目录）
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    print("="*70)
    print("校友入校登记系统 - 启动中...")
    print("="*70)
    print("\n访问地址:")
    print("  主页: http://localhost:5000/")
    print("  家长端: http://localhost:5000/parent-simple")
    print("  教师端: http://localhost:5000/teacher-wechat")
    print("  管理员: http://localhost:5000/admin")
    print("\n按 Ctrl+C 停止服务器")
    print("="*70 + "\n")

    # 启动Flask开发服务器
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
