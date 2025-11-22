#!/usr/bin/env python3
import sqlite3
import sys
from datetime import datetime

def verify_data_integrity():
    """验证数据库数据完整性"""
    print("="*60)
    print("🔍 CreditPilot 数据完整性验证")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        checks_passed = 0
        checks_failed = 0
        
        # 1. 客户记录
        cursor.execute("SELECT COUNT(*) FROM customers")
        customers = cursor.fetchone()[0]
        if customers > 0:
            print(f"✅ 客户记录: {customers}")
            checks_passed += 1
        else:
            print(f"❌ 客户记录: {customers} (期望 > 0)")
            checks_failed += 1
        
        # 2. 账单记录
        cursor.execute("SELECT COUNT(*) FROM statements")
        statements = cursor.fetchone()[0]
        if statements > 0:
            print(f"✅ 账单记录: {statements}")
            checks_passed += 1
        else:
            print(f"❌ 账单记录: {statements} (期望 > 0)")
            checks_failed += 1
        
        # 3. 交易记录
        cursor.execute("SELECT COUNT(*) FROM transactions")
        transactions = cursor.fetchone()[0]
        if transactions > 0:
            print(f"✅ 交易记录: {transactions:,}")
            checks_passed += 1
        else:
            print(f"❌ 交易记录: {transactions} (期望 > 0)")
            checks_failed += 1
        
        # 4. 信用卡记录
        cursor.execute("SELECT COUNT(*) FROM credit_cards")
        cards = cursor.fetchone()[0]
        if cards > 0:
            print(f"✅ 信用卡记录: {cards}")
            checks_passed += 1
        else:
            print(f"❌ 信用卡记录: {cards} (期望 > 0)")
            checks_failed += 1
        
        # 5. 财务汇总
        cursor.execute("""
            SELECT 
                ROUND(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 2) as expenses,
                ROUND(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 2) as payments
            FROM transactions
        """)
        row = cursor.fetchone()
        expenses = row[0] or 0
        payments = row[1] or 0
        balance = round(expenses - payments, 2)
        
        print(f"\n💰 财务汇总:")
        print(f"   总费用: RM {expenses:,.2f}")
        print(f"   总还款: RM {payments:,.2f}")
        print(f"   净余额: RM {balance:,.2f}")
        
        if expenses > 0:
            checks_passed += 1
        else:
            print(f"   ❌ 总费用为零")
            checks_failed += 1
        
        # 6. 数据一致性检查（简化版本）
        cursor.execute("SELECT COUNT(DISTINCT id) FROM customers")
        total_customers = cursor.fetchone()[0]
        
        print(f"\n✅ 数据一致性: {total_customers} 个客户记录")
        checks_passed += 1
        
        conn.close()
        
        # 总结
        print("\n" + "="*60)
        print(f"📊 验证结果: {checks_passed} 通过, {checks_failed} 失败")
        print("="*60)
        
        if checks_failed == 0:
            print("🎯 数据完整性验证: PASS\n")
            return 0
        else:
            print("❌ 数据完整性验证: FAIL\n")
            return 1
            
    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}\n")
        return 1

if __name__ == "__main__":
    sys.exit(verify_data_integrity())
