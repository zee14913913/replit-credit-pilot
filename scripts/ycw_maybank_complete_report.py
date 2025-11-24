#!/usr/bin/env python3
"""
YEO CHEE WANG Maybank完整数据报告 (2024-2025)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3

def generate_complete_report():
    """生成完整的Maybank数据报告"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    print('='*120)
    print('📊 YEO CHEE WANG - MAYBANK ISLAMIC 完整数据集报告')
    print('='*120)
    
    # 基本信息
    cursor.execute('''
        SELECT 
            c.name,
            c.customer_code,
            sa.bank_name,
            sa.account_number_last4
        FROM savings_accounts sa
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' AND sa.bank_name = 'Maybank'
    ''')
    
    info = cursor.fetchone()
    print(f'\n客户姓名: {info[0]}')
    print(f'客户代码: {info[1]}')
    print(f'银行名称: {info[2]}')
    print(f'账号后4位: {info[3]}')
    print('='*120)
    
    # 2024年统计
    print('\n📅 2024年数据统计:')
    print('-'*120)
    
    cursor.execute('''
        SELECT 
            COUNT(DISTINCT ss.id) as month_count,
            SUM(ss.total_transactions) as total_txn,
            COUNT(st.id) as actual_txn
        FROM savings_statements ss
        LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' 
          AND sa.bank_name = 'Maybank'
          AND strftime('%Y', ss.statement_date) = '2024'
    ''')
    
    stats_2024 = cursor.fetchone()
    print(f'   月份数: {stats_2024[0]} 个月')
    print(f'   交易总数: {stats_2024[2]} 笔')
    
    # 显示2024年每月详情
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', ss.statement_date) AS month,
            ss.total_transactions,
            COUNT(st.id) AS actual_count,
            ss.verification_status
        FROM savings_statements ss
        LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' 
          AND sa.bank_name = 'Maybank'
          AND strftime('%Y', ss.statement_date) = '2024'
        GROUP BY ss.id
        ORDER BY ss.statement_date
    ''')
    
    records_2024 = cursor.fetchall()
    print(f'\n   详细列表:')
    for record in records_2024:
        print(f'   {record[0]}: {record[2]:>3} 笔交易 [{record[3]}]')
    
    # 2025年统计
    print('\n📅 2025年数据统计:')
    print('-'*120)
    
    cursor.execute('''
        SELECT 
            COUNT(DISTINCT ss.id) as month_count,
            SUM(ss.total_transactions) as total_txn,
            COUNT(st.id) as actual_txn
        FROM savings_statements ss
        LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' 
          AND sa.bank_name = 'Maybank'
          AND strftime('%Y', ss.statement_date) = '2025'
    ''')
    
    stats_2025 = cursor.fetchone()
    print(f'   月份数: {stats_2025[0]} 个月')
    print(f'   交易总数: {stats_2025[2]} 笔')
    
    # 显示2025年每月详情
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', ss.statement_date) AS month,
            ss.total_transactions,
            COUNT(st.id) AS actual_count,
            ss.verification_status
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
    
    records_2025 = cursor.fetchall()
    print(f'\n   详细列表:')
    for record in records_2025:
        print(f'   {record[0]}: {record[2]:>3} 笔交易 [{record[3]}]')
    
    # 总计统计
    print('\n📊 总计统计 (2024-2025):')
    print('='*120)
    
    total_months = stats_2024[0] + stats_2025[0]
    total_txn = stats_2024[2] + stats_2025[2]
    
    print(f'   总月份数: {total_months} 个月')
    print(f'   总交易数: {total_txn} 笔')
    print(f'   平均每月: {total_txn / total_months:.1f} 笔')
    
    # 覆盖期间
    cursor.execute('''
        SELECT 
            MIN(ss.statement_date) as earliest,
            MAX(ss.statement_date) as latest
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' 
          AND sa.bank_name = 'Maybank'
    ''')
    
    period = cursor.fetchone()
    print(f'   覆盖期间: {period[0]} 至 {period[1]}')
    
    # 验证状态
    print('\n🔍 验证状态:')
    print('-'*120)
    
    cursor.execute('''
        SELECT 
            verification_status,
            COUNT(*) as count
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' 
          AND sa.bank_name = 'Maybank'
        GROUP BY verification_status
    ''')
    
    status_stats = cursor.fetchall()
    for stat in status_stats:
        print(f'   {stat[0]}: {stat[1]} 个月')
    
    # 交易类型统计
    print('\n💰 交易类型统计:')
    print('-'*120)
    
    cursor.execute('''
        SELECT 
            st.transaction_type,
            COUNT(*) as count,
            SUM(st.amount) as total_amount
        FROM savings_transactions st
        JOIN savings_statements ss ON st.savings_statement_id = ss.id
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' 
          AND sa.bank_name = 'Maybank'
        GROUP BY st.transaction_type
    ''')
    
    txn_types = cursor.fetchall()
    for txn_type in txn_types:
        print(f'   {txn_type[0].upper()}: {txn_type[1]} 笔, 总额 RM {txn_type[2]:,.2f}')
    
    # 数据完整性检查
    print('\n✅ 数据完整性检查:')
    print('-'*120)
    
    # 检查是否有交易数不匹配
    cursor.execute('''
        SELECT 
            COUNT(*)
        FROM (
            SELECT 
                ss.id,
                ss.total_transactions,
                COUNT(st.id) as actual_count
            FROM savings_statements ss
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            JOIN customers c ON sa.customer_id = c.id
            WHERE c.name = 'YEO CHEE WANG' 
              AND sa.bank_name = 'Maybank'
            GROUP BY ss.id
            HAVING ss.total_transactions != COUNT(st.id)
        )
    ''')
    
    mismatch_count = cursor.fetchone()[0]
    
    if mismatch_count > 0:
        print(f'   ⚠️  发现 {mismatch_count} 个月份交易数不匹配')
    else:
        print(f'   ✅ 所有月份交易数一致')
    
    # 检查重复记录
    cursor.execute('''
        SELECT 
            COUNT(*)
        FROM (
            SELECT 
                strftime('%Y-%m', ss.statement_date) AS month,
                COUNT(*) as count
            FROM savings_statements ss
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            JOIN customers c ON sa.customer_id = c.id
            WHERE c.name = 'YEO CHEE WANG' 
              AND sa.bank_name = 'Maybank'
            GROUP BY month
            HAVING COUNT(*) > 1
        )
    ''')
    
    duplicate_count = cursor.fetchone()[0]
    
    if duplicate_count > 0:
        print(f'   ⚠️  发现 {duplicate_count} 个月份有重复记录')
    else:
        print(f'   ✅ 无重复月份记录')
    
    # 检查验证状态
    cursor.execute('''
        SELECT COUNT(*)
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG' 
          AND sa.bank_name = 'Maybank'
          AND verification_status != 'verified'
    ''')
    
    unverified_count = cursor.fetchone()[0]
    
    if unverified_count > 0:
        print(f'   ⚠️  {unverified_count} 个月份未验证')
    else:
        print(f'   ✅ 所有月份已验证')
    
    print('\n' + '='*120)
    print('✅ 报告生成完成')
    print('='*120)
    
    conn.close()

if __name__ == '__main__':
    generate_complete_report()
