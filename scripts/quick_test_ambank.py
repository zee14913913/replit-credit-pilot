"""
快速测试AMBANK修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser

print("="*100)
print("快速测试AMBANK专用解析器")
print("="*100)

# 1. 解析PDF
doc_ai = GoogleDocumentAIService()
pdf_path = 'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf'

print(f"\n📄 解析PDF: {pdf_path}")
parsed_doc = doc_ai.parse_pdf(pdf_path)

# 2. 使用银行专用parser
parser = BankSpecificParser()
text = parsed_doc.get('text', '')
result = parser.parse_bank_statement(text, 'AMBANK')

# 3. 显示结果
print("\n" + "="*100)
print("📋 提取的字段:")
print("="*100)
for key, value in result['fields'].items():
    print(f"  {key}: {value}")

print("\n" + "="*100)
print(f"💰 交易记录（共{len(result['transactions'])}笔）:")
print("="*100)
for i, trans in enumerate(result['transactions'], 1):
    dr = f"RM {trans['dr_amount']:>10}" if trans['dr_amount'] else "          -"
    cr = f"RM {trans['cr_amount']:>10}" if trans['cr_amount'] else "          -"
    print(f"{i:2}. {trans['date']} | {trans['description'][:40]:40} | DR: {dr} | CR: {cr} | {trans['classification']}")

print("\n" + "="*100)
print("🔖 分类统计:")
print("="*100)
owner_count = sum(1 for t in result['transactions'] if t['classification'] == 'Owner')
gz_count = sum(1 for t in result['transactions'] if t['classification'] == 'GZ')
print(f"  Owner: {owner_count}笔")
print(f"  GZ: {gz_count}笔")

print("\n" + "="*100)
print("✅ 测试完成")
print("="*100)
