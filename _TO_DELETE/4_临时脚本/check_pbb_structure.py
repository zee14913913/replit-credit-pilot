import pandas as pd

file_path = '/home/user/uploaded_files/ALL CC CHOICES .xlsx'
df = pd.read_excel(file_path, sheet_name='PBB', header=None)

print("📊 PBB 标签页结构分析\n")
print(f"总行数: {len(df)}")
print(f"总列数: {len(df.columns)}\n")
print("=" * 80)

# 显示前30行
for idx in range(min(30, len(df))):
    row = df.iloc[idx]
    row_data = []
    for col_idx, val in enumerate(row):
        if pd.notna(val):
            val_str = str(val).strip()[:100]
            row_data.append(f"列{col_idx}: {val_str}")
    
    if row_data:
        print(f"第{idx+1}行:")
        for item in row_data:
            print(f"  {item}")
        print()

