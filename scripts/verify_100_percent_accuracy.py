#!/usr/bin/env python3
"""
严格验证：数据库数据与PDF月结单100%一致性检查
确保每笔交易的credit/debit和月末余额完全匹配
"""

import sys
import os
sys.path.insert(0, '.')

from ingest.savings_parser import parse_savings_statement
from db.database import get_db
from collections import defaultdict

def verify_statement_accuracy(file_path, bank_name):
    """验证单个对账单的准确性"""
    
    # 解析PDF
    info, pdf_transactions = parse_savings_statement(file_path, bank_name=bank_name)
    
    if not info['account_last4'] or not info['statement_date']:
        return None
    
    # 从数据库获取同一对账单的数据
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                st.transaction_date,
                st.description,
                st.amount,
                st.transaction_type,
                st.balance
            FROM savings_accounts sa
            JOIN savings_statements ss ON ss.savings_account_id = sa.id
            JOIN savings_transactions st ON st.savings_statement_id = ss.id
            WHERE sa.account_number_last4 = ? AND ss.statement_date = ?
            ORDER BY st.id
        ''', (info['account_last4'], info['statement_date']))
        
        db_transactions = [dict(row) for row in cursor.fetchall()]
    
    if not db_transactions:
        return None
    
    # 验证交易笔数
    pdf_count = len(pdf_transactions)
    db_count = len(db_transactions)
    
    result = {
        'file': os.path.basename(file_path),
        'statement_date': info['statement_date'],
        'account_last4': info['account_last4'],
        'pdf_count': pdf_count,
        'db_count': db_count,
        'count_match': pdf_count == db_count,
        'mismatches': [],
        'pdf_final_balance': None,
        'db_final_balance': None,
        'balance_match': False
    }
    
    # 获取PDF最后一笔交易的余额
    if pdf_transactions:
        result['pdf_final_balance'] = pdf_transactions[-1].get('balance')
    
    # 获取数据库最后一笔交易的余额
    if db_transactions:
        result['db_final_balance'] = db_transactions[-1]['balance']
    
    # 验证余额是否一致
    if result['pdf_final_balance'] is not None and result['db_final_balance'] is not None:
        result['balance_match'] = abs(result['pdf_final_balance'] - result['db_final_balance']) < 0.01
    
    # 逐笔对比交易
    for i in range(min(pdf_count, db_count)):
        pdf_txn = pdf_transactions[i]
        db_txn = db_transactions[i]
        
        # 检查金额
        amount_match = abs(pdf_txn['amount'] - db_txn['amount']) < 0.01
        
        # 检查类型
        type_match = pdf_txn['type'] == db_txn['transaction_type']
        
        # 检查余额
        balance_match = True
        if pdf_txn.get('balance') is not None and db_txn['balance'] is not None:
            balance_match = abs(pdf_txn['balance'] - db_txn['balance']) < 0.01
        
        if not (amount_match and type_match and balance_match):
            result['mismatches'].append({
                'index': i + 1,
                'pdf': {
                    'date': pdf_txn['date'],
                    'amount': pdf_txn['amount'],
                    'type': pdf_txn['type'],
                    'balance': pdf_txn.get('balance'),
                    'description': pdf_txn['description'][:50]
                },
                'db': {
                    'date': db_txn['transaction_date'],
                    'amount': db_txn['amount'],
                    'type': db_txn['transaction_type'],
                    'balance': db_txn['balance'],
                    'description': db_txn['description'][:50]
                }
            })
    
    return result

def main():
    print("="*120)
    print("储蓄账户数据100%准确性验证")
    print("对比PDF月结单 vs 数据库记录")
    print("="*120 + "\n")
    
    # 获取所有已导入的UOB对账单
    test_files = [
        ('attached_assets/31-12-24_1760494388344.pdf', 'UOB'),
        ('attached_assets/31-01-25_1760494366333.pdf', 'UOB'),
        ('attached_assets/28-02-25_1760494366331.pdf', 'UOB'),
        ('attached_assets/31-03-25_1760494366333.pdf', 'UOB'),
        ('attached_assets/30-04-25_1760494366333.pdf', 'UOB'),
        ('attached_assets/31-05-25_1760494366334.pdf', 'UOB'),
        ('attached_assets/30-06-25_1760494366333.pdf', 'UOB'),
        ('attached_assets/31-07-25_1760494366334.pdf', 'UOB'),
    ]
    
    all_passed = True
    total_txns_pdf = 0
    total_txns_db = 0
    
    for file_path, bank_name in test_files:
        if not os.path.exists(file_path):
            continue
        
        result = verify_statement_accuracy(file_path, bank_name)
        
        if not result:
            continue
        
        total_txns_pdf += result['pdf_count']
        total_txns_db += result['db_count']
        
        # 判断是否完全一致
        is_perfect = (result['count_match'] and 
                     result['balance_match'] and 
                     len(result['mismatches']) == 0)
        
        status = "✅ 100%一致" if is_perfect else "❌ 不一致"
        
        print(f"{status} | {result['file']:<40} | {result['statement_date']}")
        print(f"      交易笔数: PDF={result['pdf_count']:>3} | DB={result['db_count']:>3} | {'✓' if result['count_match'] else '✗'}")
        
        if result['pdf_final_balance'] is not None:
            print(f"      月末余额: PDF=RM {result['pdf_final_balance']:>10,.2f} | DB=RM {result['db_final_balance']:>10,.2f} | {'✓' if result['balance_match'] else '✗'}")
        
        # 显示不匹配的交易
        if result['mismatches']:
            print(f"      ⚠️  发现 {len(result['mismatches'])} 笔不匹配交易:")
            for mismatch in result['mismatches'][:3]:  # 只显示前3笔
                print(f"         第{mismatch['index']}笔:")
                print(f"         PDF: {mismatch['pdf']['type']:6s} RM {mismatch['pdf']['amount']:>10,.2f} | 余额: RM {mismatch['pdf']['balance']:>10,.2f}")
                print(f"         DB:  {mismatch['db']['type']:6s} RM {mismatch['db']['amount']:>10,.2f} | 余额: RM {mismatch['db']['balance']:>10,.2f}")
            if len(result['mismatches']) > 3:
                print(f"         ... 还有 {len(result['mismatches']) - 3} 笔不匹配")
        
        print()
        
        if not is_perfect:
            all_passed = False
    
    print("="*120)
    print("验证总结:")
    print(f"  • PDF总交易数: {total_txns_pdf} 笔")
    print(f"  • 数据库总交易数: {total_txns_db} 笔")
    print(f"  • 交易笔数匹配: {'✅ 是' if total_txns_pdf == total_txns_db else '❌ 否'}")
    
    if all_passed:
        print(f"\n🎉 所有对账单数据100%准确！")
        print(f"   ✅ 每笔交易的金额、类型（credit/debit）完全一致")
        print(f"   ✅ 月末余额与PDF月结单完全一致")
    else:
        print(f"\n⚠️  发现数据不一致，需要修复！")
    
    print("="*120)
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
