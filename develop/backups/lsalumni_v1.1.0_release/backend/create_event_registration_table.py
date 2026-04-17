"""
创建EventRegistration表
"""

from app import create_app, db
from app.models.event_registration import EventRegistration

def create_event_registration_table():
    """创建event_registrations表"""
    app = create_app()

    with app.app_context():
        try:
            # 创建表
            EventRegistration.__table__.create(db.engine, checkfirst=True)
            print("EventRegistration表创建成功")

            # 验证表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            if 'event_registrations' in tables:
                print("表验证成功")

                # 显示表结构
                columns = inspector.get_columns('event_registrations')
                print("\n表结构:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
            else:
                print("表验证失败")

        except Exception as e:
            print(f"创建表失败: {str(e)}")
            raise

if __name__ == "__main__":
    create_event_registration_table()