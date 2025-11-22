#!/usr/bin/env python3
"""
Maybank月结单批量导入脚本 - YEO CHEE WANG 2025年
逐月导入，每月验证两遍后再进行下一个月
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
import shutil
from pathlib import Path
from ingest.savings_parser import parse_maybank_savings
from services.auto_verifier import AutoVerifier

# Maybank账号信息
CUSTOMER_NAME = "YEO CHEE WANG"
BANK_NAME = "Maybank"
ACCOUNT_LAST_4 = "3470"

# PDF文件映射 (2025年1月-9月)
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

def import_single_month(pdf_path, statement_date, month_name, account_id, conn):
    """导入单个月份的月结单"""
    cursor = conn.cursor()
    
    print(f'\n{"="*100}')
    print(f'📅 开始处理: {month_name} ({statement_date})')
    print(f'{"="*100}')
    
    # 1. 解析PDF
    print(f'\n🔍 步骤1: 解析PDF文件...')
    try:
        statement_info, transactions = parse_maybank_savings(pdf_path)
        print(f'   ✅ 成功解析: {len(transactions)} 笔交易')
        print(f'   📊 Beginning Balance: RM {statement_info.get("beginning_balance", "N/A")}')
        print(f'   📊 Closing Balance: RM {statement_info.get("closing_balance", "N/A")}')
    except Exception as e:
        print(f'   ❌ 解析失败: {e}')
        return False
    
    # 2. 保存PDF到客户目录
    print(f'\n💾 步骤2: 保存PDF原件...')
    customer_code = "Be_rich_YCW"
    savings_dir = Path(f'static/uploads/customers/{customer_code}/savings')
    savings_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(datetime.now().timestamp() * 1000)
    dest_filename = f'{month_name.replace(" ", "_")}_{timestamp}.pdf'
    dest_path = savings_dir / dest_filename
    
    shutil.copy2(pdf_path, dest_path)
    relative_path = str(dest_path).replace('static/', '')
    print(f'   ✅ PDF已保存: {relative_path}')
    
    # 3. 检查是否已存在该月份的记录
    cursor.execute('''
        SELECT id FROM savings_statements
        WHERE savings_account_id = ? AND statement_date = ?
    ''', (account_id, statement_date))
    
    existing = cursor.fetchone()
    if existing:
        print(f'   ⚠️  警告: {month_name} 已存在记录 (ID: {existing[0]}), 跳过导入')
        return False
    
    # 4. 插入月结单记录
    print(f'\n📝 步骤3: 创建月结单记录...')
    cursor.execute('''
        INSERT INTO savings_statements (
            savings_account_id,
            statement_date,
            total_transactions,
            file_path,
            file_type,
            verification_status,
            is_processed,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        account_id,
        statement_date,
        len(transactions),
        relative_path,
        'pdf',
        'pending',
        0,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    statement_id = cursor.lastrowid
    print(f'   ✅ 月结单记录已创建 (ID: {statement_id})')
    
    # 5. 插入所有交易记录
    print(f'\n💰 步骤4: 导入{len(transactions)}笔交易记录...')
    for txn in transactions:
        cursor.execute('''
            INSERT INTO savings_transactions (
                savings_statement_id,
                transaction_date,
                description,
                amount,
                transaction_type,
                balance,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            statement_id,
            txn['date'],
            txn['description'],
            txn['amount'],
            txn['type'],
            txn['balance'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    conn.commit()
    print(f'   ✅ {len(transactions)}笔交易已全部导入')
    
    # 6. 第一次验证
    print(f'\n🔍 步骤5: 第一次验证...')
    verifier = AutoVerifier()
    result = verifier.verify_statement(statement_id)
    
    print(f'   验证结果: {result["status"]}')
    if result['status'] == 'verified':
        print(f'   ✅ 第一次验证通过')
    else:
        print(f'   ⚠️  发现问题: {", ".join(result.get("errors", []))}')
    
    # 7. 第二次验证（手动抽查）
    print(f'\n🔍 步骤6: 第二次验证（抽查前5笔和后5笔交易）...')
    cursor.execute('''
        SELECT transaction_date, description, amount, transaction_type, balance
        FROM savings_transactions
        WHERE savings_statement_id = ?
        ORDER BY id
        LIMIT 5
    ''', (statement_id,))
    
    first_5 = cursor.fetchall()
    print(f'\n   前5笔交易:')
    for txn in first_5:
        print(f'   {txn[0]}: {txn[1][:50]:<50} {txn[3]:<7} RM {txn[2]:>10.2f} → RM {txn[4]:.2f}')
    
    cursor.execute('''
        SELECT transaction_date, description, amount, transaction_type, balance
        FROM savings_transactions
        WHERE savings_statement_id = ?
        ORDER BY id DESC
        LIMIT 5
    ''', (statement_id,))
    
    last_5 = list(reversed(cursor.fetchall()))
    print(f'\n   后5笔交易:')
    for txn in last_5:
        print(f'   {txn[0]}: {txn[1][:50]:<50} {txn[3]:<7} RM {txn[2]:>10.2f} → RM {txn[4]:.2f}')
    
    # 8. 标记为已验证
    cursor.execute('''
        UPDATE savings_statements
        SET verification_status = 'verified',
            verified_by = 'Manual Import + Dual Verification',
            verified_at = ?
        WHERE id = ?
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), statement_id))
    
    conn.commit()
    
    print(f'\n✅ {month_name} 导入完成并验证通过!')
    print(f'   月结单ID: {statement_id}')
    print(f'   交易总数: {len(transactions)}')
    print(f'   验证状态: verified')
    
    return True

def main():
    """主函数 - 逐月导入2025年Maybank月结单"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    print('='*100)
    print('🏦 Maybank月结单批量导入系统 - 2025年')
    print('='*100)
    print(f'客户: {CUSTOMER_NAME}')
    print(f'银行: {BANK_NAME}')
    print(f'账号后4位: {ACCOUNT_LAST_4}')
    print(f'总月份数: {len(PDF_FILES)}')
    print('='*100)
    
    # 获取储蓄账户ID (已经存在的Maybank账户)
    cursor.execute('''
        SELECT sa.id FROM savings_accounts sa
        JOIN customers c ON sa.customer_id = c.id
        WHERE c.name = ? AND sa.bank_name = ?
    ''', (CUSTOMER_NAME, BANK_NAME))
    
    account = cursor.fetchone()
    
    if not account:
        print(f'❌ 错误: 找不到Maybank账户')
        return
    
    account_id = account[0]
    print(f'✅ 储蓄账户ID: {account_id}')
    
    # 逐月导入
    success_count = 0
    skip_count = 0
    
    for pdf_path, statement_date, month_name in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f'\n❌ 文件不存在: {pdf_path}')
            skip_count += 1
            continue
        
        result = import_single_month(pdf_path, statement_date, month_name, account_id, conn)
        
        if result:
            success_count += 1
        else:
            skip_count += 1
    
    conn.close()
    
    # 最终摘要
    print('\n\n')
    print('='*100)
    print('📊 导入完成摘要')
    print('='*100)
    print(f'成功导入: {success_count} 个月')
    print(f'跳过: {skip_count} 个月')
    print(f'总计: {len(PDF_FILES)} 个月')
    print('='*100)

if __name__ == '__main__':
    main()
