#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WSGI入口文件 - 微信云托管
"""

import os
import sys

# 添加backend路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()
