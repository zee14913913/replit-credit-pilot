import pandas as pd
import re

file_path = '/home/user/uploaded_files/ALL CC CHOICES .xlsx'

try:
    xls = pd.ExcelFile(file_path)
    print(f"📊 手工统计每个银行的实际信用卡数量\n")
    print("=" * 80)
    
    total_cards = 0
    bank_counts = []
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        card_count = 0
        card_names = []
        
        # 遍历所有行，查找以 "•" 开头的信用卡名称
        for idx, row in df.iterrows():
            for col_val in row:
                if pd.notna(col_val):
                    val_str = str(col_val).strip()
                    
                    # 查找以 • 或 • 开头的行（信用卡名称）
                    if val_str.startswith('•') or val_str.startswith('•'):
                        # 提取卡片名称（在 & 或 | 之前）
                        card_name = val_str.split('&')[0].split('|')[0].strip()
                        card_name = card_name.lstrip('•').lstrip('•').strip()
                        
                        # 过滤掉空名称和纯符号
                        if card_name and len(card_name) > 3:
                            # 避免重复计数（同一张卡可能出现在多列）
                            if card_name not in card_names:
                                card_names.append(card_name)
                                card_count += 1
        
        bank_counts.append({
            'bank': sheet_name,
            'count': card_count
        })
        total_cards += card_count
        
        print(f"✅ {sheet_name:25s} | 实际卡数: {card_count:3d}")
        
        # 显示前3张卡片名称作为验证
        if card_names:
            print(f"   示例: {', '.join(card_names[:3])}")
    
    print("=" * 80)
    print(f"\n📈 汇总统计:")
    print(f"   - 总银行数: {len(bank_counts)}")
    print(f"   - 总信用卡数: {total_cards}")
    
    print(f"\n🔍 详细清单:")
    for item in bank_counts:
        print(f"   {item['bank']:25s}: {item['count']:3d} 张")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

