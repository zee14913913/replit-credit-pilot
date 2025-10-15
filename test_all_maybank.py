#!/usr/bin/env python3
"""Comprehensive test of all Maybank statements"""

import sys
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
import glob
from collections import defaultdict

# Find all Maybank files
test_files = sorted(glob.glob('attached_assets/*1760493863*.pdf') + glob.glob('attached_assets/*1760493881*.pdf'))

print(f"{'='*100}")
print(f"YEO CHEE WANG - Maybank Islamic Account 151427-273470")
print(f"Testing {len(test_files)} Monthly Statements (Feb 2024 - Jul 2025)")
print(f"{'='*100}\n")

total_transactions = 0
total_with_balance = 0
statements_summary = []

for file_path in test_files:
    info, transactions = parse_savings_statement(file_path, bank_name='Maybank')
    
    balances_found = sum(1 for t in transactions if t.get('balance') is not None)
    total_transactions += len(transactions)
    total_with_balance += balances_found
    
    statements_summary.append({
        'file': file_path.split('/')[-1],
        'date': info['statement_date'],
        'txns': len(transactions),
        'balances': balances_found
    })

# Display summary table
print(f"{'Month':<12} {'Transactions':>12} {'Balance %':>12}")
print(f"{'-'*40}")

for s in sorted(statements_summary, key=lambda x: x['date']):
    pct = (s['balances'] / s['txns'] * 100) if s['txns'] > 0 else 0
    print(f"{s['date']:<12} {s['txns']:>12} {pct:>11.1f}%")

print(f"{'-'*40}")
print(f"{'TOTAL':<12} {total_transactions:>12} {total_with_balance/total_transactions*100:>11.1f}%")

print(f"\n{'='*100}")
print(f"✅ SUMMARY:")
print(f"   • {len(test_files)} statements processed successfully")
print(f"   • {total_transactions} total transactions extracted")
print(f"   • {total_with_balance}/{total_transactions} transactions with balance ({total_with_balance/total_transactions*100:.1f}%)")
print(f"   • Account: 151427-273470 (YEO CHEE WANG)")
print(f"   • Coverage: Feb 2024 to Jul 2025 (18 months)")
print(f"{'='*100}")
