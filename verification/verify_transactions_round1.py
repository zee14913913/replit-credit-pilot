"""
Round 1 Verification: Transaction-by-transaction comparison with PDF originals
Purpose: Ensure 100% accuracy - no omissions, no additions, no modifications
Date: 2025-10-25
"""

import sys
sys.path.insert(0, '.')
from db.database import get_db
import json

def verify_bank_monthly_statement(bank_name, statement_month):
    """Verify a single monthly statement transaction by transaction"""
    
    print("\n" + "=" * 120)
    print(f"验证: {bank_name} - {statement_month}")
    print("=" * 120)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get monthly statement
        cursor.execute("""
            SELECT 
                ms.id,
                ms.previous_balance_total,
                ms.closing_balance_total,
                ms.owner_expenses,
                ms.owner_payments,
                ms.gz_expenses,
                ms.gz_payments,
                ms.transaction_count,
                ms.file_paths
            FROM monthly_statements ms
            WHERE ms.bank_name = ? AND ms.statement_month = ?
        """, (bank_name, statement_month))
        
        stmt = cursor.fetchone()
        
        if not stmt:
            print(f"❌ 未找到账单记录")
            return False
        
        stmt_id = stmt[0]
        prev_balance = stmt[1]
        closing_balance = stmt[2]
        owner_expenses = stmt[3]
        owner_payments = stmt[4]
        gz_expenses = stmt[5]
        gz_payments = stmt[6]
        txn_count = stmt[7]
        file_paths_json = stmt[8]
        
        # Parse file paths
        file_paths = json.loads(file_paths_json) if file_paths_json else []
        
        print(f"\n月度总结:")
        print(f"  期初余额: RM {prev_balance:,.2f}")
        print(f"  期末余额: RM {closing_balance:,.2f}")
        print(f"  交易总数: {txn_count} 笔")
        print(f"\n分类统计:")
        print(f"  Own's Expenses: RM {owner_expenses:,.2f}")
        print(f"  Own's Payment:  RM {owner_payments:,.2f}")
        print(f"  GZ's Expenses:  RM {gz_expenses:,.2f}")
        print(f"  GZ's Payment:   RM {gz_payments:,.2f}")
        print(f"\nPDF文件:")
        for fp in file_paths:
            print(f"  - {fp}")
        
        # Get all transactions
        cursor.execute("""
            SELECT 
                t.id,
                t.transaction_date,
                t.description,
                t.amount,
                t.transaction_type,
                t.owner_flag,
                t.card_last4,
                t.payer_name,
                t.supplier_name
            FROM transactions t
            WHERE t.monthly_statement_id = ?
            ORDER BY t.transaction_date, t.id
        """, (stmt_id,))
        
        transactions = cursor.fetchall()
        
        print(f"\n" + "=" * 120)
        print(f"交易明细 ({len(transactions)} 笔) - 请逐一对比PDF原件")
        print("=" * 120)
        print(f"{'#':>3} {'日期':>10} {'金额':>12} {'类型':>8} {'分类':>5} {'卡号':>8} {'描述':60}")
        print("-" * 120)
        
        for idx, txn in enumerate(transactions, 1):
            txn_id = txn[0]
            txn_date = txn[1]
            description = txn[2] or ''
            amount = txn[3]
            txn_type = txn[4] or ''
            owner_flag = txn[5] or 'own'
            card_last4 = txn[6] or ''
            payer_name = txn[7] or ''
            supplier_name = txn[8] or ''
            
            # Format description with card number
            if card_last4:
                desc_with_card = f"{description} (卡{card_last4})"
            else:
                desc_with_card = description
            
            # Truncate if too long
            if len(desc_with_card) > 60:
                desc_with_card = desc_with_card[:57] + "..."
            
            # Determine classification
            if txn_type in ['purchase', 'fee']:
                category = 'OWN消' if owner_flag == 'own' else 'GZ消'
            elif txn_type == 'payment':
                category = 'OWN付' if owner_flag == 'own' else 'GZ付'
            else:
                category = txn_type[:4].upper()
            
            print(f"{idx:3d} {txn_date:>10} RM {amount:>10,.2f} {txn_type:>8} {category:>5} {'*'+card_last4:>8} {desc_with_card:60}")
        
        print("=" * 120)
        
        # Calculate verification stats
        purchases = [t for t in transactions if t[4] in ['purchase', 'fee']]
        payments = [t for t in transactions if t[4] == 'payment']
        
        total_purchases = sum(t[3] for t in purchases)
        total_payments = sum(t[3] for t in payments)
        
        print(f"\n验证检查:")
        print(f"  消费交易: {len(purchases)} 笔, 总额 RM {total_purchases:,.2f}")
        print(f"  付款交易: {len(payments)} 笔, 总额 RM {total_payments:,.2f}")
        print(f"  计算余额变化: {prev_balance} + {total_purchases} + {total_payments} = {prev_balance + total_purchases + total_payments:,.2f}")
        print(f"  账单期末余额: {closing_balance:,.2f}")
        
        balance_diff = abs((prev_balance + total_purchases + total_payments) - closing_balance)
        if balance_diff < 0.01:
            print(f"  ✅ 余额验证通过！")
        else:
            print(f"  ⚠️ 余额差异: RM {balance_diff:,.2f}")
        
        print(f"\n请对照PDF原件，确认:")
        print(f"  1. 每笔交易的日期、金额、描述是否100%一致")
        print(f"  2. 是否有遗漏的交易")
        print(f"  3. 是否有多余的交易")
        print(f"  4. 卡号标注是否正确")
        
        return True


def verify_all_banks():
    """Verify all 5 banks - Round 1"""
    
    print("\n" + "=" * 120)
    print("第一轮验证: 5间银行信用卡账单逐笔对比")
    print("=" * 120)
    
    banks_to_verify = [
        ("Alliance Bank", "2024-09"),  # Example: earliest month with multiple cards
        ("HSBC", "2025-08"),           # Example: recent month
        ("Hong Leong Bank", "2025-04"), # Example: month with high amount
        ("Maybank", "2024-11"),        # Example: month with high amount
        ("UOB", "2025-08")             # Example: recent month
    ]
    
    print(f"\n策略: 对每个银行选择关键月份进行深度验证")
    print(f"共需验证 {len(banks_to_verify)} 个月度账单\n")
    
    for bank, month in banks_to_verify:
        verify_bank_monthly_statement(bank, month)
        print("\n")
    
    print("=" * 120)
    print("第一轮验证完成")
    print("=" * 120)
    print("\n请确认以上所有月份的交易记录与PDF原件100%一致")
    print("如有任何差异，请立即报告！")


def export_verification_report():
    """Export complete transaction list for verification"""
    
    print("\n" + "=" * 120)
    print("生成完整交易清单供验证")
    print("=" * 120)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Export all transactions by bank
        cursor.execute("""
            SELECT 
                ms.bank_name,
                ms.statement_month,
                t.transaction_date,
                t.description,
                t.amount,
                t.transaction_type,
                t.owner_flag,
                t.card_last4
            FROM transactions t
            JOIN monthly_statements ms ON ms.id = t.monthly_statement_id
            WHERE ms.customer_id = 10
            ORDER BY ms.bank_name, ms.statement_month, t.transaction_date, t.id
        """)
        
        transactions = cursor.fetchall()
        
        # Group by bank
        by_bank = {}
        for txn in transactions:
            bank = txn[0]
            if bank not in by_bank:
                by_bank[bank] = []
            by_bank[bank].append(txn)
        
        for bank, txns in sorted(by_bank.items()):
            print(f"\n{bank}: {len(txns)} 笔交易")
        
        print(f"\n总计: {len(transactions)} 笔交易")
        
        # Write to file
        with open('/tmp/verification_report_round1.txt', 'w', encoding='utf-8') as f:
            f.write("=" * 120 + "\n")
            f.write("第一轮验证报告 - 完整交易清单\n")
            f.write("=" * 120 + "\n\n")
            
            for bank, txns in sorted(by_bank.items()):
                f.write(f"\n{'=' * 120}\n")
                f.write(f"{bank} - {len(txns)} 笔交易\n")
                f.write(f"{'=' * 120}\n")
                f.write(f"{'月份':>8} {'日期':>10} {'金额':>12} {'类型':>8} {'分类':>5} {'卡号':>8} 描述\n")
                f.write("-" * 120 + "\n")
                
                for txn in txns:
                    month = txn[1]
                    date = txn[2]
                    desc = txn[3] or ''
                    amount = txn[4]
                    txn_type = txn[5] or ''
                    owner_flag = txn[6] or 'own'
                    card_last4 = txn[7] or ''
                    
                    if txn_type in ['purchase', 'fee']:
                        category = 'OWN消' if owner_flag == 'own' else 'GZ消'
                    elif txn_type == 'payment':
                        category = 'OWN付' if owner_flag == 'own' else 'GZ付'
                    else:
                        category = txn_type[:4].upper()
                    
                    f.write(f"{month:>8} {date:>10} RM {amount:>10,.2f} {txn_type:>8} {category:>5} {'*'+card_last4:>8} {desc}\n")
        
        print(f"\n✅ 报告已生成: /tmp/verification_report_round1.txt")


if __name__ == '__main__':
    print("=" * 120)
    print("第一轮验证: 信用卡交易逐笔对比PDF原件")
    print("=" * 120)
    
    # Run verification
    verify_all_banks()
    
    # Export report
    export_verification_report()
    
    print("\n" + "=" * 120)
    print("✅ 第一轮验证工具运行完成")
    print("=" * 120)
    print("\n下一步: 请仔细核对以上交易与PDF原件是否100%一致")
