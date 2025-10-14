#!/usr/bin/env python3
"""
View Monthly Ledger - 查看客户的月度账本
"""
import sqlite3
import sys

def view_customer_ledger(customer_id: int = None):
    """查看客户的月度账本"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    if not customer_id:
        # 列出所有客户
        cursor.execute("""
            SELECT DISTINCT c.customer_id, cu.name
            FROM credit_cards c
            JOIN customers cu ON c.customer_id = cu.id
            JOIN monthly_ledger ml ON ml.customer_id = c.customer_id
            ORDER BY cu.name
        """)
        customers = cursor.fetchall()
        
        print("\n=== 有月度账本的客户 ===")
        for cid, name in customers:
            print(f"  [{cid}] {name}")
        
        print("\n用法: python view_monthly_ledger.py <customer_id>")
        print("示例: python view_monthly_ledger.py 5")
        conn.close()
        return
    
    # 获取客户信息
    cursor.execute("SELECT name, email FROM customers WHERE id = ?", (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        print(f"❌ Customer ID {customer_id} not found")
        conn.close()
        return
    
    customer_name, email = customer
    
    print(f"\n{'='*100}")
    print(f" {customer_name} (ID: {customer_id}) - 月度财务账本")
    print(f"{'='*100}")
    
    # 获取所有信用卡的月度账本
    cursor.execute("""
        SELECT 
            c.bank_name,
            c.card_number_last4,
            ml.month_start,
            ml.previous_balance as prev_cust,
            ml.customer_spend,
            ml.customer_payments,
            ml.rolling_balance as cust_balance,
            iml.previous_balance as prev_inf,
            iml.infinite_spend,
            iml.supplier_fee,
            iml.infinite_payments,
            iml.rolling_balance as inf_balance,
            iml.transfer_count
        FROM monthly_ledger ml
        JOIN infinite_monthly_ledger iml 
            ON ml.card_id = iml.card_id AND ml.month_start = iml.month_start
        JOIN credit_cards c ON ml.card_id = c.id
        WHERE ml.customer_id = ?
        ORDER BY c.bank_name, c.card_number_last4, ml.month_start DESC
    """, (customer_id,))
    
    results = cursor.fetchall()
    
    if not results:
        print(f"\nℹ️  没有找到月度账本记录")
        conn.close()
        return
    
    # 按卡片分组显示
    current_card = None
    
    for row in results:
        bank = row[0]
        last4 = row[1]
        month = row[2][:7]
        
        card_name = f"{bank} (*{last4})"
        
        if card_name != current_card:
            if current_card:
                print()
            print(f"\n{'─'*100}")
            print(f"💳 {card_name}")
            print(f"{'─'*100}")
            print(f"\n{'月份':<10} {'客户上月':>13} {'客户消费':>13} {'客户付款':>13} {'客户余额':>13} | {'INFINITE消费':>13} {'手续费':>10} {'INFINITE付款':>13} {'INFINITE余额':>13} {'转账':>5}")
            print(f"{'-'*100}")
            current_card = card_name
        
        # 打印数据行
        print(f"{month:<10} ", end='')
        print(f"RM {row[3]:>10,.2f} ", end='')
        print(f"RM {row[4]:>10,.2f} ", end='')
        print(f"RM {row[5]:>10,.2f} ", end='')
        print(f"RM {row[6]:>10,.2f} | ", end='')
        print(f"RM {row[8]:>10,.2f} ", end='')
        print(f"RM {row[9]:>7,.2f} ", end='')
        print(f"RM {row[10]:>10,.2f} ", end='')
        print(f"RM {row[11]:>10,.2f} ", end='')
        print(f"{row[12]:>5}")
    
    # 汇总统计
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT c.id) as card_count,
            COUNT(DISTINCT ml.month_start) as month_count,
            SUM(ml.customer_spend) as total_customer_spend,
            SUM(ml.customer_payments) as total_customer_payments,
            SUM(iml.infinite_spend) as total_infinite_spend,
            SUM(iml.supplier_fee) as total_supplier_fee,
            SUM(iml.infinite_payments) as total_infinite_payments
        FROM monthly_ledger ml
        JOIN infinite_monthly_ledger iml 
            ON ml.card_id = iml.card_id AND ml.month_start = iml.month_start
        JOIN credit_cards c ON ml.card_id = c.id
        WHERE ml.customer_id = ?
    """, (customer_id,))
    
    summary = cursor.fetchone()
    
    print(f"\n{'='*100}")
    print(f" 汇总统计")
    print(f"{'='*100}")
    print(f"  信用卡数量: {summary[0]}")
    print(f"  月份数量: {summary[1]}")
    print(f"  客户总消费: RM {summary[2]:,.2f}")
    print(f"  客户总付款: RM {summary[3]:,.2f}")
    print(f"  客户净欠款: RM {summary[2] - summary[3]:,.2f}")
    print(f"  INFINITE总消费: RM {summary[4]:,.2f}")
    print(f"  INFINITE总手续费: RM {summary[5]:,.2f}")
    print(f"  INFINITE总付款: RM {summary[6]:,.2f}")
    print(f"  INFINITE净余额: RM {summary[4] - summary[6]:,.2f}")
    
    # 显示供应商发票
    cursor.execute("""
        SELECT 
            invoice_number,
            supplier_name,
            invoice_date,
            total_amount,
            supplier_fee
        FROM supplier_invoices
        WHERE customer_id = ?
        ORDER BY invoice_date DESC
        LIMIT 10
    """, (customer_id,))
    
    invoices = cursor.fetchall()
    
    if invoices:
        print(f"\n{'='*100}")
        print(f" 最近的供应商发票 (Top 10)")
        print(f"{'='*100}")
        print(f"{'发票编号':<30} {'供应商':<20} {'日期':<12} {'金额':>15} {'手续费':>10}")
        print(f"{'-'*90}")
        for inv in invoices:
            print(f"{inv[0]:<30} {inv[1]:<20} {inv[2][:7]:<12} RM {inv[3]:>12,.2f} RM {inv[4]:>7,.2f}")
    
    conn.close()
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            customer_id = int(sys.argv[1])
            view_customer_ledger(customer_id)
        except ValueError:
            print("❌ Customer ID must be a number")
    else:
        view_customer_ledger()
