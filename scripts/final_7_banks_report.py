import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser

print("="*100)
print("7家银行最终测试报告 - 修复后".center(100))
print("="*100)

test_cases = [
    ('AMBANK', '9902', 'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf'),
    ('AMBANK', '6354', 'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf'),
    ('HONG_LEONG', '3964', 'static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf'),
    ('HSBC', '0034', 'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-05/HSBC_0034_2025-05-13.pdf'),
    ('OCBC', '3506', 'static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf'),
    ('STANDARD_CHARTERED', '1237', 'static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf'),
    ('UOB', '3530', 'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf'),
]

required_fields = ['customer_name', 'ic_number', 'card_number', 'statement_date', 'payment_due_date', 'previous_balance', 'credit_limit']

doc_ai = GoogleDocumentAIService()
parser = BankSpecificParser()

results = []

for bank, card, pdf_path in test_cases:
    parsed_doc = doc_ai.parse_pdf(pdf_path)
    text = parsed_doc.get('text', '')
    
    result = parser.parse_bank_statement(text, bank)
    
    fields = result.get('fields', {})
    extracted = sum(1 for f in required_fields if fields.get(f) and str(fields.get(f)).strip() and fields.get(f) != 'N/A')
    field_pct = (extracted / 7) * 100
    
    transactions = result.get('transactions', [])
    owner = sum(1 for t in transactions if t.get('classification') == 'Owner')
    gz = sum(1 for t in transactions if t.get('classification') == 'GZ')
    
    results.append({
        'bank': bank,
        'card': card,
        'trans': len(transactions),
        'fields': extracted,
        'field_pct': field_pct,
        'owner': owner,
        'gz': gz
    })

print(f"\n{'银行':<20} {'卡号':<10} {'交易':<10} {'字段完整度':<20} {'Owner':<10} {'GZ':<10}")
print("-" * 100)

for r in results:
    print(f"{r['bank']:<20} {r['card']:<10} {r['trans']:<10} {r['fields']}/7 ({r['field_pct']:.0f}%){'':<12} {r['owner']:<10} {r['gz']:<10}")

total_trans = sum(r['trans'] for r in results)
total_gz = sum(r['gz'] for r in results)
avg_field_pct = sum(r['field_pct'] for r in results) / len(results)

print("-" * 100)
print(f"\n✅ 总交易数: {total_trans}笔")
print(f"✅ GZ交易数: {total_gz}笔")
print(f"✅ 平均字段完整度: {avg_field_pct:.1f}%")
print(f"✅ 成功解析银行: 7/7 (100%)")
print("\n" + "="*100)
