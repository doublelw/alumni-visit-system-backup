#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信云数据库同步脚本

从微信云数据库拉取审批记录，写入校内数据库
每分钟运行一次（通过cron或Windows任务计划程序）

使用方法:
    python scripts/sync_wechat_approvals.py

环境变量:
    WECHAT_CLOUD_FUNCTION_URL - 微信云函数URL（必须）
"""

import sys
import os
import requests
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.visit_application import VisitApplication

# 配置日志
log_file = os.path.join(os.path.dirname(__file__), 'sync_wechat.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 微信云函数URL（从环境变量读取）
CLOUD_FUNCTION_URL = os.environ.get('WECHAT_CLOUD_FUNCTION_URL', '')


def fetch_pending_approvals():
    """
    从微信云数据库获取待同步的审批记录

    返回:
        list: 审批记录列表
    """
    try:
        logger.info(f"正在连接微信云数据库: {CLOUD_FUNCTION_URL}")

        response = requests.post(
            CLOUD_FUNCTION_URL,
            json={'action': 'get_pending_approvals'},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if data.get('success'):
            approvals = data.get('data', [])
            logger.info(f"成功获取 {len(approvals)} 条待同步记录")
            return approvals
        else:
            logger.error(f"获取审批记录失败: {data.get('error')}")
            return []

    except requests.exceptions.Timeout:
        logger.error("连接微信云数据库超时")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"请求微信云数据库失败: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        return []


def process_approval_in_system(approval_data):
    """
    在校内系统中处理审批

    参数:
        approval_data (dict): 审批数据

    返回:
        bool: 处理是否成功
    """
    try:
        code = approval_data.get('code')
        action = approval_data.get('action')
        approval_type = approval_data.get('type')
        approval_date = approval_data.get('approval_date')
        teacher_id = approval_data.get('teacher_id')
        teacher_name = approval_data.get('teacher_name')
        created_at = approval_data.get('created_at')

        logger.info(f"正在处理审批码: {code}, 操作: {action}, 类型: {approval_type}")

        # 查找对应的申请记录
        application = VisitApplication.query.filter_by(access_code=code).first()

        if not application:
            logger.warning(f"  ⚠ 未找到审批码 {code} 对应的申请记录")
            return False

        if application.status != 'pending':
            logger.warning(f"  ⚠ 审批码 {code} 状态为 {application.status}，跳过")
            return False

        # 更新审批状态
        if action == 'approve':
            application.status = 'approved'
            application.approved_by = teacher_id
            application.approved_at = datetime.now()

            # 设置审批日期
            if approval_date:
                try:
                    approval_datetime = datetime.strptime(approval_date, '%Y-%m-%d')
                    application.approval_date = approval_datetime.date()
                except ValueError:
                    logger.warning(f"  ⚠ 日期格式错误: {approval_date}，使用今天")
                    application.approval_date = datetime.now().date()
            else:
                application.approval_date = datetime.now().date()

            logger.info(f"  ✅ 审批通过: {code}, 类型: {approval_type}, 日期: {application.approval_date}")

        elif action == 'reject':
            application.status = 'rejected'
            application.approved_by = teacher_id
            application.approved_at = datetime.now()
            application.rejection_reason = approval_data.get('reason', '未提供理由')

            logger.info(f"  ❌ 审批拒绝: {code}, 理由: {application.rejection_reason}")

        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"  ❌ 处理审批 {approval_data.get('code')} 失败: {str(e)}")
        db.session.rollback()
        return False


def mark_as_synced(record_ids):
    """
    标记微信云数据库记录为已同步

    参数:
        record_ids (list): 记录ID列表
    """
    try:
        logger.info(f"正在标记 {len(record_ids)} 条记录为已同步")

        response = requests.post(
            CLOUD_FUNCTION_URL,
            json={
                'action': 'mark_synced',
                'data': {'ids': record_ids}
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if data.get('success'):
            logger.info(f"  ✅ 成功标记 {len(record_ids)} 条记录为已同步")
        else:
            logger.error(f"  ❌ 标记同步失败: {data.get('error')}")

    except Exception as e:
        logger.error(f"  ❌ 标记同步失败: {str(e)}")


def sync_wechat_approvals():
    """主同步流程"""
    logger.info("=" * 60)
    logger.info("开始同步微信审批记录")
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 检查配置
    if not CLOUD_FUNCTION_URL:
        logger.error("❌ 未配置 WECHAT_CLOUD_FUNCTION_URL 环境变量")
        logger.error("请在 .env 文件中添加:")
        logger.error("WECHAT_CLOUD_FUNCTION_URL=https://your-cloud-function-url")
        return

    # 2. 获取待同步的审批记录
    pending_approvals = fetch_pending_approvals()

    if not pending_approvals:
        logger.info("✅ 没有待同步的审批记录")
        logger.info("=" * 60)
        return

    logger.info(f"📥 找到 {len(pending_approvals)} 条待同步记录")

    # 3. 创建Flask应用上下文
    app = create_app()
    with app.app_context():
        synced_ids = []
        success_count = 0
        fail_count = 0

        # 4. 逐条处理审批记录
        for approval in pending_approvals:
            record_id = approval.get('_id')
            success = process_approval_in_system(approval)

            if success:
                synced_ids.append(record_id)
                success_count += 1
            else:
                fail_count += 1

        # 5. 标记为已同步
        if synced_ids:
            mark_as_synced(synced_ids)

    # 6. 输出统计
    logger.info("-" * 60)
    logger.info(f"✅ 同步完成: 成功 {success_count} 条, 失败 {fail_count} 条")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        sync_wechat_approvals()
    except KeyboardInterrupt:
        logger.info("\n收到中断信号，退出")
    except Exception as e:
        logger.error(f"程序异常: {str(e)}")
