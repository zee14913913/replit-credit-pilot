#!/usr/bin/env python3
"""Test OCBC parser on YEO CHEE WANG individual account statements"""

import sys
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
import glob

# Get the newly uploaded OCBC files
test_files = [
    'attached_assets/APR 2024_1760494303077.pdf',
    'attached_assets/AUG 2024_1760494303077.pdf',
    'attached_assets/DEC 2024_1760494303077.pdf',
    'attached_assets/FEB 2024_1760494303077.pdf',
    'attached_assets/JAN 2024_1760494303077.pdf',
    'attached_assets/JULY 2024_1760494303077.pdf',
    'attached_assets/JUNE 2024_1760494303077.pdf',
    'attached_assets/MAR 2024_1760494303077.pdf',
    'attached_assets/MAY 2024_1760494303078.pdf',
    'attached_assets/NOV 2024_1760494303078.pdf',
    'attached_assets/OCT 2024_1760494303078.pdf',
    'attached_assets/SEP 2024_1760494303078.pdf',
    'attached_assets/APR 2025_1760494323189.pdf',
    'attached_assets/FEB 2025_1760494323200.pdf',
    'attached_assets/JAN 2025_1760494323200.pdf',
    'attached_assets/JULY 2025_1760494323201.pdf',
    'attached_assets/JUNE 2025_1760494323201.pdf',
    'attached_assets/MAR 2025_1760494323201.pdf',
    'attached_assets/MAY 2025_1760494323201.pdf',
]

print(f"{'='*100}")
print(f"YEO CHEE WANG - OCBC EASI-SAVE Account 712-261484-1 (Individual Account)")
print(f"Testing {len(test_files)} Monthly Statements")
print(f"{'='*100}\n")

total_transactions = 0
total_with_balance = 0
statements = []

for file_path in test_files:
    try:
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
        
        balance_pct = (balances_found/len(transactions)*100) if len(transactions) > 0 else 0
        print(f"{file_path.split('/')[-1]:<40} | Txns: {len(transactions):>3} | Balance: {balances_found:>3}/{len(transactions):<3} ({balance_pct:>5.1f}%)")
    except FileNotFoundError:
        print(f"{file_path.split('/')[-1]:<40} | FILE NOT FOUND")

print(f"\n{'='*100}")
print(f"✅ SUMMARY:")
print(f"   • {len(test_files)} statements processed")
print(f"   • {total_transactions} total transactions extracted")
print(f"   • {total_with_balance}/{total_transactions} transactions with balance ({total_with_balance/total_transactions*100 if total_transactions > 0 else 0:.1f}%)")
print(f"{'='*100}")
