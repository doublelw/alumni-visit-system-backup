"""
检查数据库字段"""
import sys
sys.path.insert(0, '.')

from app import create_app, db

app = create_app()

with app.app_context():
    inspector = db.inspect(db.engine)
    columns = inspector.get_columns('visit_applications')

    print("visit_applications 表字段:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")

    # 检查特批字段
    has_special = any(col['name'] == 'is_special_approval' for col in columns)
    has_reason = any(col['name'] == 'special_approval_reason' for col in columns)

    print(f"\nis_special_approval: {'存在' if has_special else '不存在'}")
    print(f"special_approval_reason: {'存在' if has_reason else '不存在'}")
