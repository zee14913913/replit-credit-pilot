#!/usr/bin/env python3
from pdf_field_extractor import HSBCBankParser

# 测试HSBC ID 522的PDF
pdf_path = 'static/uploads/customers/Be_rich_CJY/credit_cards/HSBC/2025-10/HSBC_0034_2025-10-13.pdf'

parser = HSBCBankParser('HSBC')
result = parser.parse(pdf_path)

print("=" * 80)
print("HSBC ID 522 Parser测试")
print("=" * 80)
print(f"PDF路径: {pdf_path}")
print(f"\n提取结果:")
print(f"  Statement Date: {result['statement_date']}")
print(f"  Due Date: {result['due_date']}")
print(f"  Statement Total: RM {result['statement_total']}")
print(f"  Minimum Payment: RM {result['minimum_payment']}")
print(f"\n提取错误: {result['extraction_errors']}")
print("=" * 80)
