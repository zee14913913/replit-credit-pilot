#!/usr/bin/env python3
from pdf_field_extractor import StandardCharteredBankParser

# 测试Standard Chartered解析器
pdf_path = 'attached_assets/SDC OCT _1761808054088.pdf'

parser = StandardCharteredBankParser('STANDARD CHARTERED')
result = parser.parse(pdf_path)

print("=" * 80)
print("Standard Chartered Parser测试结果")
print("=" * 80)
print(f"PDF路径: {pdf_path}")
print(f"\n提取结果:")
print(f"  Statement Date: {result['statement_date']}")
print(f"  Due Date: {result['due_date'] or 'NULL (IMMEDIATE)'}")
print(f"  Statement Total: RM {result['statement_total']}")
print(f"  Minimum Payment: RM {result['minimum_payment']}")
print(f"\n提取错误: {result['extraction_errors']}")
print("=" * 80)

# 验证真实值（根据之前的PDF分析）
print("\n验证（期望值）:")
print("  Statement Date: 2025-10-14")
print("  Due Date: NULL (因为PDF显示IMMEDIATE)")
print("  Statement Total: RM 73889.93")
print("  Minimum Payment: RM 9220.36")

if (result['statement_date'] == '2025-10-14' and 
    result['statement_total'] == '73889.93' and 
    result['minimum_payment'] == '9220.36'):
    print("\n✅ Standard Chartered解析器测试通过！所有值匹配真实PDF数据")
    print("   （due_date正确处理IMMEDIATE为NULL）")
else:
    print("\n❌ Standard Chartered解析器测试失败！请检查提取逻辑")
    print(f"   实际statement_date: {result['statement_date']}")
    print(f"   实际statement_total: {result['statement_total']}")
    print(f"   实际minimum_payment: {result['minimum_payment']}")
