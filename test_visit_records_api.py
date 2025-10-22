#!/usr/bin/env python3
"""
测试访问记录API
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.visit_record import VisitRecord
from flask_jwt_extended import create_access_token

def test_visit_records_api():
    """测试访问记录API"""
    app = create_app()

    with app.app_context():
        print("=== 测试访问记录API ===")

        try:
            # 测试基本查询
            print("1. 测试基本查询...")
            count = VisitRecord.query.count()
            print(f"   访问记录总数: {count}")

            # 测试查询前5条记录
            records = VisitRecord.query.limit(5).all()
            print(f"   查询到 {len(records)} 条记录")

            for i, record in enumerate(records):
                try:
                    record_dict = record.to_dict()
                    print(f"   记录 {i+1}: {record_dict.get('user', {}).get('real_name', '未知')} - {record_dict.get('verification_method', '未知')}")
                except Exception as e:
                    print(f"   记录 {i+1} to_dict 失败: {str(e)}")

            # 测试分页查询
            print("\n2. 测试分页查询...")
            pagination = VisitRecord.query.paginate(page=1, per_page=3, error_out=False)
            print(f"   分页结果: {pagination.total} 总记录, {pagination.pages} 页")

            # 测试关联查询
            print("\n3. 测试关联查询...")
            for record in records[:2]:  # 只测试前2条
                try:
                    print(f"   记录ID: {record.id}")
                    print(f"   用户: {record.user.real_name if record.user else '未知'}")
                    print(f"   验证方式: {record.verification_method}")
                    print(f"   进入时间: {record.entry_time}")
                    print(f"   状态: {'已完成' if record.exit_time else '进行中'}")
                    print("   ---")
                except Exception as e:
                    print(f"   关联查询失败: {str(e)}")

            print("\n✅ 访问记录API测试成功！")
            return True

        except Exception as e:
            print(f"\n❌ 访问记录API测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_visit_records_api()
    if success:
        print("\n🎉 访问记录API功能正常！")
    else:
        print("\n❌ 访问记录API有问题！")
        sys.exit(1)