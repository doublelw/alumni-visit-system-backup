#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunicorn生产环境配置文件
"""

import multiprocessing
import os
import sys

# 添加项目路径到Python路径
project_root = "/var/www/lsalumni"
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    sys.path.insert(0, os.path.join(project_root, "backend"))

# 设置工作目录
os.chdir(project_root)

# 服务器socket
bind = "127.0.0.1:5000"
backlog = 2048
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 重启
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 日志
accesslog = "/var/log/lsalumni/access.log"
errorlog = "/var/log/lsalumni/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "lsalumni"

# 安全
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL（如需要）
# keyfile = "/path/to/ssl/keyfile.key"
# certfile = "/path/to/ssl/certfile.crt"