#!/usr/bin/env python3
"""
Public Bank活期账户批量导入 - 正式导入脚本

功能：
1. 创建/获取客户记录（AI SMART TECH SDN. BHD.）
2. 创建/获取储蓄账户记录（Public Bank活期账户 #3824549009）
3. 批量导入7个月结单（2025年3月 - 2025年9月）
4. 使用事务性DB写入，失败自动回滚
5. 每个月结单导入后验证余额

作者：Smart Credit & Loan Manager
日期：2025-10-30
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from ingest.savings_parser import parse_savings_statement
from db.database import get_db


def get_or_create_customer(conn, customer_name):
    """获取或创建客户记录（不会commit，由调用者统一处理事务）"""
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM customers WHERE name = ?', (customer_name,))
    row = cursor.fetchone()
    
    if row:
        customer_id = row[0]
        print(f"  ✓ 找到现有客户记录 ID#{customer_id}: {customer_name}")
        return customer_id
    
    customer_code = f"CORP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    email = f"{customer_code.lower()}@company.local"
    
    cursor.execute('''
        INSERT INTO customers (
            customer_code, name, email, phone, monthly_income, created_at
        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (customer_code, customer_name, email, '', 0.0))
    
    customer_id = cursor.lastrowid
    
    print(f"  ✓ 创建新客户记录 ID#{customer_id}: {customer_name} (代码: {customer_code})")
    return customer_id


def get_or_create_savings_account(conn, customer_id, bank_name, account_number, account_holder):
    """获取或创建储蓄账户记录（不会commit，由调用者统一处理事务）"""
    cursor = conn.cursor()
    
    account_last4 = account_number[-4:] if account_number else '0000'
    
    cursor.execute('''
        SELECT id FROM savings_accounts 
        WHERE customer_id = ? AND bank_name = ? AND account_number_last4 = ?
    ''', (customer_id, bank_name, account_last4))
    row = cursor.fetchone()
    
    if row:
        account_id = row[0]
        print(f"  ✓ 找到现有储蓄账户 ID#{account_id}: {bank_name} ...{account_last4}")
        return account_id
    
    cursor.execute('''
        INSERT INTO savings_accounts (
            customer_id, bank_name, account_number_last4, 
            account_type, account_holder_name, created_at
        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (customer_id, bank_name, account_last4, 'RM Cm Current Account-i', account_holder))
    
    account_id = cursor.lastrowid
    
    print(f"  ✓ 创建新储蓄账户 ID#{account_id}: {bank_name} #{account_number}")
    return account_id


def import_statement_with_transactions(conn, savings_account_id, file_path, statement_info, transactions):
    """导入单个月结单及其所有交易记录（不会commit或rollback，由调用者统一处理事务）"""
    cursor = conn.cursor()
    
    # 转换日期格式：DD Mon YYYY → YYYY-MM-DD
    from datetime import datetime as dt
    statement_date_obj = dt.strptime(statement_info['statement_date'], '%d %b %Y')
    statement_date_db = statement_date_obj.strftime('%Y-%m-%d')
    
    cursor.execute('''
        INSERT INTO savings_statements (
            savings_account_id, statement_date, file_path, file_type,
            total_transactions, is_processed, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (savings_account_id, statement_date_db, file_path, 'PDF', 
          len(transactions), 1))
    
    statement_id = cursor.lastrowid
    
    for txn in transactions:
        # 转换交易日期格式：DD-MM-YYYY → YYYY-MM-DD
        txn_date_parts = txn['date'].split('-')
        txn_date_db = f"{txn_date_parts[2]}-{txn_date_parts[1]}-{txn_date_parts[0]}"
        
        cursor.execute('''
            INSERT INTO savings_transactions (
                savings_statement_id, transaction_date, description,
                amount, transaction_type, balance, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (statement_id, txn_date_db, txn['description'], 
              txn['amount'], txn['type'], txn.get('balance')))
    
    return statement_id


def batch_import_statements(pdf_files):
    """批量导入所有月结单 - 使用单一事务确保原子性"""
    print("=" * 130)
    print("Public Bank活期账户批量导入 - 正式导入（单一事务模式）")
    print("AI SMART TECH SDN. BHD. | 账户 #3824549009 | 2025年3月 - 2025年9月")
    print("=" * 130)
    print()
    
    with get_db() as conn:
        try:
            print("步骤 1: 解析并验证所有PDF文件")
            print("-" * 130)
            
            parsed_data = []
            
            for idx, file_path in enumerate(sorted(pdf_files), 1):
                print(f"[{idx}/{len(pdf_files)}] 解析: {os.path.basename(file_path)}")
                
                statement_info, transactions = parse_savings_statement(file_path, bank_name='Public Bank')
                
                # 计算期初期末余额并验证
                if transactions:
                    first_txn = transactions[0]
                    last_txn = transactions[-1]
                    
                    # 推算期初余额
                    if first_txn['type'] == 'credit':
                        opening_balance = first_txn['balance'] - first_txn['amount']
                    else:
                        opening_balance = first_txn['balance'] + first_txn['amount']
                    
                    closing_balance = last_txn['balance']
                    
                    # 计算总存入/提取
                    total_credit = sum(t['amount'] for t in transactions if t['type'] == 'credit')
                    total_debit = sum(t['amount'] for t in transactions if t['type'] == 'debit')
                    
                    # 验证：期初 + 存入 - 提取 = 期末
                    expected_closing = opening_balance + total_credit - total_debit
                    balance_verified = abs(expected_closing - closing_balance) < 0.01
                    
                    if not balance_verified:
                        diff = abs(expected_closing - closing_balance)
                        raise ValueError(f"余额验证失败: {os.path.basename(file_path)} (差异: RM {diff:,.2f})")
                    
                    parsed_data.append({
                        'file_path': file_path,
                        'statement_info': statement_info,
                        'transactions': transactions,
                        'opening_balance': opening_balance,
                        'closing_balance': closing_balance
                    })
                    
                    print(f"  ✓ {statement_info['statement_date']} - {len(transactions)} 笔交易 - 余额验证通过")
                else:
                    raise ValueError(f"无交易记录: {os.path.basename(file_path)}")
            
            print(f"\n✅ 所有{len(pdf_files)}个PDF文件解析成功，余额验证100%通过")
            print()
            
            print("步骤 2: 创建/获取客户记录")
            print("-" * 130)
            customer_id = get_or_create_customer(conn, 'AI SMART TECH SDN. BHD.')
            print()
            
            print("步骤 3: 创建/获取储蓄账户记录")
            print("-" * 130)
            savings_account_id = get_or_create_savings_account(
                conn, customer_id, 'Public Bank', 
                '3824549009', 'AI SMART TECH SDN. BHD.'
            )
            print()
            
            print("步骤 4: 批量导入月结单和交易（单一事务）")
            print("-" * 130)
            
            total_transactions = 0
            
            for idx, data in enumerate(parsed_data, 1):
                file_path = data['file_path']
                statement_info = data['statement_info']
                transactions = data['transactions']
                
                statement_id = import_statement_with_transactions(
                    conn, savings_account_id, file_path, 
                    statement_info, transactions
                )
                
                total_transactions += len(transactions)
                
                print(f"  [{idx}/{len(parsed_data)}] ✓ 月结单 #{statement_id}: {statement_info['statement_date']} "
                      f"({len(transactions)} 笔交易)")
            
            print()
            print("步骤 5: 提交事务")
            print("-" * 130)
            
            conn.commit()
            
            print("  ✓ 事务已成功提交到数据库")
            print()
            
            print("=" * 130)
            print("✅ 批量导入成功完成！")
            print("=" * 130)
            print()
            print(f"【导入汇总】")
            print(f"  客户: AI SMART TECH SDN. BHD.")
            print(f"  银行: Public Bank Malaysia Berhad")
            print(f"  账户: 3824549009 (RM Cm Current Account-i)")
            print(f"  月结单数: {len(parsed_data)}")
            print(f"  总交易数: {total_transactions}")
            print(f"  时间跨度: 2025年3月 - 2025年9月")
            print()
            
            return True
            
        except Exception as e:
            print()
            print("=" * 130)
            print("❌ 批量导入失败！正在回滚所有更改...")
            print("=" * 130)
            print(f"错误: {e}")
            print()
            import traceback
            traceback.print_exc()
            
            conn.rollback()
            print("  ✓ 事务已回滚，数据库未被修改")
            print()
            
            return False


def main():
    # PDF文件列表（按月份顺序）
    pdf_files = [
        'attached_assets/31:03:25_1761805099156.pdf',
        'attached_assets/30:04:25_1761805099156.pdf',
        'attached_assets/31:05:25_1761805099156.pdf',
        'attached_assets/30:06:25_1761805099156.pdf',
        'attached_assets/31:07:25_1761805099157.pdf',
        'attached_assets/30:08:25_1761805099156.pdf',
        'attached_assets/31:09:25_1761805099157.pdf',
    ]
    
    success = batch_import_statements(pdf_files)
    
    if success:
        print("✅ 导入任务成功完成！")
        return 0
    else:
        print("❌ 导入任务失败！")
        return 1


if __name__ == '__main__':
    sys.exit(main())
