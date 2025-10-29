#!/usr/bin/env python3
"""
标记账单为已验证
仅在完成双重人工验证后使用
"""

import sys
import sqlite3
from datetime import datetime

def mark_verified(statement_id: int):
    """将账单标记为已验证"""
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            ss.id,
            ss.verification_status,
            sa.bank_name,
            sa.account_number_last4,
            c.name as customer_name
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        JOIN customers c ON sa.customer_id = c.id
        WHERE ss.id = ?
    ''', (statement_id,))
    
    stmt = cursor.fetchone()
    
    if not stmt:
        print(f"❌ 找不到账单ID: {statement_id}")
        conn.close()
        return False
    
    print("=" * 80)
    print(f"📌 标记账单为已验证")
    print("=" * 80)
    print()
    print(f"账单ID:      {stmt[0]}")
    print(f"客户:        {stmt[4]}")
    print(f"银行账户:    {stmt[2]} ****{stmt[3]}")
    print(f"当前状态:    {stmt[1]}")
    print()
    
    confirmation = input("⚠️  确认已完成双重人工验证？(输入 YES 确认): ")
    
    if confirmation.strip().upper() != 'YES':
        print("❌ 取消操作")
        conn.close()
        return False
    
    cursor.execute('''
        UPDATE savings_statements 
        SET verification_status = 'verified',
            verified_at = ?
        WHERE id = ?
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), statement_id))
    
    conn.commit()
    
    print()
    print("✅ 账单已标记为 verified")
    print(f"✅ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("=" * 80)
    
    conn.close()
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 scripts/mark_statement_verified.py <statement_id>")
        print()
        print("示例: python3 scripts/mark_statement_verified.py 207")
        sys.exit(1)
    
    statement_id = int(sys.argv[1])
    mark_verified(statement_id)
