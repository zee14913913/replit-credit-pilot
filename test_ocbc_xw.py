#!/usr/bin/env python3
"""Test OCBC XW MAMA statements"""

import sys
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
import glob

# Find XW MAMA OCBC files
test_files = sorted(glob.glob('attached_assets/*1760494*.pdf'))

print(f"{'='*100}")
print(f"TEO YOK CHU & YEO CHEE WANG (XW MAMA) - OCBC Account 712-261489-2")
print(f"Testing {len(test_files)} Monthly Statements")
print(f"{'='*100}\n")

total_transactions = 0
total_with_balance = 0
statements = []

for file_path in test_files:
    info, transactions = parse_savings_statement(file_path, bank_name='OCBC')
    
    balances_found = sum(1 for t in transactions if t.get('balance') is not None)
    total_transactions += len(transactions)
    total_with_balance += balances_found
    
    statements.append({
        'file': file_path.split('/')[-1],
        'date': info['statement_date'],
        'txns': len(transactions),
        'balances': balances_found
    })
    
    print(f"{file_path.split('/')[-1]:<35} | Txns: {len(transactions):>3} | Balance: {balances_found:>3}/{len(transactions):<3} ({balances_found/len(transactions)*100 if len(transactions) > 0 else 0:>5.1f}%)")

print(f"\n{'='*100}")
print(f"✅ SUMMARY:")
print(f"   • {len(test_files)} statements processed")
print(f"   • {total_transactions} total transactions extracted")
print(f"   • {total_with_balance}/{total_transactions} transactions with balance ({total_with_balance/total_transactions*100 if total_transactions > 0 else 0:.1f}%)")
print(f"{'='*100}")
