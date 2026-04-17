#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信审批同步守护进程

每60秒运行一次同步脚本，持续监控微信云数据库

使用方法:
    python scripts/sync_daemon.py

环境变量:
    SYNC_INTERVAL - 同步间隔（秒），默认60秒

示例:
    # 后台运行（Linux/Mac）
    nohup python scripts/sync_daemon.py &

    # 后台运行（Windows）
    start /B python scripts\sync_daemon.py
"""

import time
import subprocess
import logging
import os
import signal
import sys
from datetime import datetime

# 配置日志
log_file = os.path.join(os.path.dirname(__file__), 'sync_daemon.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 同步间隔（秒）
SYNC_INTERVAL = int(os.environ.get('SYNC_INTERVAL', '60'))

# 全局标志
running = True


def signal_handler(signum, frame):
    """信号处理器"""
    global running
    logger.info(f"收到信号 {signum}，准备退出...")
    running = False


def run_sync():
    """运行同步脚本"""
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'sync_wechat_approvals.py')

        logger.info("开始执行同步任务")

        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30  # 30秒超时
        )

        if result.returncode == 0:
            logger.info("✅ 同步任务执行成功")
            if result.stdout:
                logger.debug(f"输出: {result.stdout}")
        else:
            logger.error(f"❌ 同步任务执行失败 (返回码: {result.returncode})")
            if result.stderr:
                logger.error(f"错误: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("❌ 同步任务执行超时（>30秒）")
    except Exception as e:
        logger.error(f"❌ 同步任务异常: {str(e)}")


def main():
    """主循环"""
    global running

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    logger.info("微信审批同步守护进程启动")
    logger.info(f"同步间隔: {SYNC_INTERVAL} 秒")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    logger.info("按 Ctrl+C 停止守护进程")
    logger.info("")

    # 立即执行一次同步
    run_sync()

    # 主循环
    loop_count = 0
    while running:
        try:
            loop_count += 1
            logger.info(f"--- 第 {loop_count} 轮循环，等待 {SYNC_INTERVAL} 秒 ---")

            # 等待指定时间
            for i in range(SYNC_INTERVAL):
                if not running:
                    break
                time.sleep(1)

            # 检查是否继续运行
            if not running:
                break

            # 执行同步
            run_sync()

        except KeyboardInterrupt:
            logger.info("\n收到键盘中断，退出")
            break
        except Exception as e:
            logger.error(f"主循环异常: {str(e)}")
            logger.info("等待60秒后继续...")
            time.sleep(60)

    logger.info("")
    logger.info("=" * 60)
    logger.info("微信审批同步守护进程已停止")
    logger.info(f"停止时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"总共执行: {loop_count} 轮")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
