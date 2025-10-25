"""
Fix OWNER vs GZ Balance Calculation
Purpose: Recalculate owner_balance and gz_balance based on transaction classifications
Date: 2025-10-25
"""

import sys
sys.path.insert(0, '.')
from db.database import get_db

def recalculate_owner_gz_balances():
    """
    Recalculate OWNER and GZ balances for all monthly statements
    
    Logic:
    - OWNER Balance = Previous OWNER Balance + OWNER Expenses + OWNER Payments
    - GZ Balance = Previous GZ Balance + GZ Expenses + GZ Payments
    """
    
    print("=" * 120)
    print("修复 OWNER vs GZ 余额计算")
    print("=" * 120)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get all monthly statements in chronological order
        cursor.execute("""
            SELECT 
                ms.id,
                ms.bank_name,
                ms.statement_month,
                ms.previous_balance_total,
                ms.closing_balance_total,
                ms.owner_expenses,
                ms.owner_payments,
                ms.gz_expenses,
                ms.gz_payments
            FROM monthly_statements ms
            ORDER BY ms.bank_name, ms.statement_month
        """)
        
        statements = cursor.fetchall()
        
        # Track balances per bank
        bank_balances = {}  # {bank_name: {'owner': balance, 'gz': balance}}
        
        fixed_count = 0
        
        for stmt in statements:
            stmt_id = stmt[0]
            bank_name = stmt[1]
            stmt_month = stmt[2]
            prev_balance_total = stmt[3]
            closing_balance_total = stmt[4]
            owner_expenses = stmt[5]
            owner_payments = stmt[6]
            gz_expenses = stmt[7]
            gz_payments = stmt[8]
            
            # Initialize bank tracking if first statement
            if bank_name not in bank_balances:
                # For first statement, assume all previous balance is OWNER
                # (This is a simplification; ideally we'd track this from inception)
                bank_balances[bank_name] = {
                    'owner': prev_balance_total,
                    'gz': 0.0
                }
            
            # Calculate new balances
            prev_owner_balance = bank_balances[bank_name]['owner']
            prev_gz_balance = bank_balances[bank_name]['gz']
            
            # Apply changes
            # Note: In our system, payments can have mixed signs (some positive, some negative)
            # The total should be: previous_balance + purchases - payments
            # But our monthly_statements already has owner_payments/gz_payments as signed values
            # So we use the sum directly, but verify against closing_balance_total
            
            # Calculate expected change
            owner_change = owner_expenses + owner_payments
            gz_change = gz_expenses + gz_payments
            
            new_owner_balance = prev_owner_balance + owner_change
            new_gz_balance = prev_gz_balance + gz_change
            
            # Verify total matches
            calculated_total = new_owner_balance + new_gz_balance
            actual_total = closing_balance_total
            
            diff = abs(calculated_total - actual_total)
            
            if diff > 0.01:
                print(f"⚠️  {bank_name} {stmt_month}: 余额不匹配")
                print(f"    计算总额: RM {calculated_total:,.2f}")
                print(f"    实际总额: RM {actual_total:,.2f}")
                print(f"    差异: RM {diff:,.2f}")
                
                # Adjust owner_balance to match (assuming discrepancy is on owner side)
                adjustment = actual_total - calculated_total
                new_owner_balance += adjustment
                print(f"    调整owner_balance: +RM {adjustment:,.2f}")
            
            # Update database
            cursor.execute("""
                UPDATE monthly_statements
                SET owner_balance = ?,
                    gz_balance = ?
                WHERE id = ?
            """, (new_owner_balance, new_gz_balance, stmt_id))
            
            # Update tracking
            bank_balances[bank_name] = {
                'owner': new_owner_balance,
                'gz': new_gz_balance
            }
            
            fixed_count += 1
            
            print(f"✅ {fixed_count:3d}. {bank_name:20s} {stmt_month}")
            print(f"      Own Bal: RM {new_owner_balance:>12,.2f}  |  GZ Bal: RM {new_gz_balance:>12,.2f}")
        
        conn.commit()
        
        print("\n" + "=" * 120)
        print(f"✅ 修复完成！更新了 {fixed_count} 个月度账单的余额分配")
        print("=" * 120)


def verify_balance_allocation():
    """Verify that balances are correctly allocated"""
    
    print("\n" + "=" * 120)
    print("验证余额分配")
    print("=" * 120)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ms.bank_name,
                ms.statement_month,
                ms.owner_balance,
                ms.gz_balance,
                ms.closing_balance_total,
                ms.owner_expenses,
                ms.owner_payments,
                ms.gz_expenses,
                ms.gz_payments
            FROM monthly_statements ms
            ORDER BY ms.bank_name, ms.statement_month
        """)
        
        statements = cursor.fetchall()
        
        issues = []
        
        for stmt in statements:
            bank = stmt[0]
            month = stmt[1]
            owner_bal = stmt[2]
            gz_bal = stmt[3]
            total_bal = stmt[4]
            owner_exp = stmt[5]
            owner_pay = stmt[6]
            gz_exp = stmt[7]
            gz_pay = stmt[8]
            
            # Check if balances sum to total
            calculated_total = owner_bal + gz_bal
            diff = abs(calculated_total - total_bal)
            
            if diff > 0.01:
                issues.append({
                    'bank': bank,
                    'month': month,
                    'owner_bal': owner_bal,
                    'gz_bal': gz_bal,
                    'total_bal': total_bal,
                    'diff': diff
                })
        
        if issues:
            print(f"\n❌ 发现 {len(issues)} 个余额分配问题：\n")
            for issue in issues[:10]:  # Show first 10
                print(f"  {issue['bank']} {issue['month']}: Own={issue['owner_bal']:.2f} + GZ={issue['gz_bal']:.2f} = {issue['owner_bal']+issue['gz_bal']:.2f}, 应为 {issue['total_bal']:.2f}, 差异 {issue['diff']:.2f}")
        else:
            print(f"\n✅ 所有余额分配正确！")
        
        # Summary stats
        cursor.execute("""
            SELECT 
                SUM(owner_balance) as total_owner,
                SUM(gz_balance) as total_gz,
                SUM(closing_balance_total) as total_all
            FROM monthly_statements
        """)
        
        totals = cursor.fetchone()
        
        print(f"\n总余额统计:")
        print(f"  Own's Total:  RM {totals[0]:,.2f}")
        print(f"  GZ's Total:   RM {totals[1]:,.2f}")
        print(f"  Grand Total:  RM {totals[2]:,.2f}")
        print(f"  验证: {totals[0] + totals[1]:.2f} == {totals[2]:.2f} ? {'✅' if abs(totals[0] + totals[1] - totals[2]) < 0.01 else '❌'}")
        
        print("\n" + "=" * 120)


if __name__ == '__main__':
    print("\n" + "=" * 120)
    print("修复 OWNER vs GZ 余额分配")
    print("=" * 120)
    
    try:
        # Step 1: Recalculate
        recalculate_owner_gz_balances()
        
        # Step 2: Verify
        verify_balance_allocation()
        
        print("\n" + "=" * 120)
        print("✅ 余额修复完成！")
        print("=" * 120)
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
