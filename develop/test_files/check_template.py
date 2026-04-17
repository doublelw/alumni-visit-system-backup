"""
检查制卡中心数据导入模板文件
"""

import pandas as pd
import os

template_path = r"D:\Project\校友入校登记\制卡中心数据导入模版.xls"

print(f"模板文件路径: {template_path}")
print(f"文件是否存在: {os.path.exists(template_path)}")

if os.path.exists(template_path):
    try:
        # 读取Excel文件
        df = pd.read_excel(template_path)

        print("\n" + "="*80)
        print("📋 制卡中心数据导入模板 - 文件结构")
        print("="*80)

        print(f"\n总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")

        print("\n列名:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")

        print("\n前5行数据:")
        print(df.head().to_string())

        print("\n数据类型:")
        print(df.dtypes.to_string())

        # 检查是否有示例数据
        print("\n数据预览:")
        for index, row in df.head(3).iterrows():
            print(f"\n第{index + 1}行:")
            for col in df.columns:
                value = row[col]
                if pd.notna(value):
                    print(f"  {col}: {value}")
                else:
                    print(f"  {col}: [空]")

        # 保存为CSV便于查看
        csv_path = template_path.replace('.xls', '_preview.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n已保存CSV预览文件: {csv_path}")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n文件不存在！")

print("\n" + "="*80)
