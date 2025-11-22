"""
演示处理 CHEOK JUN YOON 第一张账单
展示完整的PDF解析 → 分类 → 计算 → 报告生成流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.statement_parser import parse_statement_auto
from services.transaction_classifier import TransactionClassifier
from services.credit_card_core import CreditCardCore
from decimal import Decimal
import json

# 选择第一张账单：2025-05 AMBANK
PDF_PATH = "static/uploads/customers/Be_rich_CJY/credit_cards/AMBANK/2025-05/AMBANK_9902_2025-05-28.pdf"

print("="*80)
print("CreditPilot 账单处理演示")
print("="*80)
print(f"客户：CHEOK JUN YOON")
print(f"账单：{PDF_PATH}")
print("="*80)

# 步骤1：PDF解析（Google Document AI + fallback）
print("\n🚀 步骤1：PDF解析（使用Google Document AI + pdfplumber双引擎）")
info, transactions = parse_statement_auto(PDF_PATH)

print(f"\n✅ PDF解析成功！")
print(f"   - 银行：{info.get('bank')}")
print(f"   - 账单月份：{info.get('statement_date')}")
print(f"   - Previous Balance：RM {info.get('previous_balance', 0):,.2f}")
print(f"   - 提取交易数：{len(transactions)}笔")

# 统计DR/CR
dr_txns = [t for t in transactions if t.get('type') == 'DR']
cr_txns = [t for t in transactions if t.get('type') == 'CR']

print(f"   - DR交易：{len(dr_txns)}笔")
print(f"   - CR交易：{len(cr_txns)}笔")

# 步骤2：交易分类
print("\n🔍 步骤2：交易分类（7个Suppliers）")
classifier = TransactionClassifier()

owner_expenses = []
gz_expenses = []
payments = []

for txn in transactions:
    desc = txn.get('description', '').upper()
    
    if txn.get('type') == 'DR':
        # 检查7个Suppliers
        is_supplier = False
        for supplier in classifier.suppliers:
            if supplier.upper() in desc:
                gz_expenses.append(txn)
                txn['category'] = "GZ's Expenses"
                is_supplier = True
                break
        
        if not is_supplier:
            owner_expenses.append(txn)
            txn['category'] = "Owner's Expenses"
    
    elif txn.get('type') == 'CR':
        payments.append(txn)
        txn['category'] = "Payment"

print(f"\n✅ 分类完成！")
print(f"   - Owner's Expenses：{len(owner_expenses)}笔")
print(f"   - GZ's Expenses：{len(gz_expenses)}笔")
print(f"   - Payments：{len(payments)}笔")

# 显示GZ's Expenses详情
if gz_expenses:
    print(f"\n   【GZ's Expenses明细】")
    for i, txn in enumerate(gz_expenses, 1):
        print(f"     {i}. {txn.get('date')} | {txn.get('description')[:50]} | RM {txn.get('amount', 0):,.2f}")

# 步骤3：计算财务指标
print("\n🧮 步骤3：计算9个财务指标")

statement_info = {
    'id': 0,
    'statement_month': info.get('statement_date'),
    'previous_balance': Decimal(str(info.get('previous_balance', 0))),
    'bank_name': info.get('bank'),
    'card_holder_name': 'CHEOK JUN YOON',
    'customer_name': 'CHEOK JUN YOON'
}

core = CreditCardCore()

# 转换交易格式
txn_list = [
    {
        'id': i,
        'date': t.get('date', ''),
        'description': t.get('description', ''),
        'amount': Decimal(str(t.get('amount', 0))),
        'type': t.get('type', 'DR'),
        'category': t.get('category', '')
    }
    for i, t in enumerate(transactions)
]

round1 = core._calculate_round_1(statement_info, txn_list)
gz_payment2 = Decimal('0')
final = core._calculate_final(round1, gz_payment2)

print(f"\n✅ 计算完成！")
print(f"\n【第1轮计算 - 6个基础项目】")
print(f"   Previous Balance：RM {statement_info['previous_balance']:,.2f}")
print(f"   1. Owner's Expenses：RM {round1['owner_expenses']:,.2f}")
print(f"   2. GZ's Expenses：RM {round1['gz_expenses']:,.2f}")
print(f"   3. Owner's Payment：RM {round1['owner_payment']:,.2f}")
print(f"   4. GZ's Payment1：RM {round1['gz_payment1']:,.2f}")
print(f"   5. Owner's OS Bal (Round 1)：RM {round1['owner_os_bal_round1']:,.2f}")
print(f"   6. GZ's OS Bal (Round 1)：RM {round1['gz_os_bal_round1']:,.2f}")

print(f"\n【第2轮计算】")
print(f"   7. GZ's Payment2：RM {gz_payment2:,.2f}")

print(f"\n【最终结果】")
print(f"   8. FINAL Owner OS Bal：RM {final['final_owner_os_bal']:,.2f}")
print(f"   9. FINAL GZ OS Bal：RM {final['final_gz_os_bal']:,.2f}")

# DR/CR验证
print(f"\n【DR/CR平衡验证】")
print(f"   Total DR：RM {round1['total_dr']:,.2f}")
print(f"   Total CR：RM {round1['total_cr']:,.2f}")
diff = round1['total_dr'] - round1['total_cr']
print(f"   差异：RM {diff:,.2f}")

if abs(diff) <= Decimal('0.01'):
    print(f"   状态：✅ 平衡（在±0.01误差范围内）")
else:
    print(f"   状态：⚠️ 不平衡")

# 生成JSON报告
report = {
    'customer': 'CHEOK JUN YOON',
    'pdf_path': PDF_PATH,
    'bank': info.get('bank'),
    'statement_month': info.get('statement_date'),
    'previous_balance': float(statement_info['previous_balance']),
    'transactions': {
        'total': len(transactions),
        'dr': len(dr_txns),
        'cr': len(cr_txns),
        'owner_expenses': len(owner_expenses),
        'gz_expenses': len(gz_expenses),
        'payments': len(payments)
    },
    'calculation': {
        'owner_expenses': float(round1['owner_expenses']),
        'gz_expenses': float(round1['gz_expenses']),
        'owner_payment': float(round1['owner_payment']),
        'gz_payment1': float(round1['gz_payment1']),
        'owner_os_bal_round1': float(round1['owner_os_bal_round1']),
        'gz_os_bal_round1': float(round1['gz_os_bal_round1']),
        'gz_payment2': float(gz_payment2),
        'final_owner_os_bal': float(final['final_owner_os_bal']),
        'final_gz_os_bal': float(final['final_gz_os_bal']),
        'total_dr': float(round1['total_dr']),
        'total_cr': float(round1['total_cr']),
        'balance_diff': float(diff)
    },
    'validation': {
        'is_balanced': abs(diff) <= Decimal('0.01'),
        'difference': float(diff)
    }
}

# 保存报告
os.makedirs('reports', exist_ok=True)
with open('reports/cheok_demo_statement.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n✅ 详细报告已保存：reports/cheok_demo_statement.json")
print("="*80)
