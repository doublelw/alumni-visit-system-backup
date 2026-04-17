#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
校友入校登记系统 - 微信云托管启动文件
"""

import os
import sys

# 添加backend路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 微信云托管会自动设置端口
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
