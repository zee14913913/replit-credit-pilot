#!/usr/bin/env python3
"""验证UOB 4月数据的余额连续性"""

import sys
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement

# 重新提取4月数据
info, txns = parse_savings_statement('attached_assets/30-04-25_1760494366333.pdf', bank_name='UOB')

print('完整交易列表（验证余额连续性）：')
print('='*130)

prev_balance = 3.12  # 期初余额（BALANCE B/F）
total_deposits = 0
total_withdrawals = 0

for i, t in enumerate(txns, 1):
    total_deposits += t['amount'] if t['type'] == 'credit' else 0
    total_withdrawals += t['amount'] if t['type'] == 'debit' else 0
    
    # 计算预期余额
    if t['type'] == 'credit':
        expected_balance = prev_balance + t['amount']
    else:
        expected_balance = prev_balance - t['amount']
    
    actual_balance = t.get('balance', 0)
    diff = abs(expected_balance - actual_balance)
    match = '✓' if diff < 0.01 else f'✗ 差异{diff:.2f}!'
    
    print(f'{i:2d}. {t["date"]:12s} | {t["type"]:6s} | RM {t["amount"]:>10,.2f} | '
          f'实际余额: RM {actual_balance:>10,.2f} | 预期余额: RM {expected_balance:>10,.2f} | {match}')
    
    if t["description"][:60]:
        print(f'    {t["description"][:80]}')
    
    prev_balance = actual_balance  # 使用实际余额作为下一笔的期初

print('='*130)
print(f'\n汇总:')
print(f'  总存款: RM {total_deposits:>12,.2f} (PDF应为: RM 215,750.34)')
print(f'  总取款: RM {total_withdrawals:>12,.2f} (PDF应为: RM 215,736.21)')
print(f'  最终余额: RM {txns[-1].get("balance", 0):>10,.2f} (PDF应为: RM 17.25)')
print(f'\n  期初余额: RM {3.12:>10,.2f}')
print(f'  计算期末: RM {3.12 + total_deposits - total_withdrawals:>10,.2f}')
