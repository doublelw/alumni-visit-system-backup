"""
密钥管理历史测试数据生成脚本
生成分页测试所需的密钥更换历史记录
"""
from app import create_app, db
from app.models.key_history import KeyHistory
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # 清空现有数据
    KeyHistory.query.delete()
    db.session.commit()
    print("[OK] Cleared existing key history data")

    # 生成25条测试记录（足以测试分页）
    records = []
    for i in range(25):
        days_ago = 35 + i * 2  # 从35天前开始，每次递增2天
        change_date = datetime.now() - timedelta(days=days_ago)

        # 交替生成电子卡和JWT密钥记录
        if i % 2 == 0:
            record = KeyHistory(
                key_type='electronic_card',
                old_key=f'old_ec_key_{i}',
                new_key=f'new_ec_key_{i}',
                changed_by='admin',
                changed_at=change_date,
                reason='scheduled_rotation'
            )
        else:
            record = KeyHistory(
                key_type='jwt',
                old_key=f'old_jwt_key_{i}',
                new_key=f'new_jwt_key_{i}',
                changed_by='admin',
                changed_at=change_date,
                reason='scheduled_rotation'
            )

        records.append(record)

    db.session.add_all(records)
    db.session.commit()

    print(f"[OK] Generated {len(records)} key history records")

    # 验证数据
    total = KeyHistory.query.count()
    print(f"[OK] Total records in database: {total}")

    # 显示分页信息
    per_page = 20
    pages = (total + per_page - 1) // per_page
    print(f"[OK] Per page: {per_page}, Total pages: {pages}")

    # 显示第一条和最后一条记录
    first = KeyHistory.query.order_by(KeyHistory.changed_at.desc()).first()
    last = KeyHistory.query.order_by(KeyHistory.changed_at.asc()).first()
    print(f"[OK] Latest record: {first.changed_at.strftime('%Y-%m-%d %H:%M:%S')} - {first.key_type}")
    print(f"[OK] Oldest record: {last.changed_at.strftime('%Y-%m-%d %H:%M:%S')} - {last.key_type}")

    print("\n[SUCCESS] Test data generation completed!")

