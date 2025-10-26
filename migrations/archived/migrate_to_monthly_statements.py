"""
Data Migration Script: Merge per-card statements into monthly-bank aggregates
Purpose: Convert 75 individual card statements into monthly consolidated statements
Date: 2025-10-25
"""

import sys
sys.path.insert(0, '.')
from db.database import get_db
from services.owner_classifier import OwnerClassifier
import json
from collections import defaultdict

def analyze_current_data():
    """Analyze current statement structure"""
    print("=" * 100)
    print("STEP 1: Analyzing Current Data")
    print("=" * 100)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get all statements grouped by customer, bank, month
        cursor.execute("""
            SELECT 
                c.id as customer_id,
                c.name as customer_name,
                cc.bank_name,
                strftime('%Y-%m', s.statement_date) as statement_month,
                COUNT(DISTINCT s.id) as statement_count,
                COUNT(DISTINCT cc.id) as card_count,
                GROUP_CONCAT(DISTINCT cc.card_number_last4) as card_numbers,
                SUM(s.previous_balance) as total_prev_balance,
                SUM(s.statement_total) as total_closing_balance
            FROM statements s
            JOIN credit_cards cc ON cc.id = s.card_id
            JOIN customers c ON c.id = cc.customer_id
            WHERE c.id = 10
            GROUP BY c.id, c.name, cc.bank_name, strftime('%Y-%m', s.statement_date)
            ORDER BY cc.bank_name, statement_month
        """)
        
        groups = cursor.fetchall()
        
        print(f"\n找到 {len(groups)} 个需要合并的月度账单组：\n")
        
        total_old_statements = 0
        
        for idx, group in enumerate(groups, 1):
            customer_id = group[0]
            customer_name = group[1]
            bank_name = group[2]
            statement_month = group[3]
            statement_count = group[4]
            card_count = group[5]
            card_numbers = group[6]
            total_prev = group[7] or 0
            total_closing = group[8] or 0
            
            total_old_statements += statement_count
            
            print(f"{idx:3d}. {bank_name:20s} {statement_month} - {statement_count} statements, {card_count} cards")
            print(f"     Cards: {card_numbers}")
            print(f"     期初总额: RM {total_prev:,.2f}, 期末总额: RM {total_closing:,.2f}")
        
        print("\n" + "=" * 100)
        print(f"总结: 将 {total_old_statements} 个单卡账单 合并成 {len(groups)} 个月度账单")
        print("=" * 100)
        
        return groups


def migrate_statements():
    """Migrate individual card statements to monthly aggregates"""
    print("\n" + "=" * 100)
    print("STEP 2: Migrating to Monthly Statements")
    print("=" * 100)
    
    classifier = OwnerClassifier()
    overrides = classifier.get_manual_overrides()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get all statement groups
        cursor.execute("""
            SELECT 
                c.id as customer_id,
                cc.bank_name,
                strftime('%Y-%m', s.statement_date) as statement_month,
                GROUP_CONCAT(s.id) as statement_ids,
                GROUP_CONCAT(cc.id) as card_ids,
                GROUP_CONCAT(cc.card_number_last4) as card_last4s,
                GROUP_CONCAT(cc.card_type) as card_types,
                GROUP_CONCAT(s.file_path) as file_paths,
                MIN(s.statement_date) as period_start,
                MAX(s.statement_date) as period_end,
                SUM(s.previous_balance) as total_prev_balance,
                SUM(s.statement_total) as total_closing_balance
            FROM statements s
            JOIN credit_cards cc ON cc.id = s.card_id
            JOIN customers c ON c.id = cc.customer_id
            WHERE c.id = 10
            GROUP BY c.id, cc.bank_name, strftime('%Y-%m', s.statement_date)
            ORDER BY cc.bank_name, statement_month
        """)
        
        groups = cursor.fetchall()
        
        migrated_count = 0
        
        for group in groups:
            customer_id = group[0]
            bank_name = group[1]
            statement_month = group[2]
            statement_ids = group[3].split(',')
            card_ids = group[4].split(',')
            card_last4s = group[5].split(',')
            card_types = group[6].split(',') if group[6] else [''] * len(card_ids)
            file_paths_str = group[7]
            period_start = group[8]
            period_end = group[9]
            total_prev_balance = group[10] or 0
            total_closing_balance = group[11] or 0
            
            # Create file_paths JSON
            file_paths = [fp for fp in file_paths_str.split(',') if fp] if file_paths_str else []
            file_paths_json = json.dumps(file_paths)
            
            # Get all transactions for these statements
            stmt_ids_placeholder = ','.join('?' * len(statement_ids))
            cursor.execute(f"""
                SELECT 
                    id, statement_id, transaction_date, description, amount,
                    transaction_type, payer_name, supplier_name, is_supplier,
                    card_last4
                FROM transactions
                WHERE statement_id IN ({stmt_ids_placeholder})
            """, statement_ids)
            
            columns = [col[0] for col in cursor.description]
            transactions = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Classify transactions
            classifications = classifier.classify_transaction_batch(transactions, overrides)
            
            # Calculate OWNER vs GZ breakdown
            owner_expenses = 0
            owner_payments = 0
            gz_expenses = 0
            gz_payments = 0
            
            for txn in transactions:
                txn_id = txn['id']
                amount = txn['amount']
                txn_type = txn['transaction_type']
                owner_flag = classifications.get(txn_id, 'own')
                
                if owner_flag == 'own':
                    if txn_type in ['purchase', 'fee']:
                        owner_expenses += amount
                    elif txn_type == 'payment':
                        owner_payments += amount
                else:  # gz
                    if txn_type in ['purchase', 'fee']:
                        gz_expenses += amount
                    elif txn_type == 'payment':
                        gz_payments += amount
            
            # Calculate balances (simplified - assuming all balance belongs to owner for now)
            # This needs refinement based on actual balance tracking logic
            owner_balance = total_closing_balance
            gz_balance = 0
            
            # Insert monthly_statement
            cursor.execute("""
                INSERT INTO monthly_statements (
                    customer_id, bank_name, statement_month,
                    period_start_date, period_end_date,
                    previous_balance_total, closing_balance_total,
                    owner_balance, gz_balance,
                    owner_expenses, owner_payments,
                    gz_expenses, gz_payments,
                    file_paths, card_count, transaction_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id, bank_name, statement_month,
                period_start, period_end,
                total_prev_balance, total_closing_balance,
                owner_balance, gz_balance,
                owner_expenses, owner_payments,
                gz_expenses, gz_payments,
                file_paths_json, len(set(card_ids)), len(transactions)
            ))
            
            monthly_statement_id = cursor.lastrowid
            
            # Insert monthly_statement_cards
            for i, old_stmt_id in enumerate(statement_ids):
                card_id = card_ids[i]
                card_last4 = card_last4s[i]
                card_type = card_types[i] if i < len(card_types) else ''
                
                # Get individual card balance
                cursor.execute("""
                    SELECT previous_balance, statement_total, file_path
                    FROM statements WHERE id = ?
                """, (old_stmt_id,))
                
                card_data = cursor.fetchone()
                if card_data:
                    cursor.execute("""
                        INSERT INTO monthly_statement_cards (
                            monthly_statement_id, card_id, card_last4, card_type,
                            previous_balance, closing_balance,
                            original_statement_id, file_path
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        monthly_statement_id, card_id, card_last4, card_type,
                        card_data[0] or 0, card_data[1] or 0,
                        old_stmt_id, card_data[2]
                    ))
                
                # Record migration map
                cursor.execute("""
                    INSERT INTO statement_migration_map (old_statement_id, monthly_statement_id)
                    VALUES (?, ?)
                """, (old_stmt_id, monthly_statement_id))
            
            # Update transactions to reference monthly_statement_id and set owner_flag
            for txn in transactions:
                txn_id = txn['id']
                owner_flag = classifications.get(txn_id, 'own')
                classification_source = 'override' if txn_id in overrides else 'auto'
                
                cursor.execute("""
                    UPDATE transactions
                    SET monthly_statement_id = ?,
                        owner_flag = ?,
                        classification_source = ?
                    WHERE id = ?
                """, (monthly_statement_id, owner_flag, classification_source, txn_id))
            
            migrated_count += 1
            print(f"✅ {migrated_count:3d}. {bank_name:20s} {statement_month} - {len(transactions)} transactions, {len(set(card_ids))} cards")
        
        conn.commit()
        
        print("\n" + "=" * 100)
        print(f"✅ 成功迁移 {migrated_count} 个月度账单！")
        print("=" * 100)
        
        return migrated_count


def verify_migration():
    """Verify migration results"""
    print("\n" + "=" * 100)
    print("STEP 3: Verifying Migration")
    print("=" * 100)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check monthly_statements count
        cursor.execute("SELECT COUNT(*) FROM monthly_statements")
        monthly_count = cursor.fetchone()[0]
        
        # Check transactions updated
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE monthly_statement_id IS NOT NULL")
        txn_updated = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE owner_flag IS NOT NULL")
        txn_classified = cursor.fetchone()[0]
        
        # Check total balances match
        cursor.execute("SELECT SUM(previous_balance), SUM(statement_total) FROM statements WHERE card_id IN (SELECT id FROM credit_cards WHERE customer_id = 10)")
        old_totals = cursor.fetchone()
        
        cursor.execute("SELECT SUM(previous_balance_total), SUM(closing_balance_total) FROM monthly_statements")
        new_totals = cursor.fetchone()
        
        print(f"\n✅ Monthly Statements Created: {monthly_count}")
        print(f"✅ Transactions Updated: {txn_updated}")
        print(f"✅ Transactions Classified: {txn_classified}")
        print(f"\n余额验证:")
        print(f"  旧系统期初余额: RM {old_totals[0]:,.2f}")
        print(f"  新系统期初余额: RM {new_totals[0]:,.2f}")
        print(f"  差异: RM {abs(old_totals[0] - new_totals[0]):,.2f}")
        print(f"\n  旧系统期末余额: RM {old_totals[1]:,.2f}")
        print(f"  新系统期末余额: RM {new_totals[1]:,.2f}")
        print(f"  差异: RM {abs(old_totals[1] - new_totals[1]):,.2f}")
        
        if abs(old_totals[0] - new_totals[0]) < 0.01 and abs(old_totals[1] - new_totals[1]) < 0.01:
            print(f"\n✅ 余额验证通过！")
        else:
            print(f"\n⚠️ 余额存在差异，需要进一步检查")
        
        print("\n" + "=" * 100)


if __name__ == '__main__':
    print("\n" + "=" * 100)
    print("数据迁移: 单卡账单 → 月度合并账单")
    print("=" * 100)
    
    try:
        # Step 1: Analyze
        groups = analyze_current_data()
        
        # Confirmation
        print(f"\n即将迁移 {len(groups)} 个月度账单组")
        print("=" * 100)
        
        # Step 2: Migrate
        migrated = migrate_statements()
        
        # Step 3: Verify
        verify_migration()
        
        print("\n" + "=" * 100)
        print("✅ 数据迁移完成！")
        print("=" * 100)
        print("\n下一步: 进行两次手动逐笔验证，确保100%准确")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
