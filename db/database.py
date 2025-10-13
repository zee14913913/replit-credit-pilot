import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_loan_manager.db')

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    try:
        yield conn
    finally:
        conn.close()

def log_audit(user_id, action_type, entity_type=None, entity_id=None, description=None, ip_address=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs (user_id, action_type, entity_type, entity_id, description, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, action_type, entity_type, entity_id, description, ip_address))
        conn.commit()

def get_customer(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_customers():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers ORDER BY id')
        return [dict(row) for row in cursor.fetchall()]

def get_customer_cards(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM credit_cards WHERE customer_id = ? ORDER BY id', (customer_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_card_statements(card_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM statements WHERE card_id = ? ORDER BY statement_date DESC', (card_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_statement_transactions(statement_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transactions WHERE statement_id = ? ORDER BY transaction_date', (statement_id,))
        return [dict(row) for row in cursor.fetchall()]
