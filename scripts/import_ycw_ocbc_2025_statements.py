#!/usr/bin/env python3
"""
YEO CHEE WANG - OCBC 2025年储蓄账户月结单导入脚本
导入范围: 2025年1月-7月（7个月）
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
from ingest.savings_parser import parse_ocbc_savings

# PDF文件映射（2025年1月-7月）
PDF_FILES = [
    ("attached_assets/JAN 2025_1761777193753.pdf", "2025-01-31", "Jan 2025"),
    ("attached_assets/FEB 2025_1761777193753.pdf", "2025-02-28", "Feb 2025"),
    ("attached_assets/MAR 2025_1761777193753.pdf", "2025-03-31", "Mar 2025"),
    ("attached_assets/APR 2025_1761777193753.pdf", "2025-04-30", "Apr 2025"),
    ("attached_assets/MAY 2025_1761777193754.pdf", "2025-05-31", "May 2025"),
    ("attached_assets/JUNE 2025_1761777193753.pdf", "2025-06-30", "Jun 2025"),
    ("attached_assets/JULY 2025_1761777193753.pdf", "2025-07-31", "Jul 2025"),
]

def import_ocbc_statement(pdf_path, statement_date, month_name, conn):
    """导入单个月份的OCBC储蓄账户月结单"""
    cursor = conn.cursor()
    
    print(f'\n{"="*100}')
    print(f'📅 导入: {month_name} ({statement_date})')
    print(f'{"="*100}')
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f'❌ 文件不存在: {pdf_path}')
        return False
    
    # 1. 解析PDF
    print(f'\n🔍 步骤1: 解析PDF文件...')
    try:
        statement_info, transactions = parse_ocbc_savings(pdf_path)
        print(f'   ✅ 成功解析: {len(transactions)} 笔交易')
        print(f'   📄 账号: {statement_info.get("account_number", "N/A")}')
        print(f'   💰 期初余额: RM {statement_info.get("opening_balance", 0):.2f}')
        print(f'   💰 期末余额: RM {statement_info.get("closing_balance", 0):.2f}')
    except Exception as e:
        print(f'   ❌ 解析失败: {e}')
        return False
    
    # 2. 检查是否已导入
    cursor.execute('''
        SELECT ss.id
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = 'YEO CHEE WANG'
          AND sa.bank_name = 'OCBC'
          AND ss.statement_date = ?
    ''', (statement_date,))
    
    existing = cursor.fetchone()
    if existing:
        print(f'   ⚠️  该月份已存在，跳过导入')
        return False
    
    # 3. 获取客户ID
    cursor.execute("SELECT id FROM customers WHERE name = 'YEO CHEE WANG'")
    customer = cursor.fetchone()
    
    if not customer:
        print(f'   ❌ 客户不存在: YEO CHEE WANG')
        return False
    
    customer_id = customer[0]
    
    # 4. 获取或创建储蓄账户
    print(f'\n🔍 步骤2: 获取储蓄账户...')
    cursor.execute('''
        SELECT id FROM savings_accounts
        WHERE customer_id = ? AND bank_name = 'OCBC'
    ''', (customer_id,))
    
    account = cursor.fetchone()
    
    if account:
        savings_account_id = account[0]
        print(f'   ✅ 找到现有账户 ID: {savings_account_id}')
    else:
        cursor.execute('''
            INSERT INTO savings_accounts (customer_id, bank_name, account_number, account_type)
            VALUES (?, 'OCBC', ?, 'Savings Account')
        ''', (customer_id, statement_info.get('account_number', 'Unknown')))
        savings_account_id = cursor.lastrowid
        print(f'   ✅ 创建新账户 ID: {savings_account_id}')
    
    # 5. 生成目标文件路径
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    month_year = datetime.strptime(statement_date, '%Y-%m-%d').strftime('%B_%Y')
    destination_filename = f"{month_year}_{timestamp}.pdf"
    destination_path = f"static/uploads/customers/Be_rich_YCW/savings/{destination_filename}"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    
    # 复制文件
    import shutil
    shutil.copy2(pdf_path, destination_path)
    print(f'   ✅ 文件已复制到: {destination_path}')
    
    # 6. 插入月结单记录
    print(f'\n🔍 步骤3: 插入月结单记录...')
    cursor.execute('''
        INSERT INTO savings_statements (
            savings_account_id,
            statement_date,
            opening_balance,
            closing_balance,
            total_deposits,
            total_withdrawals,
            transaction_count,
            file_path,
            upload_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        savings_account_id,
        statement_date,
        statement_info.get('opening_balance', 0),
        statement_info.get('closing_balance', 0),
        statement_info.get('total_deposits', 0),
        statement_info.get('total_withdrawals', 0),
        len(transactions),
        destination_path,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    statement_id = cursor.lastrowid
    print(f'   ✅ 月结单记录已创建 ID: {statement_id}')
    
    # 7. 插入交易记录
    print(f'\n🔍 步骤4: 插入交易记录...')
    for txn in transactions:
        cursor.execute('''
            INSERT INTO savings_transactions (
                savings_statement_id,
                transaction_date,
                description,
                amount,
                transaction_type,
                balance
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            statement_id,
            txn['date'],
            txn['description'],
            txn['amount'],
            txn['type'],
            txn['balance']
        ))
    
    print(f'   ✅ 成功插入 {len(transactions)} 笔交易')
    
    conn.commit()
    
    print(f'\n✅ {month_name} 导入完成！')
    return True

def main():
    """主函数 - 批量导入OCBC 2025年1-7月月结单"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    conn.row_factory = sqlite3.Row
    
    print('='*100)
    print('🏦 OCBC 2025年储蓄账户月结单导入系统')
    print('='*100)
    print(f'客户: YEO CHEE WANG')
    print(f'银行: OCBC')
    print(f'范围: 2025年1月-7月 (7个月)')
    print('='*100)
    
    imported_count = 0
    skipped_count = 0
    failed_count = 0
    
    # 逐月导入
    for pdf_path, statement_date, month_name in PDF_FILES:
        result = import_ocbc_statement(pdf_path, statement_date, month_name, conn)
        
        if result:
            imported_count += 1
        elif result is False and os.path.exists(pdf_path):
            skipped_count += 1
        else:
            failed_count += 1
    
    conn.close()
    
    # 最终摘要
    print('\n' + '='*100)
    print('📊 导入摘要')
    print('='*100)
    print(f'✅ 成功导入: {imported_count} 个月')
    print(f'⚠️  已存在跳过: {skipped_count} 个月')
    print(f'❌ 导入失败: {failed_count} 个月')
    print(f'📁 总计: {len(PDF_FILES)} 个月')
    print('='*100)
    
    if imported_count > 0:
        print(f'\n🎉 成功导入 {imported_count} 个月的数据！')
        print(f'💡 下一步: 运行验证脚本确认数据准确性')

if __name__ == '__main__':
    main()
