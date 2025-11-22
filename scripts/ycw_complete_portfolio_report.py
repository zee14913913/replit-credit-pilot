#!/usr/bin/env python3
"""
YEO CHEE WANG 完整投资组合报告
包括所有银行的储蓄账户和信用卡数据
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3

def generate_portfolio_report():
    """生成完整投资组合报告"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    print('='*120)
    print('🏦 YEO CHEE WANG - 完整投资组合报告 (2024-2025)')
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
    print('\n📈 储蓄账户详细统计（按银行）:')
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
            GROUP BY year
            ORDER BY year
        ''', (bank,))
        
        yearly_stats = cursor.fetchall()
        
        for year_stat in yearly_stats:
            year, month_count, txn_count = year_stat
            print(f'   {year}年: {month_count} 个月, {txn_count} 笔交易')
    
    print('\n' + '='*120)
    print('💳 信用卡总览')
    print('='*120)
    
    # 获取所有信用卡
    cursor.execute('''
        SELECT 
            cc.bank_name,
            cc.card_number_last4,
            COUNT(DISTINCT ms.id) as statement_count,
            COUNT(t.id) as transaction_count,
            MIN(ms.statement_date) as earliest,
            MAX(ms.statement_date) as latest
        FROM credit_cards cc
        LEFT JOIN monthly_statements ms ON cc.id = ms.credit_card_id
        LEFT JOIN transactions t ON ms.id = t.monthly_statement_id
        JOIN customers c ON cc.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG'
        GROUP BY cc.id
        ORDER BY cc.bank_name
    ''')
    
    credit_cards = cursor.fetchall()
    
    total_cc_statements = 0
    total_cc_transactions = 0
    
    if credit_cards:
        print(f'\n{"银行":<20} {"卡号后4位":<12} {"月结单数":<10} {"交易笔数":<10} {"覆盖期间":<30}')
        print('-'*120)
        
        for card in credit_cards:
            bank, last4, stmt_count, txn_count, earliest, latest = card
            total_cc_statements += stmt_count
            total_cc_transactions += txn_count
            period = f'{earliest} ~ {latest}' if earliest and latest else 'N/A'
            print(f'{bank:<20} {last4:<12} {stmt_count:<10} {txn_count:<10} {period:<30}')
        
        print('-'*120)
        print(f'{"总计":<20} {len(credit_cards):<12} {total_cc_statements:<10} {total_cc_transactions:<10}')
        
        # 信用卡详细统计
        print('\n📈 信用卡详细统计（按银行）:')
        print('-'*120)
        
        for card in credit_cards:
            bank, last4, _, _, _, _ = card
            
            print(f'\n💳 {bank} (****{last4}):')
            
            # 按年份统计
            cursor.execute('''
                SELECT 
                    strftime('%Y', ms.statement_date) as year,
                    COUNT(DISTINCT ms.id) as month_count,
                    COUNT(t.id) as txn_count
                FROM credit_cards cc
                LEFT JOIN monthly_statements ms ON cc.id = ms.credit_card_id
                LEFT JOIN transactions t ON ms.id = t.monthly_statement_id
                JOIN customers c ON cc.customer_id = c.id
                WHERE c.name = 'YEO CHEE WANG'
                  AND cc.bank_name = ?
                  AND cc.card_number_last4 = ?
                GROUP BY year
                ORDER BY year
            ''', (bank, last4))
            
            yearly_stats = cursor.fetchall()
            
            for year_stat in yearly_stats:
                year, month_count, txn_count = year_stat
                print(f'   {year}年: {month_count} 个月, {txn_count} 笔交易')
    else:
        print('\n   (暂无信用卡数据)')
    
    print('\n' + '='*120)
    print('📊 综合统计总览')
    print('='*120)
    
    print(f'\n储蓄账户:')
    print(f'   银行数量: {len(savings_accounts)} 家')
    print(f'   月结单总数: {total_savings_statements} 份')
    print(f'   交易总笔数: {total_savings_transactions} 笔')
    
    if credit_cards:
        print(f'\n信用卡:')
        print(f'   信用卡数量: {len(credit_cards)} 张')
        print(f'   月结单总数: {total_cc_statements} 份')
        print(f'   交易总笔数: {total_cc_transactions} 笔')
    
    print(f'\n总计:')
    total_statements = total_savings_statements + total_cc_statements
    total_transactions = total_savings_transactions + total_cc_transactions
    print(f'   月结单总数: {total_statements} 份')
    print(f'   交易总笔数: {total_transactions} 笔')
    
    # 数据质量检查
    print('\n' + '='*120)
    print('✅ 数据质量检查')
    print('='*120)
    
    # 检查储蓄账户验证状态
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
    
    print(f'\n储蓄账户验证状态:')
    print(f'   总月结单数: {savings_verification[0]}')
    print(f'   已验证: {savings_verification[1]}')
    print(f'   验证率: {(savings_verification[1]/savings_verification[0]*100) if savings_verification[0] > 0 else 0:.1f}%')
    
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
    
    print('\n' + '='*120)
    print('✅ 报告生成完成')
    print('='*120)
    
    conn.close()

if __name__ == '__main__':
    generate_portfolio_report()
