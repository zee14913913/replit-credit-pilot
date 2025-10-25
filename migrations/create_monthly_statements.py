"""
Migration: Create Monthly Statements Architecture
Purpose: Convert per-card statements to monthly-bank aggregated statements
Date: 2025-10-25
"""

import sys
sys.path.insert(0, '.')
from db.database import get_db

def create_monthly_statements_schema():
    """Create new tables for monthly statement aggregation"""
    
    sql_statements = [
        # 1. Create monthly_statements table
        """
        CREATE TABLE IF NOT EXISTS monthly_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            bank_name TEXT NOT NULL,
            statement_month TEXT NOT NULL,  -- Format: YYYY-MM
            period_start_date TEXT,         -- Earliest transaction date
            period_end_date TEXT,           -- Latest transaction date / statement date
            
            -- Aggregated balances
            previous_balance_total REAL DEFAULT 0.0,
            closing_balance_total REAL DEFAULT 0.0,
            
            -- OWNER vs GZ breakdown
            owner_balance REAL DEFAULT 0.0,      -- Own's OS Bal
            gz_balance REAL DEFAULT 0.0,         -- GZ's OS Bal
            owner_expenses REAL DEFAULT 0.0,     -- Own's Expenses
            owner_payments REAL DEFAULT 0.0,     -- Own's Payment
            gz_expenses REAL DEFAULT 0.0,        -- GZ's Expenses
            gz_payments REAL DEFAULT 0.0,        -- GZ's Payment
            
            -- Metadata
            file_paths TEXT,                     -- JSON array of PDF paths
            card_count INTEGER DEFAULT 0,        -- Number of cards in this statement
            transaction_count INTEGER DEFAULT 0,
            validation_score REAL,
            is_confirmed INTEGER DEFAULT 0,
            inconsistencies TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Ensure uniqueness
            UNIQUE(customer_id, bank_name, statement_month),
            
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        )
        """,
        
        # 2. Create monthly_statement_cards table
        """
        CREATE TABLE IF NOT EXISTS monthly_statement_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monthly_statement_id INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            card_last4 TEXT NOT NULL,
            card_type TEXT,
            
            -- Individual card balances
            previous_balance REAL DEFAULT 0.0,
            closing_balance REAL DEFAULT 0.0,
            
            -- Credit limits (optional)
            credit_limit REAL,
            
            -- Link to original statement
            original_statement_id INTEGER,  -- Reference to old statements table
            file_path TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (monthly_statement_id) REFERENCES monthly_statements(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES credit_cards(id) ON DELETE CASCADE,
            FOREIGN KEY (original_statement_id) REFERENCES statements(id) ON DELETE SET NULL
        )
        """,
        
        # 3. Create transaction_owner_overrides table
        """
        CREATE TABLE IF NOT EXISTS transaction_owner_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL UNIQUE,
            owner_flag TEXT NOT NULL CHECK(owner_flag IN ('own', 'gz')),
            override_reason TEXT,
            overridden_by TEXT,  -- Admin username
            overridden_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
        )
        """,
        
        # 4. Create statement_migration_map table (for rollback)
        """
        CREATE TABLE IF NOT EXISTS statement_migration_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            old_statement_id INTEGER NOT NULL,
            monthly_statement_id INTEGER NOT NULL,
            migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (old_statement_id) REFERENCES statements(id),
            FOREIGN KEY (monthly_statement_id) REFERENCES monthly_statements(id)
        )
        """,
        
        # 5. Create indexes for performance
        """
        CREATE INDEX IF NOT EXISTS idx_monthly_statements_customer 
        ON monthly_statements(customer_id, bank_name, statement_month)
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_monthly_statement_cards_monthly 
        ON monthly_statement_cards(monthly_statement_id)
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_transaction_owner_overrides_txn 
        ON transaction_owner_overrides(transaction_id)
        """
    ]
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        for idx, sql in enumerate(sql_statements, 1):
            try:
                cursor.execute(sql)
                print(f"✅ Step {idx}/{len(sql_statements)}: Success")
            except Exception as e:
                print(f"❌ Step {idx}/{len(sql_statements)}: Failed - {e}")
                raise
        
        conn.commit()
        print("\n✅ All tables created successfully!")


def add_columns_to_transactions():
    """Add new columns to transactions table"""
    
    columns_to_add = [
        ("monthly_statement_id", "INTEGER"),
        ("owner_flag", "TEXT CHECK(owner_flag IN ('own', 'gz', NULL))"),
        ("classification_source", "TEXT")  # 'auto', 'manual', 'override'
    ]
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(transactions)")
        existing_columns = {col[1] for col in cursor.fetchall()}
        
        for col_name, col_type in columns_to_add:
            if col_name in existing_columns:
                print(f"⏭️  Column '{col_name}' already exists, skipping")
                continue
            
            try:
                cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added column '{col_name}' to transactions table")
            except Exception as e:
                print(f"❌ Failed to add column '{col_name}': {e}")
                raise
        
        conn.commit()
        print("\n✅ Transactions table updated successfully!")


def verify_schema():
    """Verify new tables were created correctly"""
    
    tables_to_check = [
        'monthly_statements',
        'monthly_statement_cards',
        'transaction_owner_overrides',
        'statement_migration_map'
    ]
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        print("\n" + "=" * 80)
        print("Schema Verification")
        print("=" * 80)
        
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,))
            exists = cursor.fetchone()[0]
            
            if exists:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                print(f"✅ {table:35s} - Exists ({row_count} rows)")
            else:
                print(f"❌ {table:35s} - NOT FOUND!")
        
        # Check transactions table columns
        print("\n" + "=" * 80)
        print("Transactions Table New Columns")
        print("=" * 80)
        
        cursor.execute("PRAGMA table_info(transactions)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        for col_name in ['monthly_statement_id', 'owner_flag', 'classification_source', 'card_last4']:
            if col_name in columns:
                print(f"✅ {col_name:30s} - {columns[col_name]}")
            else:
                print(f"❌ {col_name:30s} - NOT FOUND!")


if __name__ == '__main__':
    print("=" * 80)
    print("Creating Monthly Statements Schema")
    print("=" * 80)
    print()
    
    try:
        # Step 1: Create new tables
        print("Step 1: Creating new tables...")
        create_monthly_statements_schema()
        
        # Step 2: Add columns to transactions
        print("\nStep 2: Updating transactions table...")
        add_columns_to_transactions()
        
        # Step 3: Verify
        print("\nStep 3: Verifying schema...")
        verify_schema()
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION SCHEMA CREATION COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        sys.exit(1)
