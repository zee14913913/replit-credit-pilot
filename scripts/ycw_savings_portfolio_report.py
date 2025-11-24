#!/usr/bin/env python3
"""
YEO CHEE WANG 储蓄账户完整投资组合报告
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3

def generate_portfolio_report():
    """生成储蓄账户完整投资组合报告"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    print('='*120)
    print('🏦 YEO CHEE WANG - 储蓄账户完整投资组合报告 (2024-2025)')
    print('='*120)
    
    # 客户基本信息
    cursor.execute('''
        SELECT name, customer_code, created_at
        FROM customers
        WHERE name = 'YEO CHEE WANG'
    ''')
    
    customer = cursor.fetchone()
    print(f'\n客户姓名: {customer[0]}')
    print(f'客户代码: {customer[1]}')
    print(f'账户创建: {customer[2]}')
    
    print('\n' + '='*120)
    print('📊 储蓄账户总览')
    print('='*120)
    
    # 获取所有储蓄账户
    cursor.execute('''
        SELECT 
            sa.bank_name,
            sa.account_number_last4,
            COUNT(DISTINCT ss.id) as statement_count,
            COUNT(st.id) as transaction_count,
            MIN(ss.statement_date) as earliest,
            MAX(ss.statement_date) as latest
        FROM savings_accounts sa
        LEFT JOIN savings_statements ss ON sa.id = ss.savings_account_id
        LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG'
        GROUP BY sa.id
        ORDER BY sa.bank_name
    ''')
    
    savings_accounts = cursor.fetchall()
    
    total_savings_statements = 0
    total_savings_transactions = 0
    
    print(f'\n{"银行":<20} {"账号后4位":<12} {"月结单数":<10} {"交易笔数":<10} {"覆盖期间":<30}')
    print('-'*120)
    
    for account in savings_accounts:
        bank, last4, stmt_count, txn_count, earliest, latest = account
        total_savings_statements += stmt_count
        total_savings_transactions += txn_count
        period = f'{earliest} ~ {latest}' if earliest and latest else 'N/A'
        print(f'{bank:<20} {last4:<12} {stmt_count:<10} {txn_count:<10} {period:<30}')
    
    print('-'*120)
    print(f'{"总计":<20} {len(savings_accounts):<12} {total_savings_statements:<10} {total_savings_transactions:<10}')
    
    # 储蓄账户详细统计
    print('\n📈 储蓄账户详细统计（按银行按年份）:')
    print('-'*120)
    
    for account in savings_accounts:
        bank, last4, _, _, _, _ = account
        
        print(f'\n🏦 {bank} (****{last4}):')
        
        # 按年份统计
        cursor.execute('''
            SELECT 
                strftime('%Y', ss.statement_date) as year,
                COUNT(DISTINCT ss.id) as month_count,
                COUNT(st.id) as txn_count
            FROM savings_accounts sa
            LEFT JOIN savings_statements ss ON sa.id = ss.savings_account_id
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
            JOIN customers c ON sa.customer_id = c.id
            WHERE c.name = 'YEO CHEE WANG'
              AND sa.bank_name = ?
              AND sa.account_number_last4 = ?
            GROUP BY year
            ORDER BY year
        ''', (bank, last4))
        
        yearly_stats = cursor.fetchall()
        
        for year_stat in yearly_stats:
            year, month_count, txn_count = year_stat
            if year:
                print(f'   {year}年: {month_count:>2} 个月, {txn_count:>4} 笔交易')
            else:
                print(f'   未知年份: {month_count:>2} 个月, {txn_count:>4} 笔交易')
    
    # 综合统计
    print('\n' + '='*120)
    print('📊 综合统计总览')
    print('='*120)
    
    print(f'\n储蓄账户:')
    print(f'   银行数量: {len(savings_accounts)} 家')
    print(f'   月结单总数: {total_savings_statements} 份')
    print(f'   交易总笔数: {total_savings_transactions} 笔')
    print(f'   平均每月: {total_savings_transactions / total_savings_statements:.1f} 笔' if total_savings_statements > 0 else '   平均每月: N/A')
    
    # 数据质量检查
    print('\n' + '='*120)
    print('✅ 数据质量检查')
    print('='*120)
    
    # 检查验证状态
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN verification_status = 'verified' THEN 1 ELSE 0 END) as verified
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG'
    ''')
    
    savings_verification = cursor.fetchone()
    
    print(f'\n验证状态:')
    print(f'   总月结单数: {savings_verification[0]}')
    print(f'   已验证: {savings_verification[1]}')
    verification_rate = (savings_verification[1]/savings_verification[0]*100) if savings_verification[0] > 0 else 0
    print(f'   验证率: {verification_rate:.1f}%')
    
    if savings_verification[1] == savings_verification[0]:
        print(f'   状态: ✅ 全部已验证')
    else:
        print(f'   状态: ⚠️  {savings_verification[0] - savings_verification[1]} 份待验证')
    
    # 检查重复记录
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT 
                sa.id,
                strftime('%Y-%m', ss.statement_date) AS month,
                COUNT(*) as count
            FROM savings_statements ss
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            JOIN customers c ON sa.customer_id = c.id
            WHERE c.name = 'YEO CHEE WANG'
            GROUP BY sa.id, month
            HAVING COUNT(*) > 1
        )
    ''')
    
    duplicate_count = cursor.fetchone()[0]
    
    print(f'\n重复记录检查:')
    if duplicate_count > 0:
        print(f'   ⚠️  发现 {duplicate_count} 个月份有重复记录')
    else:
        print(f'   ✅ 无重复记录')
    
    # 数据一致性检查
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT 
                ss.id,
                ss.total_transactions,
                COUNT(st.id) as actual_count
            FROM savings_statements ss
            LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            JOIN customers c ON sa.customer_id = c.id
            WHERE c.name = 'YEO CHEE WANG'
            GROUP BY ss.id
            HAVING ss.total_transactions != COUNT(st.id)
        )
    ''')
    
    mismatch_count = cursor.fetchone()[0]
    
    print(f'\n数据一致性:')
    if mismatch_count > 0:
        print(f'   ⚠️  发现 {mismatch_count} 个月份交易数不匹配')
    else:
        print(f'   ✅ 所有月份交易数一致')
    
    print('\n' + '='*120)
    print('✅ 报告生成完成')
    print('='*120)
    
    conn.close()

if __name__ == '__main__':
    generate_portfolio_report()
