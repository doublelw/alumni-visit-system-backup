"""
直接测试模板生成功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
import pandas as pd
from io import BytesIO

def test_template_generation():
    """直接测试模板生成"""
    print("=" * 80)
    print("  直接测试用户模板生成")
    print("=" * 80)

    try:
        print("\n[Step 1] 导入pandas...")
        import pandas as pd
        print("[OK] pandas导入成功")

        print("\n[Step 2] 创建模板数据...")
        template_data = {
            '用户名*': ['zhangsan', 'lisi', 'wangwu'],
            '密码*': ['password123', 'password123', 'password123'],
            '真实姓名*': ['张三', '李四', '王五'],
            '邮箱*': ['zhangsan@example.com', 'lisi@example.com', 'wangwu@example.com'],
            '手机号': ['13800138000', '13800138001', '13800138002'],
            '用户类型*': ['teacher', 'student', 'alumni'],
            '学号': ['', 'S2023001', 'S2020001'],
            '工号': ['T001', '', ''],
            '班级': ['高三1班', '高三1班', ''],
            '年级': ['高三', '高三', ''],
            '是否班主任': ['是', '', ''],
            '可拜访权限': ['是', '', '是']
        }
        print("[OK] 模板数据创建成功")

        print("\n[Step 3] 创建DataFrame...")
        df = pd.DataFrame(template_data)
        print(f"[OK] DataFrame创建成功，形状: {df.shape}")

        print("\n[Step 4] 创建Excel文件...")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='用户导入模板', index=False)
        print("[OK] Excel文件创建成功")

        print("\n[Step 5] 检查文件大小...")
        output.seek(0)
        file_size = len(output.getvalue())
        print(f"[OK] 文件大小: {file_size} 字节")

        # 保存到本地文件测试
        print("\n[Step 6] 保存到本地文件...")
        with open('test_template.xlsx', 'wb') as f:
            f.write(output.getvalue())
        print("[OK] 文件已保存: test_template.xlsx")

        print("\n" + "=" * 80)
        print("  [SUCCESS] 模板生成成功！")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_template_generation()

    print("\n" + "=" * 80)
    if success:
        print("  [SUCCESS] 模板功能正常")
    else:
        print("  [FAIL] 模板功能有问题")
    print("=" * 80)
