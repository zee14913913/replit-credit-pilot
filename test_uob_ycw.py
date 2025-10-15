#!/usr/bin/env python3
"""Test UOB parser on YEO CHEE WANG ONE Account statements"""

import sys
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement

# List of uploaded UOB files
test_files = [
    'attached_assets/28-02-25_1760494366331.pdf',
    'attached_assets/30-04-25_1760494366333.pdf',
    'attached_assets/30-06-25_1760494366333.pdf',
    'attached_assets/31-01-25_1760494366333.pdf',
    'attached_assets/31-03-25_1760494366333.pdf',
    'attached_assets/31-05-25_1760494366334.pdf',
    'attached_assets/31-07-25_1760494366334.pdf',
    'attached_assets/31-12-24_1760494388344.pdf',
]

print(f"{'='*100}")
print(f"YEO CHEE WANG - UOB ONE Account 914-316-184-2")
print(f"Testing {len(test_files)} Monthly Statements")
print(f"{'='*100}\n")

total_transactions = 0
total_with_balance = 0

for file_path in test_files:
    try:
        info, transactions = parse_savings_statement(file_path, bank_name='UOB')
        
        balances_found = sum(1 for t in transactions if t.get('balance') is not None)
        total_transactions += len(transactions)
        total_with_balance += balances_found
        
        balance_pct = (balances_found/len(transactions)*100) if len(transactions) > 0 else 0
        print(f"{file_path.split('/')[-1]:<40} | Txns: {len(transactions):>3} | Balance: {balances_found:>3}/{len(transactions):<3} ({balance_pct:>5.1f}%)")
        
        # Show first 2 transactions for verification
        if len(transactions) > 0 and len(transactions) <= 3:
            for t in transactions:
                bal_str = f"RM {t.get('balance'):>10.2f}" if t.get('balance') is not None else "N/A"
                print(f"     {t['date']} | {t['type']:6s} | RM {t['amount']:>10.2f} | Bal: {bal_str} | {t['description'][:50]}")
    except FileNotFoundError:
        print(f"{file_path.split('/')[-1]:<40} | FILE NOT FOUND")

print(f"\n{'='*100}")
print(f"✅ SUMMARY:")
print(f"   • {len(test_files)} statements processed")
print(f"   • {total_transactions} total transactions extracted")
print(f"   • {total_with_balance}/{total_transactions} transactions with balance ({total_with_balance/total_transactions*100 if total_transactions > 0 else 0:.1f}%)")
print(f"{'='*100}")
