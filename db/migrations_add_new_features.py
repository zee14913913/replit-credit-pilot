import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_loan_manager.db')

def migrate_database():
    """Add tables for new features: budgets, tags, batch operations, filters, users, etc."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting database migration for new features...")
    
    # 1. Budgets table - for budget management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            alert_threshold REAL DEFAULT 80.0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            UNIQUE(customer_id, category)
        )
    ''')
    print("✓ Created budgets table")
    
    # 2. Tags table - for custom tags
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            tag_color TEXT DEFAULT '#1FAA59',
            usage_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            UNIQUE(customer_id, tag_name)
        )
    ''')
    print("✓ Created tags table")
    
    # 3. Transaction tags relationship (many-to-many)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            UNIQUE(transaction_id, tag_id)
        )
    ''')
    print("✓ Created transaction_tags relationship table")
    
    # 4. Extend transactions table with notes and receipt
    try:
        cursor.execute('ALTER TABLE transactions ADD COLUMN notes TEXT')
        print("✓ Added notes column to transactions")
    except sqlite3.OperationalError:
        print("  notes column already exists")
    
    try:
        cursor.execute('ALTER TABLE transactions ADD COLUMN receipt_path TEXT')
        print("✓ Added receipt_path column to transactions")
    except sqlite3.OperationalError:
        print("  receipt_path column already exists")
    
    try:
        cursor.execute('ALTER TABLE transactions ADD COLUMN is_reimbursable INTEGER DEFAULT 0')
        print("✓ Added is_reimbursable column to transactions")
    except sqlite3.OperationalError:
        print("  is_reimbursable column already exists")
    
    # 5. Saved filters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            filter_name TEXT NOT NULL,
            filter_criteria TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    print("✓ Created saved_filters table")
    
    # 6. Batch jobs table - for batch operations tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_type TEXT NOT NULL,
            customer_id INTEGER,
            total_items INTEGER DEFAULT 0,
            processed_items INTEGER DEFAULT 0,
            failed_items INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            result_data TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    print("✓ Created batch_jobs table")
    
    # 7. Export history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS export_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            export_type TEXT NOT NULL,
            export_format TEXT NOT NULL,
            file_path TEXT,
            record_count INTEGER DEFAULT 0,
            filters_applied TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    print("✓ Created export_history table")
    
    # 8. Users table - for multi-user support
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'customer',
            is_active INTEGER DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Created users table")
    
    # 9. User customer relationship (many-to-many for family accounts)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            access_level TEXT DEFAULT 'view',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            UNIQUE(user_id, customer_id)
        )
    ''')
    print("✓ Created user_customers relationship table")
    
    # 10. Email notifications preferences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            email_enabled INTEGER DEFAULT 1,
            upload_notifications INTEGER DEFAULT 1,
            reminder_notifications INTEGER DEFAULT 1,
            budget_alerts INTEGER DEFAULT 1,
            anomaly_alerts INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            UNIQUE(customer_id)
        )
    ''')
    print("✓ Created notification_preferences table")
    
    # 11. Email log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            email_to TEXT NOT NULL,
            email_subject TEXT NOT NULL,
            email_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    print("✓ Created email_log table")
    
    # 12. API keys table - for API access
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key_name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            api_secret TEXT,
            permissions TEXT,
            is_active INTEGER DEFAULT 1,
            last_used TIMESTAMP,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    print("✓ Created api_keys table")
    
    # 13. Extend statements table for batch tracking
    try:
        cursor.execute('ALTER TABLE statements ADD COLUMN batch_job_id INTEGER')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_statements_batch ON statements(batch_job_id)')
        print("✓ Added batch_job_id to statements")
    except sqlite3.OperationalError:
        print("  batch_job_id column already exists")
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_budgets_customer ON budgets(customer_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_customer ON tags(customer_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON batch_jobs(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_export_history_customer ON export_history(customer_id)')
    print("✓ Created performance indexes")
    
    conn.commit()
    conn.close()
    print("\n✅ Database migration completed successfully!")
    print(f"   Database location: {DB_PATH}")

if __name__ == "__main__":
    migrate_database()
