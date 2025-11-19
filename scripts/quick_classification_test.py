import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser

# 快速测试7家银行的分类逻辑
test_cases = [
    ('AMBANK', 'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf'),
    ('AmBank', 'static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf'),
]

doc_ai = GoogleDocumentAIService()
parser = BankSpecificParser()

print("="*80)
print("快速分类测试 - 2家AMBANK".center(80))
print("="*80)

for bank, pdf_path in test_cases:
    print(f"\n【{bank}】")
    
    parsed_doc = doc_ai.parse_pdf(pdf_path)
    text = parsed_doc.get('text', '')
    
    result = parser.parse_bank_statement(text, 'AMBANK')
    transactions = result.get('transactions', [])
    
    owner = sum(1 for t in transactions if t.get('classification') == 'Owner')
    gz = sum(1 for t in transactions if t.get('classification') == 'GZ')
    
    print(f"  交易总数: {len(transactions)}笔")
    print(f"  Owner: {owner}笔 | GZ: {gz}笔")
    
    # 显示GZ交易
    if gz > 0:
        print(f"  ✅ GZ交易:")
        for t in transactions:
            if t.get('classification') == 'GZ':
                desc = t.get('description', '')[:60]
                dr = t.get('dr_amount', 0)
                print(f"     - {desc} | DR: RM {dr:,.2f}")
    else:
        print(f"  ⚠️  无GZ交易（可能该月无Supplier消费）")

print("\n" + "="*80)
print("✅ 分类逻辑测试完成！")
print("="*80)
