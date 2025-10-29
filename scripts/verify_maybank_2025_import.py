#!/usr/bin/env python3
"""
验证Maybank 2025年导入情况
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3

def verify_import():
    """验证2025年Maybank导入"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    print('='*100)
    print('📊 Maybank 2025年导入验证报告')
    print('='*100)
    print('\n客户: YEO CHEE WANG')
    print('银行: Maybank')
    print('年份: 2025')
    print('='*100)
    
    # 查询2025年所有月结单
    cursor.execute('''
        SELECT 
            ss.id,
            strftime('%Y-%m', ss.statement_date) AS month,
            ss.statement_date,
            ss.total_transactions,
            COUNT(st.id) AS actual_count,
            ss.verification_status,
            ss.verified_by,
            ss.file_path
        FROM savings_statements ss
        LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' 
          AND sa.bank_name = 'Maybank'
          AND strftime('%Y', ss.statement_date) = '2025'
        GROUP BY ss.id
        ORDER BY ss.statement_date
    ''')
    
    records = cursor.fetchall()
    
    if not records:
        print('\n❌ 未找到2025年的记录')
        return
    
    print(f'\n✅ 找到 {len(records)} 个月份的记录\n')
    
    total_transactions = 0
    
    # 表头
    print(f'{"月份":<12} {"月结单ID":<10} {"交易笔数":<10} {"实际交易":<10} {"验证状态":<15} {"验证者":<40}')
    print('-'*100)
    
    for record in records:
        stmt_id, month, stmt_date, total_txn, actual_count, status, verified_by, file_path = record
        print(f'{month:<12} {stmt_id:<10} {total_txn:<10} {actual_count:<10} {status:<15} {verified_by or "N/A":<40}')
        total_transactions += actual_count
    
    print('-'*100)
    print(f'{"总计":<12} {len(records):<10} {"":<10} {total_transactions:<10}')
    print('='*100)
    
    # 检查数据一致性
    print('\n🔍 数据一致性检查:')
    
    issues = []
    for record in records:
        stmt_id, month, stmt_date, total_txn, actual_count, status, verified_by, file_path = record
        
        if total_txn != actual_count:
            issues.append(f'  ⚠️  {month}: 声明交易数({total_txn}) ≠ 实际交易数({actual_count})')
        
        if status != 'verified':
            issues.append(f'  ⚠️  {month}: 验证状态为 {status}')
    
    if issues:
        print('\n发现以下问题:')
        for issue in issues:
            print(issue)
    else:
        print('   ✅ 所有记录数据一致，验证状态正常')
    
    # 显示每月交易详情
    print('\n📈 每月交易详细统计:')
    print(f'{"月份":<12} {"交易笔数":<10} {"借方笔数":<10} {"贷方笔数":<10}')
    print('-'*50)
    
    for record in records:
        stmt_id = record[0]
        month = record[1]
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN transaction_type = 'debit' THEN 1 ELSE 0 END) as debit_count,
                SUM(CASE WHEN transaction_type = 'credit' THEN 1 ELSE 0 END) as credit_count
            FROM savings_transactions
            WHERE savings_statement_id = ?
        ''', (stmt_id,))
        
        stat = cursor.fetchone()
        print(f'{month:<12} {stat[0]:<10} {stat[1]:<10} {stat[2]:<10}')
    
    print('='*100)
    
    # 检查是否有重复记录
    print('\n🔍 检查重复记录:')
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', ss.statement_date) AS month,
            COUNT(*) AS count
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' 
          AND sa.bank_name = 'Maybank'
          AND strftime('%Y', ss.statement_date) = '2025'
        GROUP BY month
        HAVING COUNT(*) > 1
    ''')
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print('   ⚠️  发现重复月份:')
        for dup in duplicates:
            print(f'      {dup[0]}: {dup[1]} 条记录')
    else:
        print('   ✅ 无重复记录')
    
    print('\n' + '='*100)
    print('✅ 验证完成')
    print('='*100)
    
    conn.close()

if __name__ == '__main__':
    verify_import()
