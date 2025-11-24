#!/usr/bin/env python3
from pdf_field_extractor import UOBBankParser

# 测试UOB解析器
pdf_path = 'static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf'

parser = UOBBankParser('UOB')
result = parser.parse(pdf_path)

print("=" * 80)
print("UOB Parser测试结果")
print("=" * 80)
print(f"PDF路径: {pdf_path}")
print(f"\n提取结果:")
print(f"  Statement Date: {result['statement_date']}")
print(f"  Due Date: {result['due_date']}")
print(f"  Statement Total: RM {result['statement_total']}")
print(f"  Minimum Payment: RM {result['minimum_payment']}")
print(f"\n提取错误: {result['extraction_errors']}")
print("=" * 80)

# 验证真实值（根据之前的PDF分析）
print("\n验证（期望值）:")
print("  Statement Date: 2025-05-13")
print("  Due Date: 2025-06-02")
print("  Statement Total: RM 10.38")
print("  Minimum Payment: RM 10.38")

if (result['statement_date'] == '2025-05-13' and 
    result['due_date'] == '2025-06-02' and 
    result['statement_total'] == '10.38' and 
    result['minimum_payment'] == '10.38'):
    print("\n✅ UOB解析器测试通过！所有值匹配真实PDF数据")
else:
    print("\n❌ UOB解析器测试失败！请检查提取逻辑")
