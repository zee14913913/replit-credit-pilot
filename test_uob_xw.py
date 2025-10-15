#!/usr/bin/env python3
"""Test UOB XW MAMA statements"""

import sys
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
import pdfplumber
import glob

# Find UOB files
all_files = sorted(glob.glob('attached_assets/*1760494*.pdf'))
uob_files = []

for file_path in all_files:
    try:
        with pdfplumber.open(file_path) as pdf:
            text = pdf.pages[0].extract_text()
            if 'UOB' in text.upper() or 'UNITED OVERSEAS BANK' in text.upper() or 'ONE Account' in text:
                uob_files.append(file_path)
    except:
        pass

print(f"{'='*100}")
print(f"TEO YOK CHU & YEO CHEE WANG (XW MAMA) - UOB Account 914-316-184-2")
print(f"Testing {len(uob_files)} Monthly Statements")
print(f"{'='*100}\n")

total_transactions = 0
total_with_balance = 0

for file_path in uob_files:
    info, transactions = parse_savings_statement(file_path, bank_name='UOB')
    
    balances_found = sum(1 for t in transactions if t.get('balance') is not None)
    total_transactions += len(transactions)
    total_with_balance += balances_found
    
    print(f"{file_path.split('/')[-1]:<35} | Txns: {len(transactions):>3} | Balance: {balances_found:>3}/{len(transactions):<3} ({balances_found/len(transactions)*100 if len(transactions) > 0 else 0:>5.1f}%)")
    
    # Show first 3 transactions
    if len(transactions) > 0 and len(transactions) <= 3:
        for t in transactions:
            bal_str = f"RM {t.get('balance'):>10.2f}" if t.get('balance') is not None else "N/A"
            print(f"     {t['date']} | {t['type']:6s} | RM {t['amount']:>10.2f} | Bal: {bal_str} | {t['description'][:50]}")

print(f"\n{'='*100}")
print(f"✅ SUMMARY:")
print(f"   • {len(uob_files)} statements processed")
print(f"   • {total_transactions} total transactions extracted")
print(f"   • {total_with_balance}/{total_transactions} transactions with balance ({total_with_balance/total_transactions*100 if total_transactions > 0 else 0:.1f}%)")
print(f"{'='*100}")
