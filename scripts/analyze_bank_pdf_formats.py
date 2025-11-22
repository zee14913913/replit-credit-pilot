"""
分析Cheok Jun Yoon的7间银行PDF格式
找出每间银行的表格结构、列布局、关键特征
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService

# Cheok Jun Yoon的7间银行样本PDF（每间选1张）
BANK_SAMPLES = {
    "AMBANK": "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf",
    "HONG_LEONG": "static/uploads/customers/Be_rich_CJY/credit_cards/HONG_LEONG/2025-06/HONG_LEONG_3964_2025-06-16.pdf",
    "HSBC": "static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-05/HSBC_0034_2025-05-13.pdf",
    "OCBC": "static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf",
    "STANDARD_CHARTERED": "static/uploads/customers/Be_rich_CJY/credit_cards/STANDARD_CHARTERED/2025-05/STANDARD_CHARTERED_1237_2025-05-14.pdf",
    "UOB": "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf",
    "AMBANK_ALT": "static/uploads/customers/Be_rich_CJY/credit_cards/AmBank/2025-05/AmBank_6354_2025-05-28.pdf",
}

print("="*100)
print("分析Cheok Jun Yoon的7间银行PDF格式")
print("="*100)

doc_ai = GoogleDocumentAIService()

for bank_name, pdf_path in BANK_SAMPLES.items():
    print(f"\n{'='*100}")
    print(f"银行: {bank_name}")
    print(f"样本: {pdf_path}")
    print(f"{'='*100}")
    
    try:
        # 解析PDF
        parsed_doc = doc_ai.parse_pdf(pdf_path)
        
        # 分析表格数量和结构
        tables = parsed_doc.get('tables', [])
        print(f"\n📊 表格数量: {len(tables)}")
        
        for i, table in enumerate(tables):
            print(f"\n  表格 {i+1}:")
            print(f"    - Header行数: {len(table.get('header_rows', []))}")
            print(f"    - Body行数: {len(table.get('body_rows', []))}")
            
            # 分析列数
            if table.get('header_rows'):
                header = table['header_rows'][0]
                print(f"    - 列数: {len(header)}")
                print(f"    - Header内容: {header}")
            
            # 显示前3行body数据
            if table.get('body_rows'):
                print(f"    - 前3行数据示例:")
                for j, row in enumerate(table['body_rows'][:3]):
                    print(f"      行{j+1}: {row}")
        
        # 分析文本内容中的关键字段
        text = parsed_doc.get('text', '')
        
        print(f"\n📝 关键字段检测:")
        keywords = [
            'Previous Balance', 'Statement Date', 'Card Number',
            'Transaction', 'Date', 'Description', 'Amount', 
            'DR', 'CR', 'Debit', 'Credit', 'Payment'
        ]
        
        for keyword in keywords:
            if keyword.upper() in text.upper():
                # 找出关键字的上下文
                idx = text.upper().find(keyword.upper())
                context = text[max(0, idx-20):min(len(text), idx+len(keyword)+30)]
                print(f"  ✅ {keyword}: ...{context}...")
        
        # 提取当前方法得到的交易数
        fields = doc_ai.extract_bank_statement_fields(parsed_doc)
        transactions = fields.get('transactions', [])
        print(f"\n🔍 当前提取结果: {len(transactions)}笔交易")
        
        if len(transactions) > 0:
            print(f"  示例交易:")
            for txn in transactions[:3]:
                print(f"    - {txn.get('date')} | {txn.get('description')[:40]} | RM {txn.get('amount')} | {txn.get('type')}")
        else:
            print(f"  ❌ 当前方法未能提取交易！")
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")

print(f"\n{'='*100}")
print("分析完成")
print(f"{'='*100}")
