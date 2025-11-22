"""
分析单个银行的PDF格式
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
import re

if len(sys.argv) < 2:
    print("用法: python analyze_bank_format.py <PDF路径>")
    sys.exit(1)

pdf_path = sys.argv[1]
bank_name = pdf_path.split('/')[-3]

print("="*100)
print(f"分析银行：{bank_name}")
print(f"PDF文件：{pdf_path}")
print("="*100)

# 解析PDF
doc_ai = GoogleDocumentAIService()
parsed = doc_ai.parse_pdf(pdf_path)

text = parsed.get('text', '')
lines = text.split('\n')

print(f"\n📄 总行数：{len(lines)}")
print(f"📄 表格数量：{len(parsed.get('tables', []))}")

# 显示前50行
print("\n" + "="*100)
print("前50行内容：")
print("="*100)
for i in range(min(50, len(lines))):
    print(f"{i:3}: {lines[i][:100]}")

# 查找关键字段
print("\n" + "="*100)
print("关键字段搜索：")
print("="*100)

fields = {
    'Customer Name': [r'([A-Z\s]{10,})(?=\n|$)', r'Name[:\s]+([A-Z\s]+)'],
    'Card Number': [r'(\d{4}[\s*]+\d{4}[\s*]+\d{4}[\s*]+\d{4})', r'Card.*?(\d{4})'],
    'Statement Date': [r'Statement.*?Date[:\s]+(\d{1,2}[/-]\w{3}[/-]\d{2,4})', r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'],
    'Due Date': [r'Due.*?Date[:\s]+(\d{1,2}[/-]\w{3}[/-]\d{2,4})', r'Payment.*?Due[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'],
    'Credit Limit': [r'Credit\s+Limit[:\s]+RM\s*([\d,]+\.?\d*)', r'Limit[:\s]+RM\s*([\d,]+\.?\d*)'],
    'Transaction Pattern': [r'(\d{1,2}[/-]\w{3}|\d{1,2}[/-]\d{1,2})\s+([A-Z].*?)\s+([\d,]+\.\d{2})']
}

for field_name, patterns in fields.items():
    print(f"\n{field_name}:")
    found = False
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        if matches:
            print(f"  ✅ 找到 {len(matches)} 个匹配")
            for match in matches[:3]:  # 显示前3个
                print(f"     - {match}")
            found = True
            break
    if not found:
        print(f"  ❌ 未找到")

print("\n" + "="*100)
