import pandas as pd
import re

file_path = '/home/user/uploaded_files/ALL CC CHOICES .xlsx'

def extract_cards_corporate(df):
    """提取Corporate card标签页的卡片"""
    cards = []
    for idx in range(2, 9):
        if idx < len(df):
            bank = str(df.iloc[idx, 0]).strip() if pd.notna(df.iloc[idx, 0]) else ""
            card_name = str(df.iloc[idx, 1]).strip() if pd.notna(df.iloc[idx, 1]) else ""
            if bank and card_name and bank != 'nan' and card_name != 'nan':
                cards.append(f"{bank} {card_name}")
    return cards

def extract_cards_bullet_format(df, col_index=0):
    """提取以•开头的卡片名称"""
    cards = []
    seen = set()
    
    for idx, row in df.iterrows():
        val = row[col_index]
        if pd.notna(val):
            val_str = str(val).strip()
            
            if val_str.startswith('•') or val_str.startswith('•'):
                card_name = val_str.lstrip('•').lstrip('•').strip()
                
                if 5 < len(card_name) < 100:
                    if not any(keyword in card_name for keyword in [
                        '终身免年费，无需担心', '消费享', '积分可兑换', '集中兑换',
                        '优先用', '适合', '大额消费', '日常消费', '海外消费',
                        '本地消费', '关注', '刷满', '免费', '年费', '保险', '结合'
                    ]):
                        if card_name not in seen:
                            cards.append(card_name)
                            seen.add(card_name)
    
    return cards

try:
    xls = pd.ExcelFile(file_path)
    print("📊 ALL CC CHOICES.xlsx - 精确统计每个银行的信用卡总数\n")
    print("=" * 90)
    
    total_cards = 0
    all_results = []
    
    marked_totals = {
        'Corporate card': 8,
        'MBB': 15,
        'PBB': 13
    }
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        if sheet_name == 'Corporate card':
            cards = extract_cards_corporate(df)
        elif sheet_name in ['MBB']:
            cards = extract_cards_bullet_format(df, col_index=0)
        elif sheet_name in ['PBB']:
            cards = extract_cards_bullet_format(df, col_index=1)
        else:
            cards = extract_cards_bullet_format(df, col_index=0)
            if not cards:
                cards = extract_cards_bullet_format(df, col_index=1)
        
        card_count = len(cards)
        total_cards += card_count
        
        marked = marked_totals.get(sheet_name, None)
        
        if marked:
            diff = card_count - marked
            if diff == 0:
                status = "✅ 一致"
            else:
                status = f"❌ 差异: {diff:+d}"
            marked_str = f"{marked:3d}"
        else:
            status = "⚠️  未标注"
            marked_str = "---"
        
        all_results.append({
            'bank': sheet_name,
            'count': card_count,
            'marked': marked,
            'status': status,
            'cards': cards
        })
        
        print(f"{sheet_name:25s} | 我的统计: {card_count:3d} | 标注: {marked_str} | {status}")
    
    print("=" * 90)
    print(f"\n📈 总计:")
    print(f"   - 银行总数: {len(all_results)}")
    print(f"   - 我统计的信用卡总数: {total_cards}")
    print(f"   - 已标注银行的总数: {sum(v for v in marked_totals.values())}")
    
    print(f"\n📋 卡片详情（前3个银行）:")
    for result in all_results[:3]:
        print(f"\n🏦 {result['bank']} ({len(result['cards'])}张):")
        for i, card in enumerate(result['cards'], 1):
            print(f"   {i:2d}. {card}")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

