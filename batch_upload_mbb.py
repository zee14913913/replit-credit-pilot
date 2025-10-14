#!/usr/bin/env python3
"""
Batch upload script for Chang Choon Chow's Maybank statements
Processes 12+ months of statements (Sep 2024 - Aug 2025)
"""
import os
import sqlite3
import re
from datetime import datetime
from ingest.statement_parser import parse_maybank_statement

def extract_statement_date_from_filename(filename):
    """Extract statement date from filename like '03:01:2025_*.pdf'"""
    match = re.match(r'03:(\d{2}):(\d{4})', filename)
    if match:
        month = match.group(1)
        year = match.group(2)
        # Statement date is the 3rd of the month
        return f"{year}-{month}-03"
    return None

def main():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # Get customer ID
    cursor.execute("SELECT id, name FROM customers WHERE name = 'Chang Choon Chow'")
    customer_row = cursor.fetchone()
    customer_id = customer_row[0]
    customer_name = customer_row[1]
    
    print(f"\n🎯 Processing statements for {customer_name} (ID: {customer_id})")
    
    # Get Maybank card
    cursor.execute(
        """SELECT id, card_number_last4, card_type 
           FROM credit_cards 
           WHERE customer_id = ? AND bank_name = 'Maybank'""",
        (customer_id,)
    )
    card_row = cursor.fetchone()
    if not card_row:
        print("❌ No Maybank card found!")
        conn.close()
        return
    
    card_id, card_last4, card_type = card_row
    print(f"\n💳 Maybank Card: {card_type} (*{card_last4})")
    
    # List statement files
    upload_dir = "static/uploads"
    statement_files = sorted([
        f for f in os.listdir(upload_dir) 
        if f.startswith("03:") and f.endswith(".pdf")
    ])
    
    print(f"\n📋 Found {len(statement_files)} statement files to process\n")
    
    total_statements = 0
    total_transactions = 0
    
    for filename in statement_files:
        file_path = os.path.join(upload_dir, filename)
        
        print(f"\n{'='*70}")
        print(f"📄 Processing: {filename}")
        print(f"{'='*70}")
        
        # Extract statement date from filename
        statement_date_str = extract_statement_date_from_filename(filename)
        if not statement_date_str:
            print(f"❌ Could not extract statement date from filename")
            continue
        
        print(f"📅 Statement Date: {statement_date_str}")
        
        # Parse the statement
        info, transactions = parse_maybank_statement(file_path)
        
        if not transactions:
            print(f"❌ Failed to parse statement - no transactions found")
            continue
        
        print(f"✅ Parsed {len(transactions)} transactions")
        print(f"💰 Total Amount: RM {info.get('total', 0):,.2f}")
        
        # Check if statement already exists
        cursor.execute(
            """SELECT id FROM statements 
               WHERE card_id = ? AND statement_date = ?""",
            (card_id, statement_date_str)
        )
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️  Statement already exists (ID: {existing[0]}), skipping...")
            continue
        
        # Insert statement
        cursor.execute(
            """INSERT INTO statements 
               (card_id, statement_date, due_date, statement_total, 
                file_path, is_confirmed, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                card_id,
                statement_date_str,
                statement_date_str,  # Using same date for due_date
                abs(info.get('total', 0)),
                file_path,
                0,  # not confirmed yet
                datetime.now()
            )
        )
        statement_id = cursor.lastrowid
        print(f"✅ Created statement ID: {statement_id}")
        
        # Insert transactions
        transaction_count = 0
        statement_year = int(statement_date_str[:4])
        statement_month = int(statement_date_str[5:7])
        
        for txn in transactions:
            # Parse date
            txn_date = txn.get('date', '')
            if '/' in txn_date and len(txn_date.split('/')) == 2:
                # Format: DD/MM (need to add year)
                day, month = txn_date.split('/')
                txn_month = int(month)
                
                # Handle year rollover: if transaction month > statement month, 
                # it's from the previous year (e.g., Dec transactions on Jan statement)
                if txn_month > statement_month:
                    year = statement_year - 1
                else:
                    year = statement_year
                
                full_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                full_date = statement_date_str
            
            amount = abs(txn.get('amount', 0))
            description = txn.get('description', '').strip()
            
            # Determine transaction type based on amount sign
            # Negative amounts in Maybank statements are credits/payments
            if txn.get('amount', 0) < 0:
                transaction_type = 'payment'
            else:
                transaction_type = 'purchase'
            
            cursor.execute(
                """INSERT INTO transactions 
                   (statement_id, transaction_date, description, amount, 
                    transaction_type, category, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    statement_id,
                    full_date,
                    description,
                    amount,
                    transaction_type,
                    'Uncategorized',  # Will be categorized later
                    datetime.now()
                )
            )
            transaction_count += 1
        
        print(f"✅ Inserted {transaction_count} transactions")
        
        total_statements += 1
        total_transactions += transaction_count
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print(f"\n{'='*70}")
    print(f"🎉 BATCH UPLOAD COMPLETE!")
    print(f"{'='*70}")
    print(f"✅ Total Statements Processed: {total_statements}")
    print(f"✅ Total Transactions Inserted: {total_transactions}")
    print(f"\n💡 Next steps:")
    print(f"   1. Run categorization on all transactions")
    print(f"   2. Verify statements and mark as verified")
    print(f"   3. Generate monthly reports")
    print()

if __name__ == "__main__":
    main()
