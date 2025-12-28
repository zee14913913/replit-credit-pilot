import pandas as pd
import sys

file_path = '/home/user/uploaded_files/ALL CC CHOICES .xlsx'

try:
    xls = pd.ExcelFile(file_path)
    print(f"📊 详细检查每个银行标签页的最后几行\n")
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        print("=" * 80)
        print(f"🏦 {sheet_name}")
        print(f"   总行数: {len(df)}")
        print(f"\n   最后5行内容:")
        
        last_5 = df.tail(5)
        for idx, row in last_5.iterrows():
            row_data = []
            for val in row:
                if pd.notna(val):
                    val_str = str(val).strip()
                    if val_str:
                        row_data.append(val_str)
            
            if row_data:
                print(f"   第{idx+1}行: {' | '.join(row_data[:5])}")  # 只显示前5列
        print()

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

