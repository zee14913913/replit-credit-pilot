import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService

banks_to_compare = [
    ('AMBANK', 'static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf'),
    ('UOB', 'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf'),
]

service = GoogleDocumentAIService()

for bank_name, pdf_path in banks_to_compare:
    print(f"\n{'='*100}")
    print(f"=== {bank_name} PDF: {pdf_path} ===")
    print('='*100)
    
    result = service.parse_pdf(pdf_path)
    text = result['text']
    lines = text.split('\n')
    
    print(f"\n总行数: {len(lines)}")
    print("\n前100行:")
    for i, line in enumerate(lines[:100], 1):
        print(f"{i:3d}: {line}")
    
    print(f"\n...(跳过中间部分)...\n")
    
    # 查找交易记录区域
    for i, line in enumerate(lines):
        if 'TRANSACTION' in line.upper() or 'YOUR TRANSACTION' in line.upper():
            print(f"\n交易记录区域（第{i}行开始）:")
            for j in range(i, min(i+50, len(lines))):
                print(f"{j:3d}: {lines[j]}")
            break
