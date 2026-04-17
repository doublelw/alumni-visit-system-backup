# -*- coding: utf-8 -*-
"""
初始化密钥历史数据
"""

from app import create_app, db
from app.models.key_history import KeyHistory
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print('=== 初始化密钥历史数据 ===\n')

    # 检查现有数据
    count = KeyHistory.query.count()
    print(f'现有记录数: {count}')

    if count == 0:
        print('添加初始密钥历史记录...')

        # 创建两条初始记录（35天前，显示需要更换）
        thirty_five_days_ago = datetime.now() - timedelta(days=35)

        # 电子卡密钥历史
        ec_history = KeyHistory(
            key_type='electronic_card',
            old_key='old_ec_key_2024',
            new_key='cur_ec_key_2024',
            changed_by='system',
            changed_at=thirty_five_days_ago,
            reason='initial_setup'
        )
        db.session.add(ec_history)

        # JWT密钥历史
        jwt_history = KeyHistory(
            key_type='jwt',
            old_key='old_jwt_key_2024',
            new_key='cur_jwt_key_2024',
            changed_by='system',
            changed_at=thirty_five_days_ago,
            reason='initial_setup'
        )
        db.session.add(jwt_history)

        db.session.commit()

        print('[OK] 已添加2条初始记录')
        print('  - 电子卡密钥: 35天前创建')
        print('  - JWT密钥: 35天前创建')
        print('  - 状态: 两者都已使用超过30天，需要更换')
    else:
        # 显示现有记录
        print('\n最近的密钥更换记录:')
        records = KeyHistory.query.order_by(KeyHistory.changed_at.desc()).limit(5).all()
        for r in records:
            days_ago = (datetime.now() - r.changed_at).days
            print(f'  {r.key_type}: {r.changed_at.strftime("%Y-%m-%d")} ({days_ago}天前) by {r.changed_by}')

    print('\n=== 完成！===')
