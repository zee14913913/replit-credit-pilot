#!/usr/bin/env python3
"""
OCBC 2024年详细手动验证脚本
逐月逐笔显示PDF原件和数据库记录的完整对比
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from ingest.savings_parser import parse_ocbc_savings

# PDF文件映射（2024年1月-12月）
PDF_FILES = [
    ("attached_assets/JAN 2024_1761780571039.pdf", "2024-01-31", "Jan 2024"),
    ("attached_assets/FEB 2024_1761780571039.pdf", "2024-02-29", "Feb 2024"),
    ("attached_assets/MAR 2024_1761780571040.pdf", "2024-03-31", "Mar 2024"),
    ("attached_assets/APR 2024_1761780571038.pdf", "2024-04-30", "Apr 2024"),
    ("attached_assets/MAY 2024_1761780571040.pdf", "2024-05-31", "May 2024"),
    ("attached_assets/JUNE 2024_1761780571040.pdf", "2024-06-30", "Jun 2024"),
    ("attached_assets/JULY 2024_1761780571039.pdf", "2024-07-31", "Jul 2024"),
    ("attached_assets/AUG 2024_1761780571039.pdf", "2024-08-31", "Aug 2024"),
    ("attached_assets/SEP 2024_1761780571041.pdf", "2024-09-30", "Sep 2024"),
    ("attached_assets/OCT 2024_1761780571041.pdf", "2024-10-31", "Oct 2024"),
    ("attached_assets/NOV 2024_1761780571040.pdf", "2024-11-30", "Nov 2024"),
    ("attached_assets/DEC 2024_1761780571039.pdf", "2024-12-31", "Dec 2024"),
]

def manual_verify_month(pdf_path, statement_date, month_name, conn):
    """详细显示单个月份的PDF vs 数据库对比"""
    cursor = conn.cursor()
    
    print(f'\n{"="*120}')
    print(f'📅 手动验证: {month_name} ({statement_date})')
    print(f'{"="*120}')
    
    # 1. 解析PDF
    print(f'\n🔍 第一步: 从PDF原件提取交易记录...')
    try:
        statement_info, pdf_transactions = parse_ocbc_savings(pdf_path)
        print(f'   ✅ PDF文件: {pdf_path}')
        print(f'   ✅ 提取到 {len(pdf_transactions)} 笔交易')
    except Exception as e:
        print(f'   ❌ 解析失败: {e}')
        return
    
    # 2. 从数据库获取
    print(f'\n🔍 第二步: 从数据库提取交易记录...')
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
        print(f'   ❌ 数据库中找不到该月份的记录')
        return
    
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
    print(f'   ✅ 数据库中有 {len(db_transactions)} 笔交易')
    
    # 3. 显示交易数量对比
    print(f'\n📊 交易数量对比:')
    print(f'   PDF原件: {len(pdf_transactions)} 笔')
    print(f'   数据库:  {len(db_transactions)} 笔')
    
    if len(pdf_transactions) != len(db_transactions):
        print(f'   ❌ 数量不一致！差异: {abs(len(pdf_transactions) - len(db_transactions))} 笔')
        return
    else:
        print(f'   ✅ 数量一致')
    
    # 4. 如果该月没有交易，直接返回
    if len(pdf_transactions) == 0:
        print(f'\n✅ 该月无交易记录（空月结单），验证通过')
        return
    
    # 5. 逐笔详细对比
    print(f'\n{"="*120}')
    print(f'📋 逐笔详细对比（共 {len(pdf_transactions)} 笔）')
    print(f'{"="*120}')
    
    all_match = True
    
    for i, (pdf_txn, db_txn) in enumerate(zip(pdf_transactions, db_transactions), 1):
        pdf_date = pdf_txn['date']
        pdf_desc = pdf_txn['description']
        pdf_amount = pdf_txn['amount']
        pdf_type = pdf_txn['type']
        pdf_balance = pdf_txn['balance']
        
        db_date, db_desc, db_amount, db_type, db_balance = db_txn
        
        # 检查是否匹配
        date_match = (pdf_date == db_date)
        desc_match = (pdf_desc == db_desc)
        amount_match = (abs(pdf_amount - db_amount) < 0.01)
        type_match = (pdf_type == db_type)
        balance_match = (abs(pdf_balance - db_balance) < 0.01)
        
        is_match = date_match and desc_match and amount_match and type_match and balance_match
        
        print(f'\n第 {i} 笔交易:')
        print(f'{"─"*120}')
        
        # 显示PDF数据
        print(f'PDF原件:')
        print(f'  日期: {pdf_date}')
        print(f'  描述: {pdf_desc}')
        print(f'  金额: RM {pdf_amount:.2f}')
        print(f'  类型: {pdf_type}')
        print(f'  余额: RM {pdf_balance:.2f}')
        
        print(f'\n数据库:')
        print(f'  日期: {db_date}')
        print(f'  描述: {db_desc}')
        print(f'  金额: RM {db_amount:.2f}')
        print(f'  类型: {db_type}')
        print(f'  余额: RM {db_balance:.2f}')
        
        # 显示对比结果
        print(f'\n对比结果:')
        print(f'  日期: {"✅ 一致" if date_match else f"❌ 不一致 ({pdf_date} vs {db_date})"}')
        print(f'  描述: {"✅ 一致" if desc_match else "❌ 不一致"}')
        print(f'  金额: {"✅ 一致" if amount_match else f"❌ 不一致 ({pdf_amount} vs {db_amount})"}')
        print(f'  类型: {"✅ 一致" if type_match else f"❌ 不一致 ({pdf_type} vs {db_type})"}')
        print(f'  余额: {"✅ 一致" if balance_match else f"❌ 不一致 ({pdf_balance} vs {db_balance})"}')
        
        if is_match:
            print(f'  总结: ✅ 完全一致')
        else:
            print(f'  总结: ❌ 发现差异')
            all_match = False
    
    # 6. 最终结论
    print(f'\n{"="*120}')
    print(f'🎯 {month_name} 验证结论')
    print(f'{"="*120}')
    
    if all_match:
        print(f'✅ 所有 {len(pdf_transactions)} 笔交易完全一致！')
        print(f'✅ 零删除、零新增、零修改')
        print(f'✅ 数据准确率: 100%')
    else:
        print(f'❌ 发现数据不一致，需要修正')

def main():
    """主函数 - 逐月手动验证"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    
    print('='*120)
    print('🔍 OCBC 2024年详细手动验证系统')
    print('='*120)
    print(f'验证范围: 2024年1月-12月 (12个月)')
    print(f'验证方式: 逐月逐笔手动对比')
    print(f'验证标准: 100% 1:1匹配（日期、描述、金额、类型、余额）')
    print('='*120)
    
    # 逐月验证
    for pdf_path, statement_date, month_name in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f'\n❌ 文件不存在: {pdf_path}')
            continue
        
        manual_verify_month(pdf_path, statement_date, month_name, conn)
        
        # 每验证完一个月，暂停让人工检查
        print(f'\n{"─"*120}')
        print(f'按Enter继续验证下一个月...')
        input()
    
    conn.close()
    
    print('\n' + '='*120)
    print('✅ 所有12个月份手动验证完成')
    print('='*120)

if __name__ == '__main__':
    main()
