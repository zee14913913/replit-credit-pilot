#!/usr/bin/env python3
"""Test OCBC savings parser"""

import sys
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
import glob

# Find all OCBC files
test_files = sorted(glob.glob('attached_assets/*2024*.pdf') + glob.glob('attached_assets/*2025*.pdf'))
test_files = [f for f in test_files if 'OCBC' in open(f, 'rb').read(100).decode('latin1', errors='ignore') or 'JAN 2025' in f or 'FEB 2025' in f]

print(f"Found {len(test_files)} OCBC files to test\n")

total_transactions = 0
total_with_balance = 0

for file_path in test_files[:3]:  # Test first 3
    print(f"\n{'='*80}")
    print(f"Testing: {file_path}")
    print('='*80)
    
    info, transactions = parse_savings_statement(file_path, bank_name='OCBC')
    
    print(f"\n📊 Statement Info:")
    print(f"  Bank: {info['bank_name']}")
    print(f"  Account Last 4: {info['account_last4']}")
    print(f"  Statement Date: {info['statement_date']}")
    print(f"  Total Transactions: {info['total_transactions']}")
    
    print(f"\n💳 Transactions:")
    for i, txn in enumerate(transactions, 1):
        bal_str = f"RM {txn.get('balance'):>10.2f}" if txn.get('balance') is not None else "N/A"
        print(f"  {i}. {txn['date']} | {txn['type']:6s} | RM {txn['amount']:>10.2f} | Bal: {bal_str} | {txn['description'][:60]}")
    
    balances_found = sum(1 for t in transactions if t.get('balance') is not None)
    total_transactions += len(transactions)
    total_with_balance += balances_found
    
    if len(transactions) > 0:
        print(f"\n✅ Balance: {balances_found}/{len(transactions)} ({balances_found/len(transactions)*100:.1f}%)")

print(f"\n{'='*80}")
print(f"TOTAL: {total_transactions} transactions, {total_with_balance} with balance")
