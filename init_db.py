#!/usr/bin/env python3
"""
Database initialization script for Render deployment
Creates all necessary tables and initial data
"""

import os
import sqlite3
from pathlib import Path

def init_database():
    """Initialize database with all required tables"""
    
    # Create db directory if not exists
    db_dir = Path("db")
    db_dir.mkdir(exist_ok=True)
    
    db_path = db_dir / "smart_loan_manager.db"
    
    print(f"Initializing database at: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    print("Creating tables...")
    
    # Customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            ic_number TEXT,
            monthly_income REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Customer logins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Customer sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # Credit cards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            bank_name TEXT NOT NULL,
            card_type TEXT,
            last_four TEXT,
            credit_limit REAL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # Statements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            statement_date TEXT NOT NULL,
            due_date TEXT,
            total_amount REAL,
            min_payment REAL,
            upload_filename TEXT,
            is_confirmed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES credit_cards(id)
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_id INTEGER NOT NULL,
            transaction_date TEXT,
            description TEXT,
            amount REAL,
            category TEXT,
            merchant TEXT,
            notes TEXT,
            FOREIGN KEY (statement_id) REFERENCES statements(id)
        )
    ''')
    
    # Transaction tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            color TEXT DEFAULT '#007bff',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            UNIQUE(customer_id, tag_name)
        )
    ''')
    
    # Transaction tag mappings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_tag_mapping (
            transaction_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (transaction_id, tag_id),
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (tag_id) REFERENCES transaction_tags(id)
        )
    ''')
    
    # Budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            month TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # Reminders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_id INTEGER NOT NULL,
            reminder_date TEXT NOT NULL,
            is_sent INTEGER DEFAULT 0,
            is_paid INTEGER DEFAULT 0,
            FOREIGN KEY (statement_id) REFERENCES statements(id)
        )
    ''')
    
    # BNM rates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bnm_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rate_type TEXT NOT NULL,
            rate_value REAL NOT NULL,
            effective_date TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Banking news table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banking_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            source_url TEXT,
            published_date TEXT,
            is_approved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(title, published_date)
        )
    ''')
    
    # Credit card products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_card_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT NOT NULL,
            card_name TEXT NOT NULL,
            annual_fee REAL,
            cashback_rate REAL,
            rewards_rate REAL,
            categories TEXT,
            features TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Card recommendations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS card_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            card_product_id INTEGER NOT NULL,
            match_score REAL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (card_product_id) REFERENCES credit_card_products(id)
        )
    ''')
    
    # Financial optimization suggestions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_optimization_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            suggestion_type TEXT NOT NULL,
            current_situation TEXT,
            optimization_plan TEXT,
            potential_savings REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # Consultation requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultation_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            request_type TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # Customer employment types table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_employment_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER UNIQUE NOT NULL,
            employment_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # Service terms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            term_type TEXT NOT NULL,
            agreed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # Audit logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    conn.commit()
    print("✅ Database tables created successfully!")
    
    # Insert default BNM rates if not exist
    cursor.execute("SELECT COUNT(*) FROM bnm_rates")
    if cursor.fetchone()[0] == 0:
        print("Inserting default BNM rates...")
        default_rates = [
            ('OPR', 3.00, '2025-01-01'),
            ('SBR', 3.25, '2025-01-01'),
            ('Personal Loan', 6.50, '2025-01-01'),
            ('Housing Loan', 4.20, '2025-01-01')
        ]
        cursor.executemany(
            "INSERT INTO bnm_rates (rate_type, rate_value, effective_date) VALUES (?, ?, ?)",
            default_rates
        )
        conn.commit()
        print("✅ Default BNM rates inserted!")
    
    conn.close()
    print("✅ Database initialization complete!")

if __name__ == "__main__":
    init_database()
