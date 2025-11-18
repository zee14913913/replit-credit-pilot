
"""
Apply CTOS Applications Migration
"""
import sqlite3
import os

DB_PATH = 'db/smart_loan_manager.db'
MIGRATION_PATH = 'db/migrations/017_create_ctos_applications.sql'

def apply_migration():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    if not os.path.exists(MIGRATION_PATH):
        print(f"❌ Migration file not found at {MIGRATION_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        with open(MIGRATION_PATH, 'r') as f:
            migration_sql = f.read()
        
        cursor.executescript(migration_sql)
        conn.commit()
        
        print("✅ CTOS applications table created successfully")
        
        # Verify table creation
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ctos_applications'")
        if cursor.fetchone():
            print("✅ Table verified in database")
        else:
            print("❌ Table verification failed")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    apply_migration()
