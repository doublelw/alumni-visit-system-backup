#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask应用运行入口
用于Gunicorn等WSGI服务器启动
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 开发环境直接运行
    ssl_cert = app.config.get('SSL_CERT')
    ssl_key = app.config.get('SSL_KEY')

    # 强制使用HTTP模式进行开发测试
    ssl_context = None
    print("开发环境：强制使用HTTP模式启动")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', False),
        ssl_context=ssl_context
    )