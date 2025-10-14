#!/usr/bin/env python3
"""
Backfill Previous Balance for all credit card statements.

Logic:
1. For each credit card, get all statements sorted by statement_date
2. First statement: Previous Balance = 0.00
3. Subsequent statements: Previous Balance = Previous month's Statement Total
4. Update database with correct values
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_db
from datetime import datetime

def backfill_previous_balance():
    """Backfill Previous Balance for all statements."""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get all credit cards
        cursor.execute("SELECT id, card_number_last4, bank_name FROM credit_cards ORDER BY id")
        cards = cursor.fetchall()
        
        print("=" * 80)
        print("📋 回填Previous Balance - 所有信用卡账单")
        print("=" * 80)
        
        total_updated = 0
        
        for card in cards:
            card_id, card_last4, card_name = card
            
            # Get all statements for this card, sorted by statement_date
            cursor.execute("""
                SELECT id, statement_date, statement_total, previous_balance
                FROM statements
                WHERE card_id = ?
                ORDER BY statement_date ASC
            """, (card_id,))
            
            statements = cursor.fetchall()
            
            if not statements:
                continue
            
            print(f"\n🔹 信用卡: {card_name} (****{card_last4}) - {len(statements)}个账单")
            print("-" * 80)
            
            previous_total = 0.00  # First month's Previous Balance is always 0
            
            for idx, (stmt_id, stmt_date, total_amount, old_prev_balance) in enumerate(statements):
                # Update Previous Balance
                cursor.execute("""
                    UPDATE statements
                    SET previous_balance = ?
                    WHERE id = ?
                """, (previous_total, stmt_id))
                
                # Show the change
                status = "✅" if old_prev_balance == 0 else f"🔄 {old_prev_balance:.2f} → {previous_total:.2f}"
                print(f"  {idx+1}. {stmt_date}: Previous Balance = RM {previous_total:>10.2f}, Total = RM {total_amount:>10.2f}  {status}")
                
                # Next month's Previous Balance = This month's Total
                previous_total = total_amount
                total_updated += 1
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ 回填完成！共更新 {total_updated} 个账单")
        print("=" * 80)
        
        # Verify the results
        print("\n" + "=" * 80)
        print("📊 验证结果")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                cc.bank_name,
                cc.card_number_last4,
                s.statement_date,
                s.previous_balance,
                s.statement_total
            FROM statements s
            JOIN credit_cards cc ON s.card_id = cc.id
            ORDER BY cc.id, s.statement_date
        """)
        
        results = cursor.fetchall()
        
        current_card = None
        for card_name, card_last4, stmt_date, prev_bal, total in results:
            card_key = f"{card_name} (****{card_last4})"
            
            if card_key != current_card:
                print(f"\n🔹 {card_key}")
                current_card = card_key
            
            print(f"  {stmt_date}: Prev={prev_bal:>10.2f}, Total={total:>10.2f}")

if __name__ == "__main__":
    backfill_previous_balance()
