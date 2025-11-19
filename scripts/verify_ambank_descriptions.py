"""
验证AMBANK提取的描述字段
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser, SUPPLIERS

# 解析PDF
doc_ai = GoogleDocumentAIService()
pdf_path = 'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf'
parsed_doc = doc_ai.parse_pdf(pdf_path)

# 使用银行专用parser
parser = BankSpecificParser()
text = parsed_doc.get('text', '')
result = parser.parse_bank_statement(text, 'AMBANK')

print("="*100)
print("AMBANK提取的描述字段验证")
print("="*100)

print(f"\n7个Suppliers: {SUPPLIERS}\n")

for i, trans in enumerate(result['transactions'], 1):
    desc = trans['description']
    desc_upper = desc.upper()
    is_credit = trans['type'] == 'CR'
    classification = trans['classification']
    
    print(f"\n交易{i}: {trans['type']}")
    print(f"  描述: {desc}")
    print(f"  分类: {classification}")
    
    # 检查是否应该匹配Supplier
    if not is_credit:
        matched_suppliers = [s for s in SUPPLIERS if s.upper() in desc_upper]
        if matched_suppliers:
            print(f"  ✅ 匹配的Suppliers: {matched_suppliers}")
            if classification != "GZ":
                print(f"  ❌ 错误！应该是GZ，实际是{classification}")
        else:
            print(f"  ❌ 未匹配任何Supplier")
            if classification != "Owner":
                print(f"  ❌ 错误！应该是Owner，实际是{classification}")

print("\n" + "="*100)
