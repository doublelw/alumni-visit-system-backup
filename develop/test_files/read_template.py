import pandas as pd
import os

template_path = r"D:\Project\校友入校登记\制卡中心数据导入模版.xls"

print("Template path:", template_path)
print("File exists:", os.path.exists(template_path))

if os.path.exists(template_path):
    try:
        df = pd.read_excel(template_path)

        print("\n" + "="*80)
        print("Card Center Data Import Template - File Structure")
        print("="*80)

        print(f"\nTotal rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}")

        print("\nColumn names:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")

        print("\nFirst 5 rows:")
        print(df.head().to_string())

        print("\nData types:")
        print(df.dtypes.to_string())

        csv_path = r"D:\Project\校友入校登记\template_preview.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\nCSV preview saved: {csv_path}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

print("\nDone!")
