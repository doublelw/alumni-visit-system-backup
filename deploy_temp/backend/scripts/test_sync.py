#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
同步功能测试脚本

模拟微信云数据库的API，用于测试同步脚本

使用方法:
    python scripts/test_sync.py

这会启动一个简单的HTTP服务器，模拟微信云函数API
然后在另一个终端运行 sync_wechat_approvals.py 进行测试
"""

import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 模拟数据库
MOCK_DATABASE = {
    'approvals': []
}


class MockWechatCloudHandler(BaseHTTPRequestHandler):
    """模拟微信云函数的HTTP处理器"""

    def do_POST(self):
        """处理POST请求"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
            else:
                request_data = {}

            action = request_data.get('action')
            logger.info(f"收到请求: {action}")

        if action == 'create_approval':
            response = self.create_approval(request_data.get('data'))
        elif action == 'get_pending_approvals':
            response = self.get_pending_approvals()
        elif action == 'mark_synced':
            response = self.mark_synced(request_data.get('data'))
        else:
            response = {'success': False, 'error': 'Invalid action'}

        # 返回响应
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def create_approval(self, data):
        """创建审批记录"""
        approval = {
            '_id': f'mock_{int(time.time() * 1000)}',
            'code': data.get('code'),
            'action': data.get('action'),
            'type': data.get('type'),
            'approval_date': data.get('approval_date'),
            'teacher_id': data.get('teacher_id'),
            'teacher_name': data.get('teacher_name'),
            'created_at': datetime.now().isoformat(),
            'synced': False,
            'synced_at': None
        }

        MOCK_DATABASE['approvals'].append(approval)
        logger.info(f"  ✅ 创建审批记录: {approval['code']}")
        return {'success': True, '_id': approval['_id']}

    def get_pending_approvals(self):
        """获取待同步的审批记录"""
        pending = [a for a in MOCK_DATABASE['approvals'] if not a.get('synced', False)]
        logger.info(f"  📋 待同步记录: {len(pending)} 条")
        return {'success': True, 'data': pending}

    def mark_synced(self, data):
        """标记为已同步"""
        ids = data.get('ids', [])
        count = 0

        for approval in MOCK_DATABASE['approvals']:
            if approval.get('_id') in ids:
                approval['synced'] = True
                approval['synced_at'] = datetime.now().isoformat()
                count += 1

        logger.info(f"  ✅ 标记同步: {count} 条")
        return {'success': True}

    def log_message(self, format, *args):
        """禁用默认日志"""
        pass


def start_mock_server(port=8765):
    """启动模拟服务器"""
    server = HTTPServer(('localhost', port), MockWechatCloudHandler)
    logger.info(f"模拟微信云数据库服务器启动在 http://localhost:{port}")
    logger.info("按 Ctrl+C 停止服务器")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
        server.shutdown()


def show_test_commands(port):
    """显示测试命令"""
    print("\n" + "=" * 60)
    print("测试服务器已启动！")
    print("=" * 60)
    print("\n【步骤1】在另一个终端运行同步脚本:")
    print(f"  export WECHAT_CLOUD_FUNCTION_URL=http://localhost:{port}")
    print("  python backend/scripts/sync_wechat_approvals.py")
    print("\n【步骤2】或者运行守护进程:")
    print(f"  export WECHAT_CLOUD_FUNCTION_URL=http://localhost:{port}")
    print("  python backend/scripts/sync_daemon.py")
    print("\n【步骤3】在浏览器中测试API:")
    print(f"  打开 http://localhost:{port}/test")
    print("\n【测试数据】")
    print("  会自动创建测试审批记录，包含:")
    print("  - 审批码: 123456 (家长进校，批准)")
    print("  - 审批码: 654321 (学生请假，批准)")
    print("  - 审批码: 111111 (家长进校，拒绝)")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")


def create_test_approvals():
    """创建测试审批记录"""
    logger.info("创建测试审批记录...")

    test_data = [
        {
            'code': '123456',
            'action': 'approve',
            'type': 'parent-visit',
            'approval_date': '2026-03-28',
            'teacher_id': 1,
            'teacher_name': '王老师'
        },
        {
            'code': '654321',
            'action': 'approve',
            'type': 'student-leave',
            'approval_date': '2026-03-27',
            'teacher_id': 1,
            'teacher_name': '王老师'
        },
        {
            'code': '111111',
            'action': 'reject',
            'type': 'parent-visit',
            'approval_date': None,
            'teacher_id': 1,
            'teacher_name': '王老师'
        }
    ]

    for data in test_data:
        approval = {
            '_id': f"test_{data['code']}",
            'code': data['code'],
            'action': data['action'],
            'type': data['type'],
            'approval_date': data['approval_date'],
            'teacher_id': data['teacher_id'],
            'teacher_name': data['teacher_name'],
            'created_at': datetime.now().isoformat(),
            'synced': False,
            'synced_at': None
        }
        MOCK_DATABASE['approvals'].append(approval)
        logger.info(f"  ✅ 创建测试审批: {data['code']} ({data['action']})")

    logger.info(f"✅ 共创建 {len(test_data)} 条测试记录")


if __name__ == '__main__':
    import sys

    port = 8765
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    # 创建测试数据
    create_test_approvals()

    # 显示测试命令
    show_test_commands(port)

    # 启动服务器
    start_mock_server(port)
