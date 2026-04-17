"""
快速添加特批功能字段到数据库

使用方法：
    cd backend
    python add_special_approval_fields.py
"""
import sys
sys.path.insert(0, '.')

from app import create_app, db

def add_fields():
    """添加特批相关字段"""
    app = create_app()

    with app.app_context():
        # 检查字段是否已存在
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('visit_applications')]

        if 'is_special_approval' in columns:
            print("[OK] 特批字段已存在，无需添加")
            return

        # 添加字段
        print("正在添加特批相关字段...")

        with db.engine.connect() as conn:
            # 添加is_special_approval字段（SQLite不支持COMMENT）
            conn.execute(db.text("""
                ALTER TABLE visit_applications
                ADD COLUMN is_special_approval BOOLEAN NOT NULL DEFAULT 0
            """))

            # 添加special_approval_reason字段
            conn.execute(db.text("""
                ALTER TABLE visit_applications
                ADD COLUMN special_approval_reason TEXT
            """))

            conn.commit()
            conn.close()

        print("[OK] 特批字段添加成功!")
        print("  - is_special_approval: BOOLEAN (默认0)")
        print("  - special_approval_reason: TEXT")

if __name__ == '__main__':
    add_fields()
