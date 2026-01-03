import pandas as pd
import re

file_path = '/home/user/uploaded_files/ALL CC CHOICES .xlsx'

def extract_card_names(sheet_name):
    """提取标签页中所有的信用卡名称"""
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    
    card_names = []
    
    for idx, row in df.iterrows():
        # 查找列0（通常是卡片名称列）
        val = row[0]
        if pd.notna(val):
            val_str = str(val).strip()
            
            # 对于Corporate card：直接从表格中提取（非表头行）
            if sheet_name == 'Corporate card' and idx >= 2 and idx < 9:
                # 从列1获取卡片名称
                card_name = str(row[1]).strip()
                bank = str(row[0]).strip()
                if card_name and card_name != 'Card Name':
                    card_names.append(f"{bank} {card_name}")
            
            # 对于其他银行：查找包含银行名/卡片特征的行
            # 典型的卡片名称行：Maybank Visa Infinite, Maybank 2 Gold Cards等
            elif any(keyword in val_str for keyword in ['Maybank', 'Bank', 'Card', 'Visa', 'Master', 'Amex']):
                # 排除表头、说明文字
                if not any(exclude in val_str for exclude in ['表格', '主流卡种', '优点', '建议', '总结', '主要积分']):
                    # 去除•符号
                    clean_name = val_str.lstrip('•').lstrip('•').strip()
                    
                    # 只保留较短的名称（通常<80字符）
                    if len(clean_name) < 80 and clean_name:
                        card_names.append(clean_name)
    
    return card_names

# 检查3个有标注总数的银行
print("📊 精确提取信用卡名称\n")
print("=" * 80)

for sheet_name in ['Corporate card', 'MBB', 'PBB']:
    cards = extract_card_names(sheet_name)
    
    print(f"\n🏦 {sheet_name}")
    print(f"提取到的卡片数量: {len(cards)}")
    print("\n卡片清单:")
    for i, card in enumerate(cards, 1):
        print(f"  {i:2d}. {card}")

