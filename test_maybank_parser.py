#!/usr/bin/env python3
"""Test script for Maybank Islamic savings parser"""

import sys
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
import glob

# Test with first file
test_files = sorted(glob.glob('attached_assets/*MBB*.pdf') + glob.glob('attached_assets/*1760493863*.pdf') + glob.glob('attached_assets/*1760493881*.pdf'))

print(f"Found {len(test_files)} Maybank files to test\n")

for file_path in test_files[:3]:  # Test first 3 files
    print(f"\n{'='*80}")
    print(f"Testing: {file_path}")
    print('='*80)
    
    info, transactions = parse_savings_statement(file_path, bank_name='Maybank')
    
    print(f"\n📊 Statement Info:")
    print(f"  Bank: {info['bank_name']}")
    print(f"  Account Last 4: {info['account_last4']}")
    print(f"  Statement Date: {info['statement_date']}")
    print(f"  Total Transactions: {info['total_transactions']}")
    
    print(f"\n💳 First 5 Transactions:")
    for i, txn in enumerate(transactions[:5], 1):
        print(f"  {i}. {txn['date']} | {txn['type']:6s} | RM {txn['amount']:>10.2f} | Balance: {txn.get('balance', 'N/A'):>10} | {txn['description'][:60]}")
    
    if len(transactions) > 5:
        print(f"  ... and {len(transactions) - 5} more transactions")
    
    # Verify balance extraction
    balances_found = sum(1 for t in transactions if t.get('balance') is not None)
    print(f"\n✅ Balance Extraction: {balances_found}/{len(transactions)} transactions have balance ({balances_found/len(transactions)*100:.1f}%)")

print(f"\n{'='*80}")
print("✅ Test complete!")
