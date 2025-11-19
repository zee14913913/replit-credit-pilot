import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser, SUPPLIERS

# 测试AMBANK分类逻辑
pdf_path = 'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf'

print("="*100)
print("AMBANK分类逻辑调试测试")
print("="*100)

# 1. 显示Supplier列表
print(f"\n📋 7个Supplier列表:")
for i, supplier in enumerate(SUPPLIERS, 1):
    print(f"  {i}. {supplier}")

# 2. 解析PDF
doc_ai = GoogleDocumentAIService()
parser = BankSpecificParser()

parsed_doc = doc_ai.parse_pdf(pdf_path)
text = parsed_doc.get('text', '')

result = parser.parse_bank_statement(text, 'AMBANK')

# 3. 显示所有交易及其分类
transactions = result.get('transactions', [])
customer_name = result.get('fields', {}).get('customer_name', 'N/A')

print(f"\n👤 提取的客户名: {customer_name}")
print(f"\n💰 交易记录 ({len(transactions)}笔):")

owner_count = 0
gz_count = 0

for i, trans in enumerate(transactions, 1):
    desc = trans.get('description', '')
    dr = trans.get('dr_amount', 0)
    cr = trans.get('cr_amount', 0)
    classification = trans.get('classification', 'N/A')
    trans_type = trans.get('type', 'N/A')
    
    if classification == 'Owner':
        owner_count += 1
    elif classification == 'GZ':
        gz_count += 1
    
    # 手动检查是否包含Supplier
    desc_upper = desc.upper()
    matched_suppliers = []
    for supplier in SUPPLIERS:
        if supplier.upper() in desc_upper:
            matched_suppliers.append(supplier)
    
    print(f"\n  [{i}] {classification} | {trans_type}")
    print(f"      描述: {desc[:80]}")
    if dr > 0:
        print(f"      DR金额: RM {dr:,.2f}")
    if cr > 0:
        print(f"      CR金额: RM {cr:,.2f}")
    
    if matched_suppliers:
        print(f"      ✅ 匹配Supplier: {', '.join(matched_suppliers)}")
    else:
        print(f"      ❌ 未匹配任何Supplier")

print(f"\n" + "="*100)
print(f"分类统计:")
print(f"  Owner: {owner_count}笔")
print(f"  GZ: {gz_count}笔")
print("="*100)

# 4. 测试特定描述
print(f"\n🧪 手动测试分类逻辑:")
test_cases = [
    ("AI SMART TECH SHAH ALAM MY", False),  # DR, 应该是GZ
    ("7SL COMPANY", False),  # DR, 应该是GZ
    ("PAYMENT VIA RPP RECEIVED", True),  # CR, 应该是Owner
    ("MCDONALD'S-KOTA", False),  # DR, 应该是Owner
]

for desc, is_credit in test_cases:
    classification = parser._classify_transaction(desc, is_credit, customer_name)
    print(f"  描述: {desc[:50]}")
    print(f"  类型: {'CR' if is_credit else 'DR'}")
    print(f"  分类: {classification}")
    print()
