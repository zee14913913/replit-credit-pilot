#!/usr/bin/env python3
"""
OCBC 2025年详细验证脚本
逐月逐笔验证PDF原件 vs 数据库记录
确保100%数据准确性
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from ingest.savings_parser import parse_ocbc_savings

# PDF文件映射（2025年1月-7月）
PDF_FILES = [
    ("attached_assets/JAN 2025_1761786693412.pdf", "2025-01-31", "Jan 2025"),
    ("attached_assets/FEB 2025_1761786702834.pdf", "2025-02-28", "Feb 2025"),
    ("attached_assets/MAR 2025(1)_1761786707839.pdf", "2025-03-31", "Mar 2025"),
    ("attached_assets/APR 2025_1761786712694.pdf", "2025-04-30", "Apr 2025"),
    ("attached_assets/MAY 2025_1761786719877.pdf", "2025-05-31", "May 2025"),
    ("attached_assets/JUNE 2025_1761786726743.pdf", "2025-06-30", "Jun 2025"),
    ("attached_assets/JULY 2025_1761786731224.pdf", "2025-07-31", "Jul 2025"),
]

def verify_month(pdf_path, statement_date, month_name, conn):
    """验证单个月份的数据准确性"""
    cursor = conn.cursor()
    
    print(f'\n{"="*100}')
    print(f'📅 验证: {month_name} ({statement_date})')
    print(f'{"="*100}')
    
    # 1. 解析PDF
    print(f'\n🔍 步骤1: 从PDF提取交易...')
    try:
        statement_info, pdf_transactions = parse_ocbc_savings(pdf_path)
        print(f'   ✅ PDF提取: {len(pdf_transactions)} 笔交易')
    except Exception as e:
        print(f'   ❌ PDF解析失败: {e}')
        return False
    
    # 2. 从数据库获取
    print(f'\n🔍 步骤2: 从数据库提取交易...')
    cursor.execute('''
        SELECT ss.id
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG'
          AND sa.bank_name = 'OCBC'
          AND ss.statement_date = ?
    ''', (statement_date,))
    
    stmt_record = cursor.fetchone()
    
    if not stmt_record:
        print(f'   ❌ 数据库中找不到该月份')
        return False
    
    statement_id = stmt_record[0]
    
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
    print(f'   ✅ 数据库提取: {len(db_transactions)} 笔交易')
    
    # 3. 数量对比
    print(f'\n📊 交易数量对比:')
    print(f'   PDF原件: {len(pdf_transactions)} 笔')
    print(f'   数据库:  {len(db_transactions)} 笔')
    
    if len(pdf_transactions) != len(db_transactions):
        print(f'   ❌ 数量不一致！')
        return False
    
    if len(pdf_transactions) == 0:
        print(f'   ℹ️  该月无交易（空月结单）')
        return True
    
    # 4. 逐笔对比
    print(f'\n{"─"*100}')
    print(f'📋 逐笔详细对比')
    print(f'{"─"*100}')
    
    all_match = True
    
    for i, (pdf_txn, db_txn) in enumerate(zip(pdf_transactions, db_transactions), 1):
        pdf_date = pdf_txn['date']
        pdf_desc = pdf_txn['description']
        pdf_amount = pdf_txn['amount']
        pdf_type = pdf_txn['type']
        pdf_balance = pdf_txn['balance']
        
        db_date, db_desc, db_amount, db_type, db_balance = db_txn
        
        # 检查匹配
        date_match = (pdf_date == db_date)
        desc_match = (pdf_desc == db_desc)
        amount_match = (abs(pdf_amount - db_amount) < 0.01)
        type_match = (pdf_type == db_type)
        balance_match = (abs(pdf_balance - db_balance) < 0.01)
        
        is_match = date_match and desc_match and amount_match and type_match and balance_match
        
        if is_match:
            print(f'第{i:2}笔: ✅ 一致 | {pdf_date} | {pdf_desc[:50]:50} | RM {pdf_amount:10.2f} | {pdf_balance:10.2f}')
        else:
            print(f'第{i:2}笔: ❌ 不一致')
            print(f'  PDF:  {pdf_date} | {pdf_desc[:50]:50} | RM {pdf_amount:10.2f} | {pdf_type:6} | {pdf_balance:10.2f}')
            print(f'  DB:   {db_date} | {db_desc[:50]:50} | RM {db_amount:10.2f} | {db_type:6} | {db_balance:10.2f}')
            all_match = False
    
    # 5. 结论
    print(f'\n{"="*100}')
    if all_match:
        print(f'✅ {month_name} 验证通过 - 所有{len(pdf_transactions)}笔交易100%一致！')
    else:
        print(f'❌ {month_name} 验证失败 - 发现数据不一致')
    print(f'{"="*100}')
    
    return all_match

def main():
    """主函数 - 验证所有月份"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    
    print('='*100)
    print('🔍 OCBC 2025年储蓄账户数据验证系统')
    print('='*100)
    print(f'客户: YEO CHEE WANG')
    print(f'银行: OCBC Bank')
    print(f'范围: 2025年1月-7月 (7个月)')
    print(f'验证标准: 100% 1:1匹配（日期、描述、金额、类型、余额）')
    print('='*100)
    
    verified_count = 0
    failed_count = 0
    total_transactions = 0
    
    # 逐月验证
    for pdf_path, statement_date, month_name in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f'\n❌ 文件不存在: {pdf_path}')
            failed_count += 1
            continue
        
        result = verify_month(pdf_path, statement_date, month_name, conn)
        
        if result:
            verified_count += 1
            # 计算总交易数
            statement_info, transactions = parse_ocbc_savings(pdf_path)
            total_transactions += len(transactions)
        else:
            failed_count += 1
    
    conn.close()
    
    # 最终总结
    print('\n' + '='*100)
    print('📊 验证总结')
    print('='*100)
    print(f'✅ 验证通过: {verified_count}/{len(PDF_FILES)} 个月')
    print(f'❌ 验证失败: {failed_count}/{len(PDF_FILES)} 个月')
    print(f'📝 总交易数: {total_transactions} 笔')
    print('='*100)
    
    if verified_count == len(PDF_FILES):
        print(f'\n🎉 所有{len(PDF_FILES)}个月份100%验证通过！')
        print(f'✅ 零删除、零新增、零修改')
        print(f'✅ 数据准确率: 100%')
    else:
        print(f'\n⚠️  部分月份验证失败，需要检查')
    
    print('='*100)

if __name__ == '__main__':
    main()
