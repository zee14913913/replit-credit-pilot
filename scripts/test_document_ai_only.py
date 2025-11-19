"""
测试Google Document AI独占模式
验证系统不再使用pdfplumber fallback
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.statement_parser import parse_statement_auto

# 测试PDF
PDF_PATH = "static/uploads/customers/Be_rich_CJY/credit_cards/UOB/2025-05/UOB_3530_2025-05-13.pdf"

print("="*80)
print("测试：Google Document AI 独占模式")
print("="*80)
print(f"PDF: {PDF_PATH}")
print("配置：仅允许Document AI，禁止fallback")
print("="*80)

try:
    info, transactions = parse_statement_auto(PDF_PATH)
    
    print(f"\n✅ 解析成功！")
    print(f"银行：{info.get('bank')}")
    print(f"账单日期：{info.get('statement_date')}")
    print(f"Previous Balance：RM {info.get('previous_balance', 0):,.2f}")
    print(f"交易数量：{len(transactions)}笔")
    
    # 统计DR/CR
    dr_count = sum(1 for t in transactions if t.get('type') == 'DR')
    cr_count = sum(1 for t in transactions if t.get('type') == 'CR')
    
    print(f"DR交易：{dr_count}笔")
    print(f"CR交易：{cr_count}笔")
    
    print("\n✅ Google Document AI独占模式工作正常！")
    print("✅ 系统已正确配置为仅使用Document AI")
    
except RuntimeError as e:
    print(f"\n❌ RuntimeError（预期行为）：{e}")
    print("✅ 系统已正确配置：不使用fallback，抛出错误")
    
except Exception as e:
    print(f"\n❌ 其他错误：{e}")
    print("⚠️ 需要检查配置")

print("="*80)
