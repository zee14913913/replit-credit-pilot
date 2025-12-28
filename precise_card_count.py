import pandas as pd
import re

file_path = '/home/user/uploaded_files/ALL CC CHOICES .xlsx'

# 信用卡关键词（用于识别真正的卡片名称）
CARD_KEYWORDS = [
    'card', 'visa', 'mastercard', 'master', 'amex', 'american express',
    'platinum', 'gold', 'classic', 'infinite', 'signature', 'world',
    'titanium', 'premier', 'cash back', 'cashback', 'rewards'
]

def is_card_name(text):
    """判断文本是否为信用卡名称"""
    text_lower = text.lower()
    
    # 必须包含至少一个关键词
    has_keyword = any(kw in text_lower for kw in CARD_KEYWORDS)
    
    # 排除纯建议文字（包含"使用"、"优先"、"适合"等词）
    advice_keywords = ['使用', '优先', '适合', '建议', '最大化', '尽量', '确保', '避免', '关注']
    is_advice = any(kw in text for kw in advice_keywords)
    
    # 排除太长的文字（超过100字符通常是说明文字）
    too_long = len(text) > 100
    
    return has_keyword and not is_advice and not too_long

try:
    xls = pd.ExcelFile(file_path)
    print(f"📊 精确统计每个银行的信用卡数量（仅统计真正的卡片名称）\n")
    print("=" * 80)
    
    total_cards = 0
    bank_counts = []
    all_details = []
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        card_names = set()  # 使用set去重
        
        # 遍历所有行
        for idx, row in df.iterrows():
            for col_val in row:
                if pd.notna(col_val):
                    val_str = str(col_val).strip()
                    
                    # 查找以 • 开头的行
                    if val_str.startswith('•') or val_str.startswith('•'):
                        # 提取第一部分（卡片名称通常在&或|之前）
                        parts = re.split(r'[&|]', val_str)
                        for part in parts[:2]:  # 只看前两部分
                            card_name = part.lstrip('•').lstrip('•').strip()
                            
                            # 判断是否为真正的卡片名称
                            if card_name and is_card_name(card_name):
                                card_names.add(card_name)
        
        card_count = len(card_names)
        bank_counts.append({
            'bank': sheet_name,
            'count': card_count,
            'cards': sorted(list(card_names))
        })
        total_cards += card_count
        
        print(f"✅ {sheet_name:25s} | 卡数: {card_count:3d}")
        
        # 显示前5张卡片名称
        if card_names:
            sample_cards = sorted(list(card_names))[:5]
            for i, card in enumerate(sample_cards, 1):
                print(f"   {i}. {card}")
        print()
    
    print("=" * 80)
    print(f"\n📈 汇总统计:")
    print(f"   - 总银行数: {len(bank_counts)}")
    print(f"   - 总信用卡数: {total_cards}")
    
    print(f"\n🔍 详细清单:")
    for item in bank_counts:
        print(f"   {item['bank']:25s}: {item['count']:3d} 张")
    
    # 对比用户提供的总数（如果有）
    print(f"\n📋 与标注总数对比:")
    user_totals = {
        'Corporate card': 8,
        'MBB': 15,
        'PBB': 13
    }
    
    for item in bank_counts:
        if item['bank'] in user_totals:
            user_count = user_totals[item['bank']]
            my_count = item['count']
            diff = my_count - user_count
            status = "✅" if diff == 0 else f"❌ 差异: {diff:+d}"
            print(f"   {item['bank']:25s} | 标注: {user_count:3d} | 我的统计: {my_count:3d} | {status}")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

