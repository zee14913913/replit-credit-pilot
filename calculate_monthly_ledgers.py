#!/usr/bin/env python3
"""
Monthly Ledger Calculator - 为所有客户计算月度账本
"""
import sys
sys.path.insert(0, '.')

from services.monthly_ledger_engine import MonthlyLedgerEngine
import sqlite3

def calculate_all_customers():
    """计算所有客户的月度账本"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 获取所有有账单的客户
    cursor.execute("""
        SELECT DISTINCT 
            c.customer_id,
            cu.name
        FROM credit_cards c
        JOIN customers cu ON c.customer_id = cu.id
        JOIN statements s ON s.card_id = c.id
        ORDER BY cu.name
    """)
    customers = cursor.fetchall()
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"开始计算所有客户的月度账本")
    print(f"{'='*80}")
    print(f"共 {len(customers)} 位客户\n")
    
    engine = MonthlyLedgerEngine()
    
    for customer_id, customer_name in customers:
        print(f"\n{'='*80}")
        print(f"正在计算: {customer_name} (ID: {customer_id})")
        print(f"{'='*80}\n")
        
        try:
            engine.calculate_all_cards_for_customer(customer_id, recalculate_all=True)
        except Exception as e:
            print(f"❌ 计算失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n\n{'='*80}")
    print(f"✅ 所有客户的月度账本计算完成！")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    calculate_all_customers()
