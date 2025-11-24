#!/usr/bin/env python3
"""
深度系统扫描 - 检查所有可能存在客户数据的地方
"""
import sqlite3
import os

def deep_scan():
    print("=" * 120)
    print("深度系统扫描 - 检查所有数据库表和文件")
    print("=" * 120)
    
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n检查 {len(all_tables)} 个数据库表...")
    print("-" * 120)
    
    # 检查每个表的记录数
    non_empty_tables = []
    for table in all_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                non_empty_tables.append((table, count))
        except Exception as e:
            pass
    
    if non_empty_tables:
        print(f"\n找到 {len(non_empty_tables)} 个非空表:")
        for table, count in sorted(non_empty_tables, key=lambda x: x[1], reverse=True):
            print(f"  {table:<40} {count:>8} 条记录")
            
            # 对于关键表，显示详细内容
            if table in ['customers', 'credit_cards', 'statements', 'monthly_statements', 'savings_accounts', 'loans']:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                if rows:
                    print(f"    示例数据: {rows[0][:5] if len(rows[0]) > 5 else rows[0]}")
    
    # 检查customers表详情
    print("\n" + "=" * 120)
    print("客户表详细检查")
    print("=" * 120)
    cursor.execute("SELECT id, name, email, customer_code, created_at FROM customers")
    customers = cursor.fetchall()
    print(f"客户总数: {len(customers)}")
    for cust in customers:
        print(f"  ID {cust[0]}: {cust[1]} | {cust[2]} | 客户编号: {cust[3]} | 创建于: {cust[4]}")
    
    # 检查credit_cards
    print("\n" + "=" * 120)
    print("信用卡表详细检查")
    print("=" * 120)
    cursor.execute("""
        SELECT cc.id, cc.bank_name, cc.card_number_last4, c.name, c.customer_code 
        FROM credit_cards cc 
        JOIN customers c ON cc.customer_id = c.id
    """)
    cards = cursor.fetchall()
    print(f"信用卡总数: {len(cards)}")
    for card in cards:
        print(f"  Card {card[0]}: {card[1]} ({card[2]}) | 客户: {card[3]} ({card[4]})")
    
    # 检查statements
    print("\n" + "=" * 120)
    print("对账单表详细检查")
    print("=" * 120)
    cursor.execute("""
        SELECT s.id, s.statement_date, s.file_path, cc.bank_name, c.name, c.customer_code
        FROM statements s
        JOIN credit_cards cc ON s.card_id = cc.id
        JOIN customers c ON cc.customer_id = c.id
    """)
    statements = cursor.fetchall()
    print(f"对账单总数: {len(statements)}")
    for stmt in statements:
        print(f"  Statement {stmt[0]}: {stmt[1]} | {stmt[3]} | 客户: {stmt[4]} ({stmt[5]})")
        if stmt[2]:
            file_exists = "✓ 存在" if os.path.exists(stmt[2]) else "✗ 不存在"
            print(f"    文件: {stmt[2]} [{file_exists}]")
    
    # 检查monthly_statements
    print("\n" + "=" * 120)
    print("月度对账单表详细检查")
    print("=" * 120)
    cursor.execute("""
        SELECT ms.id, ms.statement_month, ms.bank_name, c.name, c.customer_code
        FROM monthly_statements ms
        JOIN customers c ON ms.customer_id = c.id
    """)
    monthly_stmts = cursor.fetchall()
    print(f"月度对账单总数: {len(monthly_stmts)}")
    for mstmt in monthly_stmts:
        print(f"  Monthly Statement {mstmt[0]}: {mstmt[1]} | {mstmt[2]} | 客户: {mstmt[3]} ({mstmt[4]})")
    
    conn.close()
    
    print("\n" + "=" * 120)
    print("扫描完成")
    print("=" * 120)

if __name__ == '__main__':
    deep_scan()
