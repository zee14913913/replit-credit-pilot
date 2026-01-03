import pandas as pd
import sys

file_path = '/home/user/uploaded_files/ALL CC CHOICES .xlsx'

try:
    xls = pd.ExcelFile(file_path)
    print(f"📊 ALL CC CHOICES.xlsx - 银行信用卡总数核对\n")
    print("=" * 80)
    
    total_cards = 0
    bank_totals = []
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        # 查找最后几行中的总数标注
        last_rows = df.tail(10)  # 检查最后10行
        
        found_total = None
        total_row_idx = None
        
        # 遍历最后几行，查找包含数字的单元格（可能是总数）
        for idx in range(len(last_rows)):
            row = last_rows.iloc[idx]
            for col_idx, cell in enumerate(row):
                cell_str = str(cell).strip()
                # 查找纯数字或类似 "总计: 15" 的模式
                if cell_str.isdigit() and int(cell_str) > 0 and int(cell_str) < 100:
                    # 检查这一行是否是最后一行或倒数第二行
                    actual_row_idx = len(df) - len(last_rows) + idx
                    if actual_row_idx >= len(df) - 3:  # 最后3行内
                        found_total = int(cell_str)
                        total_row_idx = actual_row_idx
                        break
            if found_total:
                break
        
        if found_total:
            bank_totals.append({
                'bank': sheet_name,
                'total': found_total,
                'row_index': total_row_idx
            })
            total_cards += found_total
            print(f"✅ {sheet_name:25s} | 总数: {found_total:3d} | 位置: 第{total_row_idx+1}行")
        else:
            print(f"❌ {sheet_name:25s} | 未找到总数标注")
    
    print("=" * 80)
    print(f"\n📈 汇总统计:")
    print(f"   - 已标注总数的银行: {len(bank_totals)}/18")
    print(f"   - 已标注银行的信用卡总数: {total_cards}")
    print(f"\n🔍 详细清单:")
    for item in bank_totals:
        print(f"   {item['bank']:25s}: {item['total']:3d} 张")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

