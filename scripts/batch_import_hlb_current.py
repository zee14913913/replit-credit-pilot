#!/usr/bin/env python3
"""
HLB活期账户批量导入 - 正式导入脚本

功能：
1. 创建/获取客户记录（INFINITE GZ SDN. BHD.）
2. 创建/获取储蓄账户记录（HLB活期账户 #23600594645）
3. 批量导入16个月结单（2024年7月 - 2025年10月）
4. 使用事务性DB写入，失败自动回滚
5. 每个月结单导入后验证余额

作者：Smart Credit & Loan Manager
日期：2025-10-30
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pdfplumber
import re
import glob
from datetime import datetime
from ingest.savings_parser import apply_balance_change_algorithm
from db.database import get_db


def parse_hlb_current_account(file_path):
    """
    HLB活期账户解析器（与干运行版本相同）
    
    Returns:
        tuple: (info dict, transactions list)
    
    Raises:
        ValueError: 无法提取期初/期末余额时抛出
    """
    with pdfplumber.open(file_path) as pdf:
        full_text = ''
        for page in pdf.pages:
            full_text += page.extract_text() + '\n'
        
        lines = [l.strip() for l in full_text.split('\n') if l.strip()]
        
        info = {
            'bank_name': 'Hong Leong Bank',
            'bank_code': 'HLB',
            'account_number': None,
            'account_holder': None,
            'statement_date': None,
            'statement_period': None,
            'opening_balance': None,
            'closing_balance': None,
            'total_deposits_pdf': None,
            'total_withdrawals_pdf': None,
            'branch': None
        }
        
        for line in lines:
            if 'A/C No' in line:
                match = re.search(r'(\d{11})', line)
                if match:
                    info['account_number'] = match.group(1)
            
            if 'Date / Tarikh :' in line:
                match = re.search(r'(\d{2}-\d{2}-\d{4})', line)
                if match:
                    info['statement_date'] = match.group(1)
            
            if 'Statement Period' in line:
                match = re.search(r'(\d{2}/\d{2}/\d{2}\s*-\s*\d{2}/\d{2}/\d{2})', line)
                if match:
                    info['statement_period'] = match.group(1)
            
            if 'Branch / Cawangan :' in line:
                match = re.search(r':\s*(.+)', line)
                if match:
                    info['branch'] = match.group(1).strip()
            
            if lines[0] and not info['account_holder']:
                for i, l in enumerate(lines):
                    if 'INFINITE GZ SDN' in l:
                        info['account_holder'] = l.strip()
                        break
            
            if 'Balance from previous statement' in line:
                match = re.search(r'([\d,]*\.?\d+)$', line)
                if match:
                    bal_str = match.group(1).replace(',', '')
                    info['opening_balance'] = float(bal_str) if bal_str else 0.0
            
            if 'Total Deposits' in line and 'Closing Balance' in line:
                match = re.search(r'Closing Balance.*?([\d,]+\.\d{2})', line)
                if match:
                    info['closing_balance'] = float(match.group(1).replace(',', ''))
            
            if 'Total Deposits' in line:
                match = re.search(r'Total Deposits.*?:\s*\d+\s+([\d,]+\.\d{2})', line)
                if match:
                    info['total_deposits_pdf'] = float(match.group(1).replace(',', ''))
            
            if 'Total Withdrawals' in line:
                match = re.search(r'Total Withdrawals.*?:\s*\d+\s+([\d,]+\.\d{2})', line)
                if match:
                    info['total_withdrawals_pdf'] = float(match.group(1).replace(',', ''))
        
        if info['opening_balance'] is None:
            raise ValueError(f"无法提取期初余额 - PDF格式可能已变更")
        
        if info['closing_balance'] is None:
            raise ValueError(f"无法提取期末余额 - PDF格式可能已变更（检查'Total Deposits ... Closing Balance'行格式）")
        
        temp_transactions = []
        
        for i, line in enumerate(lines):
            if re.match(r'^\d{2}-\d{2}-\d{4}', line):
                if 'balance from previous' in line.lower() or 'balance c/f' in line.lower():
                    continue
                
                date_match = re.match(r'^(\d{2}-\d{2}-\d{4})', line)
                date_str = date_match.group(1)
                
                amounts = re.findall(r'([\d,]+\.\d{2})', line)
                
                if len(amounts) >= 1:
                    balance = float(amounts[-1].replace(',', ''))
                    
                    desc = line
                    desc = re.sub(r'^\d{2}-\d{2}-\d{4}\s+', '', desc)
                    desc = re.sub(r'[\d,]+\.\d{2}', '', desc)
                    desc = desc.strip()
                    
                    j = i + 1
                    while j < len(lines) and j < i + 6:
                        next_line = lines[j]
                        if re.match(r'^\d{2}-\d{2}-\d{4}', next_line):
                            break
                        if 'Total' in next_line:
                            break
                        if re.match(r'^[\d,\.]+$', next_line):
                            j += 1
                            continue
                        desc += ' ' + next_line
                        j += 1
                    
                    temp_transactions.append({
                        'date': date_str,
                        'description': desc.strip(),
                        'balance': balance,
                        'amount': 0,
                        'type': 'unknown'
                    })
        
        final_transactions = apply_balance_change_algorithm(temp_transactions, info['opening_balance'])
        
        return info, final_transactions


def get_or_create_customer(conn, customer_name):
    """
    获取或创建客户记录
    
    注意：不会commit，由调用者统一处理事务
    """
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
    """
    获取或创建储蓄账户记录
    
    注意：不会commit，由调用者统一处理事务
    """
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
    ''', (customer_id, bank_name, account_last4, 'Current Account', account_holder))
    
    account_id = cursor.lastrowid
    
    print(f"  ✓ 创建新储蓄账户 ID#{account_id}: {bank_name} #{account_number}")
    return account_id


def import_statement_with_transactions(conn, savings_account_id, file_path, info, transactions):
    """
    导入单个月结单及其所有交易记录
    
    注意：不会commit或rollback，由调用者统一处理事务
    
    Returns:
        int: statement_id
    
    Raises:
        Exception: 导入失败时抛出
    """
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO savings_statements (
            savings_account_id, statement_date, file_path, file_type,
            total_transactions, is_processed, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (savings_account_id, info['statement_date'], file_path, 'PDF', 
          len(transactions), 1))
    
    statement_id = cursor.lastrowid
    
    for txn in transactions:
        txn_date = datetime.strptime(txn['date'], '%d-%m-%Y').strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO savings_transactions (
                savings_statement_id, transaction_date, description,
                amount, transaction_type, balance, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (statement_id, txn_date, txn['description'], 
              txn['amount'], txn['type'], txn.get('balance')))
    
    return statement_id


def batch_import_statements(pdf_files):
    """
    批量导入所有月结单 - 使用单一事务确保原子性
    
    全有或全无：
    - 所有月结单成功 → 全部commit
    - 任何失败 → 全部rollback（包括客户和账户记录）
    
    Args:
        pdf_files: PDF文件路径列表
    
    Returns:
        bool: 是否全部成功
    """
    print("=" * 130)
    print("HLB活期账户批量导入 - 正式导入（单一事务模式）")
    print("INFINITE GZ SDN. BHD. | 账户 #23600594645 | 2024年7月 - 2025年10月")
    print("=" * 130)
    print()
    
    with get_db() as conn:
        try:
            print("步骤 1: 解析并验证所有PDF文件")
            print("-" * 130)
            
            parsed_data = []
            
            for idx, file_path in enumerate(sorted(pdf_files), 1):
                print(f"[{idx}/{len(pdf_files)}] 解析: {os.path.basename(file_path)}")
                
                info, transactions = parse_hlb_current_account(file_path)
                
                total_credit = sum(t['amount'] for t in transactions if t['type'] == 'credit')
                total_debit = sum(t['amount'] for t in transactions if t['type'] == 'debit')
                expected_closing = info['opening_balance'] + total_credit - total_debit
                
                balance_verified = abs(expected_closing - info['closing_balance']) < 0.01
                
                if not balance_verified:
                    diff = abs(expected_closing - info['closing_balance'])
                    raise ValueError(f"余额验证失败: {os.path.basename(file_path)} (差异: RM {diff:,.2f})")
                
                parsed_data.append({
                    'file_path': file_path,
                    'info': info,
                    'transactions': transactions
                })
                
                print(f"  ✓ {info['statement_date']} - {len(transactions)} 笔交易 - 余额验证通过")
            
            print(f"\n✅ 所有{len(pdf_files)}个PDF文件解析成功，余额验证100%通过")
            print()
            
            print("步骤 2: 创建/获取客户记录")
            print("-" * 130)
            customer_id = get_or_create_customer(conn, 'INFINITE GZ SDN. BHD.')
            print()
            
            print("步骤 3: 创建/获取储蓄账户记录")
            print("-" * 130)
            first_info = parsed_data[0]['info']
            savings_account_id = get_or_create_savings_account(
                conn, customer_id, first_info['bank_name'], 
                first_info['account_number'], first_info['account_holder']
            )
            print()
            
            print("步骤 4: 批量写入月结单及交易记录（事务中）")
            print("-" * 130)
            
            imported_statements = []
            total_transactions = 0
            
            for idx, data in enumerate(parsed_data, 1):
                file_path = data['file_path']
                info = data['info']
                transactions = data['transactions']
                
                print(f"[{idx}/{len(parsed_data)}] 导入: {os.path.basename(file_path)}")
                print(f"  账单日期: {info['statement_date']}")
                print(f"  期初余额: RM {info['opening_balance']:>12,.2f}")
                print(f"  期末余额: RM {info['closing_balance']:>12,.2f}")
                print(f"  交易数量: {len(transactions)} 笔")
                
                statement_id = import_statement_with_transactions(
                    conn, savings_account_id, file_path, info, transactions
                )
                
                imported_statements.append(statement_id)
                total_transactions += len(transactions)
                
                print(f"  ✅ 成功写入月结单 ID#{statement_id} ({len(transactions)} 笔交易)")
            
            conn.commit()
            
            print("\n" + "=" * 130)
            print("🎉 批量导入成功完成！")
            print("=" * 130)
            print(f"  已导入月结单: {len(imported_statements)} 个")
            print(f"  总交易记录: {total_transactions} 笔")
            print(f"  客户ID: {customer_id}")
            print(f"  储蓄账户ID: {savings_account_id}")
            print(f"  月结单ID范围: {min(imported_statements)} - {max(imported_statements)}")
            print("=" * 130)
            print("\n✅ 准备运行AutoVerifier v3.0进行全面验证")
            
            return True
            
        except Exception as e:
            import traceback
            conn.rollback()
            
            print("\n" + "=" * 130)
            print("❌ 批量导入失败 - 已回滚所有更改")
            print("=" * 130)
            print(f"错误: {e}")
            print("\n详细错误信息:")
            print(traceback.format_exc())
            print("=" * 130)
            print("\n没有任何数据被写入数据库（包括客户和账户记录）")
            
            return False


def main():
    """主函数"""
    pdf_dir = 'attached_assets'
    pdf_pattern = '05-*.pdf'
    
    pdf_files = sorted(glob.glob(os.path.join(pdf_dir, pdf_pattern)))
    
    if not pdf_files:
        print(f"❌ 未找到任何PDF文件: {os.path.join(pdf_dir, pdf_pattern)}")
        return False
    
    print(f"\n发现 {len(pdf_files)} 个HLB活期账户PDF文件")
    print(f"目录：{pdf_dir}")
    print(f"模式：{pdf_pattern}\n")
    
    confirm = input("确认开始批量导入？(输入 YES 继续): ")
    if confirm.strip().upper() != 'YES':
        print("取消导入")
        return False
    
    success = batch_import_statements(pdf_files)
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
