"""
调试AMBANK PDF格式，找出正确的解析方法
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService

doc_ai = GoogleDocumentAIService()
parsed = doc_ai.parse_pdf('static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf')

text = parsed.get('text', '')
lines = text.split('\n')

print("="*100)
print("AMBANK PDF格式分析")
print("="*100)

# 找到交易记录部分
trans_start = None
for i, line in enumerate(lines):
    if 'YOUR TRANSACTION DETAILS' in line or 'TRANSAKSI TERPERINCI' in line:
        trans_start = i
        break

if trans_start:
    print(f"\n交易记录从第{trans_start}行开始")
    print(f"\n显示交易记录部分 (行{trans_start}到{trans_start+50}):")
    print("-"*100)
    
    for i in range(trans_start, min(trans_start+50, len(lines))):
        print(f"{i:3}: {lines[i]}")
    
    # 尝试提取交易
    print("\n"+"="*100)
    print("尝试提取交易记录")
    print("="*100)
    
    # 方法1：查找连续的日期+描述+金额组合
    print("\n方法1：查找日期行，然后匹配后续的描述和金额")
    
    date_pattern = r'^\d{2}\s+[A-Z]{3}\s+\d{2}$'
    
    i = trans_start
    transaction_count = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 检查是否是日期行
        if re.match(date_pattern, line):
            date = line
            # 查找后续的描述和金额
            desc_lines = []
            amount = None
            
            j = i + 1
            while j < len(lines) and j < i + 10:  # 最多查找10行
                next_line = lines[j].strip()
                
                # 检查是否是金额 (纯数字格式 xxx.xx 或 x,xxx.xx)
                if re.match(r'^[\d,]+\.\d{2}$', next_line):
                    amount = next_line
                    break
                # 检查是否是下一个日期
                elif re.match(date_pattern, next_line):
                    break
                # 否则是描述
                elif next_line:
                    desc_lines.append(next_line)
                
                j += 1
            
            if amount:
                description = ' '.join(desc_lines)
                transaction_count += 1
                print(f"\n交易{transaction_count}:")
                print(f"  日期: {date}")
                print(f"  描述: {description[:60]}")
                print(f"  金额: RM {amount}")
                i = j
            else:
                i += 1
        else:
            i += 1
    
    print(f"\n共提取 {transaction_count} 笔交易")

print("\n"+"="*100)
