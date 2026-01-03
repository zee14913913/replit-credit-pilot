import pandas as pd

file_path = '/home/user/uploaded_files/ALL CC CHOICES .xlsx'

# 只查看有标注总数的3个标签页
sheets_to_check = ['Corporate card', 'MBB', 'PBB']

for sheet_name in sheets_to_check:
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    
    print("=" * 80)
    print(f"🏦 {sheet_name}")
    print(f"总行数: {len(df)}\n")
    
    # 显示所有数据（不省略）
    for idx, row in df.iterrows():
        row_data = []
        for col_idx, val in enumerate(row):
            if pd.notna(val):
                row_data.append(f"列{col_idx}: {str(val)[:80]}")
        
        if row_data:
            print(f"第{idx+1}行:")
            for item in row_data:
                print(f"  {item}")
            print()

