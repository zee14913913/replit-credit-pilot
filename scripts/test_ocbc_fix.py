import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService
from services.bank_specific_parsers import BankSpecificParser

print("="*100)
print("OCBC字段提取修复验证测试".center(100))
print("="*100)

# OCBC PDF路径
pdf_path = 'static/uploads/customers/Be_rich_CJY/credit_cards/OCBC/2025-05/OCBC_3506_2025-05-13.pdf'

# 必须提取的7个字段
required_fields = [
    'customer_name', 'ic_number', 'card_number', 
    'statement_date', 'payment_due_date', 'previous_balance', 
    'credit_limit'
]

print(f"\n📄 测试PDF: {pdf_path}")
print(f"🎯 目标: 字段提取率从 0/7 (0%) → 至少 5/7 (71%)+\n")

# 解析
doc_ai = GoogleDocumentAIService()
parser = BankSpecificParser()

# 重新加载配置（确保使用最新的regex）
parser = BankSpecificParser()

parsed_doc = doc_ai.parse_pdf(pdf_path)
text = parsed_doc.get('text', '')

print(f"✅ Document AI解析完成，文本长度: {len(text)}字符")

# 银行检测
detected_bank = parser.detect_bank(text)
print(f"✅ 自动检测银行: {detected_bank}")

# 解析账单
result = parser.parse_bank_statement(text, 'OCBC')

# 分析字段提取
fields = result.get('fields', {})
extracted_fields = []
missing_fields = []

print(f"\n{'='*100}")
print("字段提取结果分析")
print(f"{'='*100}\n")

for field in required_fields:
    value = fields.get(field)
    if value and str(value).strip() and value != 'N/A':
        extracted_fields.append(field)
        print(f"  ✅ {field:<20} = {value}")
    else:
        missing_fields.append(field)
        print(f"  ❌ {field:<20} = (未提取)")

# 计算提升率
field_count = len(extracted_fields)
field_percentage = (field_count / len(required_fields)) * 100

print(f"\n{'='*100}")
print(f"字段提取统计")
print(f"{'='*100}")
print(f"  已提取字段: {field_count}/7 ({field_percentage:.1f}%)")
print(f"  缺失字段: {len(missing_fields)}/7")

if field_percentage >= 60:
    status = "✅ PASS - 达到目标（≥60%）"
    emoji = "🎉"
else:
    status = "❌ FAIL - 未达目标（<60%）"
    emoji = "⚠️"

print(f"\n{emoji} 测试结果: {status}")

# 交易记录
transactions = result.get('transactions', [])
print(f"\n💰 交易记录: {len(transactions)}笔")

if transactions:
    print(f"  示例交易（前3笔）:")
    for i, trans in enumerate(transactions[:3], 1):
        desc = trans.get('description', 'N/A')[:50]
        dr = trans.get('dr_amount', 0)
        cr = trans.get('cr_amount', 0)
        classification = trans.get('classification', 'N/A')
        
        if dr > 0:
            print(f"    {i}. [{classification}] DR: RM {dr:>8,.2f} | {desc}")
        elif cr > 0:
            print(f"    {i}. [{classification}] CR: RM {cr:>8,.2f} | {desc}")

print(f"\n{'='*100}")

# 如果未达标，显示Document AI原始文本前100行
if field_percentage < 60:
    print("\n📋 Document AI原始文本（前100行）以供调试:")
    print("="*100)
    lines = text.split('\n')
    for i, line in enumerate(lines[:100], 1):
        print(f"{i:3d}: {line}")
    print("="*100)
