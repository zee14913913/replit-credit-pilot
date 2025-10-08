"""
Create customer authentication tables
"""
import sqlite3

def create_auth_tables():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # Customer logins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    
    # Customer sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_valid INTEGER DEFAULT 1,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Customer authentication tables created successfully")

if __name__ == "__main__":
    create_auth_tables()
