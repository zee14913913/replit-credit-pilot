#!/usr/bin/env python3
"""
Maybank 2025年100%准确性验证脚本
逐笔比对PDF原件与数据库记录，确保零删除、零新增、零修改
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from ingest.savings_parser import parse_maybank_savings

# PDF文件映射（2025年1月-9月）
PDF_FILES = [
    ("attached_assets/31-01-25_1761779697966.pdf", "2025-01-31", "Jan 2025"),
    ("attached_assets/28-02-25_1761779697965.pdf", "2025-02-28", "Feb 2025"),
    ("attached_assets/31-03-25_1761779697966.pdf", "2025-03-31", "Mar 2025"),
    ("attached_assets/30-04-25_1761779697965.pdf", "2025-04-30", "Apr 2025"),
    ("attached_assets/31-05-25_1761779697966.pdf", "2025-05-31", "May 2025"),
    ("attached_assets/30-06-25_1761779697965.pdf", "2025-06-30", "Jun 2025"),
    ("attached_assets/31-07-25_1761779697966.pdf", "2025-07-31", "Jul 2025"),
    ("attached_assets/31-08-2025_1761779697966.pdf", "2025-08-31", "Aug 2025"),
    ("attached_assets/30-09-2025_1761779697965.pdf", "2025-09-30", "Sep 2025"),
]

def verify_single_month(pdf_path, statement_date, month_name, conn):
    """对单个月份进行100%准确性验证"""
    cursor = conn.cursor()
    
    print(f'\n{"="*100}')
    print(f'🔍 验证: {month_name} ({statement_date})')
    print(f'{"="*100}')
    
    # 1. 解析PDF获取原始数据
    print(f'\n步骤1: 解析PDF原件...')
    try:
        statement_info, pdf_transactions = parse_maybank_savings(pdf_path)
        print(f'   ✅ PDF原件包含: {len(pdf_transactions)} 笔交易')
    except Exception as e:
        print(f'   ❌ 解析失败: {e}')
        return {
            'month': month_name,
            'status': 'ERROR',
            'error': str(e)
        }
    
    # 2. 从数据库获取该月份的记录
    print(f'\n步骤2: 从数据库获取记录...')
    cursor.execute('''
        SELECT ss.id, ss.total_transactions
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG'
          AND sa.bank_name = 'Maybank'
          AND ss.statement_date = ?
    ''', (statement_date,))
    
    stmt_record = cursor.fetchone()
    
    if not stmt_record:
        print(f'   ❌ 数据库中找不到该月份的记录')
        return {
            'month': month_name,
            'status': 'MISSING',
            'pdf_count': len(pdf_transactions),
            'db_count': 0
        }
    
    statement_id, db_total = stmt_record
    print(f'   ✅ 数据库记录ID: {statement_id}, 声明交易数: {db_total}')
    
    # 3. 获取数据库中的所有交易
    cursor.execute('''
        SELECT 
            transaction_date,
            description,
            amount,
            transaction_type,
            balance
        FROM savings_transactions
        WHERE savings_statement_id = ?
        ORDER BY id
    ''', (statement_id,))
    
    db_transactions = cursor.fetchall()
    print(f'   ✅ 数据库实际包含: {len(db_transactions)} 笔交易')
    
    # 4. 数量验证
    print(f'\n步骤3: 数量验证...')
    if len(pdf_transactions) != len(db_transactions):
        print(f'   ❌ 交易数量不一致!')
        print(f'      PDF原件: {len(pdf_transactions)} 笔')
        print(f'      数据库: {len(db_transactions)} 笔')
        print(f'      差异: {abs(len(pdf_transactions) - len(db_transactions))} 笔')
        return {
            'month': month_name,
            'status': 'COUNT_MISMATCH',
            'pdf_count': len(pdf_transactions),
            'db_count': len(db_transactions),
            'difference': abs(len(pdf_transactions) - len(db_transactions))
        }
    else:
        print(f'   ✅ 交易数量一致: {len(pdf_transactions)} 笔')
    
    # 5. 逐笔比对
    print(f'\n步骤4: 逐笔比对（1:1验证）...')
    
    mismatches = []
    
    for i, (pdf_txn, db_txn) in enumerate(zip(pdf_transactions, db_transactions)):
        pdf_date = pdf_txn['date']
        pdf_desc = pdf_txn['description']
        pdf_amount = pdf_txn['amount']
        pdf_type = pdf_txn['type']
        pdf_balance = pdf_txn['balance']
        
        db_date, db_desc, db_amount, db_type, db_balance = db_txn
        
        # 检查每个字段是否完全一致
        date_match = (pdf_date == db_date)
        desc_match = (pdf_desc == db_desc)
        amount_match = (abs(pdf_amount - db_amount) < 0.01)  # 浮点数比较
        type_match = (pdf_type == db_type)
        balance_match = (abs(pdf_balance - db_balance) < 0.01)  # 浮点数比较
        
        if not (date_match and desc_match and amount_match and type_match and balance_match):
            mismatch = {
                'index': i + 1,
                'pdf': {
                    'date': pdf_date,
                    'description': pdf_desc,
                    'amount': pdf_amount,
                    'type': pdf_type,
                    'balance': pdf_balance
                },
                'db': {
                    'date': db_date,
                    'description': db_desc,
                    'amount': db_amount,
                    'type': db_type,
                    'balance': db_balance
                },
                'issues': []
            }
            
            if not date_match:
                mismatch['issues'].append(f'日期不一致: {pdf_date} vs {db_date}')
            if not desc_match:
                mismatch['issues'].append(f'描述不一致')
            if not amount_match:
                mismatch['issues'].append(f'金额不一致: {pdf_amount} vs {db_amount}')
            if not type_match:
                mismatch['issues'].append(f'类型不一致: {pdf_type} vs {db_type}')
            if not balance_match:
                mismatch['issues'].append(f'余额不一致: {pdf_balance} vs {db_balance}')
            
            mismatches.append(mismatch)
    
    # 6. 输出验证结果
    if mismatches:
        print(f'   ❌ 发现 {len(mismatches)} 笔交易不一致:')
        for mm in mismatches[:5]:  # 只显示前5个不一致
            print(f'\n   第{mm["index"]}笔交易:')
            for issue in mm['issues']:
                print(f'      - {issue}')
        
        if len(mismatches) > 5:
            print(f'\n   ... 还有 {len(mismatches) - 5} 笔不一致（省略显示）')
        
        return {
            'month': month_name,
            'status': 'DATA_MISMATCH',
            'pdf_count': len(pdf_transactions),
            'db_count': len(db_transactions),
            'mismatches': len(mismatches),
            'mismatch_details': mismatches
        }
    else:
        print(f'   ✅ 所有 {len(pdf_transactions)} 笔交易完全一致!')
        print(f'   ✅ 零删除、零新增、零修改')
        
        return {
            'month': month_name,
            'status': 'PERFECT_MATCH',
            'pdf_count': len(pdf_transactions),
            'db_count': len(db_transactions),
            'verified_count': len(pdf_transactions)
        }

def main():
    """主函数 - 验证所有2025年月份"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    
    print('='*100)
    print('🔍 Maybank 2025年100%准确性验证系统')
    print('='*100)
    print(f'验证范围: 2025年1月-9月 (9个月)')
    print(f'验证标准: 100% 1:1比对（零删除、零新增、零修改）')
    print('='*100)
    
    results = []
    
    # 逐月验证
    for pdf_path, statement_date, month_name in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f'\n❌ 文件不存在: {pdf_path}')
            results.append({
                'month': month_name,
                'status': 'FILE_NOT_FOUND'
            })
            continue
        
        result = verify_single_month(pdf_path, statement_date, month_name, conn)
        results.append(result)
    
    conn.close()
    
    # 生成最终报告
    print('\n\n')
    print('='*100)
    print('📊 验证结果总览')
    print('='*100)
    
    perfect_matches = [r for r in results if r.get('status') == 'PERFECT_MATCH']
    count_mismatches = [r for r in results if r.get('status') == 'COUNT_MISMATCH']
    data_mismatches = [r for r in results if r.get('status') == 'DATA_MISMATCH']
    errors = [r for r in results if r.get('status') in ['ERROR', 'MISSING', 'FILE_NOT_FOUND']]
    
    print(f'\n✅ 完美匹配: {len(perfect_matches)} 个月')
    for r in perfect_matches:
        print(f'   {r["month"]}: {r["verified_count"]} 笔交易全部一致')
    
    if count_mismatches:
        print(f'\n⚠️  数量不一致: {len(count_mismatches)} 个月')
        for r in count_mismatches:
            print(f'   {r["month"]}: PDF={r["pdf_count"]} vs DB={r["db_count"]} (差异{r["difference"]}笔)')
    
    if data_mismatches:
        print(f'\n⚠️  数据不一致: {len(data_mismatches)} 个月')
        for r in data_mismatches:
            print(f'   {r["month"]}: {r["mismatches"]} 笔交易有差异')
    
    if errors:
        print(f'\n❌ 错误: {len(errors)} 个月')
        for r in errors:
            print(f'   {r["month"]}: {r["status"]}')
    
    # 最终结论
    print('\n' + '='*100)
    print('🎯 最终验证结论')
    print('='*100)
    
    total_verified_transactions = sum(r.get('verified_count', 0) for r in perfect_matches)
    
    if len(perfect_matches) == len(PDF_FILES):
        print(f'\n✅ 验证通过率: 100% ({len(perfect_matches)}/{len(PDF_FILES)} 个月)')
        print(f'✅ 验证交易总数: {total_verified_transactions} 笔')
        print(f'✅ 数据准确率: 100%')
        print(f'\n🎉 结论: 所有导入记录与PDF原件100%一致!')
        print(f'   - 零删除（无遗漏交易）')
        print(f'   - 零新增（无虚构交易）')
        print(f'   - 零修改（所有字段完全一致）')
    else:
        print(f'\n⚠️  验证通过率: {len(perfect_matches)/len(PDF_FILES)*100:.1f}% ({len(perfect_matches)}/{len(PDF_FILES)} 个月)')
        print(f'⚠️  验证交易总数: {total_verified_transactions} 笔')
        
        if count_mismatches or data_mismatches:
            print(f'\n⚠️  发现数据不一致，需要人工检查')
    
    print('='*100)

if __name__ == '__main__':
    main()
