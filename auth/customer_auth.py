"""
Customer Authentication System
Handles customer login, registration, and session management
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from db.database import get_db

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash

def create_customer_login(customer_id: int, email: str, password: str) -> dict:
    """Create login credentials for a customer"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM customer_logins WHERE email = ?", (email,))
        if cursor.fetchone():
            return {"success": False, "error": "Email already registered"}
        
        password_hash = hash_password(password)
        
        cursor.execute("""
            INSERT INTO customer_logins (customer_id, email, password_hash)
            VALUES (?, ?, ?)
        """, (customer_id, email, password_hash))
        
        conn.commit()
        return {"success": True, "message": "Registration successful"}

def authenticate_customer(email: str, password: str) -> dict:
    """Authenticate customer and create session"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cl.id, cl.customer_id, cl.password_hash, cl.is_active, c.name
            FROM customer_logins cl
            JOIN customers c ON cl.customer_id = c.id
            WHERE cl.email = ?
        """, (email,))
        
        result = cursor.fetchone()
        
        if not result:
            return {"success": False, "error": "Invalid email or password"}
        
        login_id, customer_id, password_hash, is_active, customer_name = result
        
        if not is_active:
            return {"success": False, "error": "Account is deactivated"}
        
        if not verify_password(password, password_hash):
            return {"success": False, "error": "Invalid email or password"}
        
        # Create session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)
        
        cursor.execute("""
            INSERT INTO customer_sessions (customer_id, session_token, expires_at)
            VALUES (?, ?, ?)
        """, (customer_id, session_token, expires_at))
        
        # Update last login
        cursor.execute("""
            UPDATE customer_logins SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        """, (login_id,))
        
        conn.commit()
        
        return {
            "success": True,
            "session_token": session_token,
            "customer_id": customer_id,
            "customer_name": customer_name
        }

def verify_session(session_token: str) -> dict:
    """Verify session token and return customer info"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cs.customer_id, c.name, cs.expires_at, cs.is_valid
            FROM customer_sessions cs
            JOIN customers c ON cs.customer_id = c.id
            WHERE cs.session_token = ?
        """, (session_token,))
        
        result = cursor.fetchone()
        
        if not result:
            return {"success": False, "error": "Invalid session"}
        
        customer_id, customer_name, expires_at, is_valid = result
        
        if not is_valid:
            return {"success": False, "error": "Session has been invalidated"}
        
        # Check if session expired
        expires_at_dt = datetime.fromisoformat(expires_at)
        if expires_at_dt < datetime.now():
            return {"success": False, "error": "Session expired"}
        
        return {
            "success": True,
            "customer_id": customer_id,
            "customer_name": customer_name
        }

def logout_customer(session_token: str) -> dict:
    """Invalidate customer session"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE customer_sessions SET is_valid = 0 WHERE session_token = ?
        """, (session_token,))
        
        conn.commit()
        
        return {"success": True, "message": "Logged out successfully"}

def get_customer_data_summary(customer_id: int) -> dict:
    """Get customer's data summary for their portal"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get customer info
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        # Get credit cards
        cursor.execute("SELECT * FROM credit_cards WHERE customer_id = ?", (customer_id,))
        credit_cards = cursor.fetchall()
        
        # Get statements
        cursor.execute("""
            SELECT * FROM statements WHERE customer_id = ? ORDER BY statement_date DESC
        """, (customer_id,))
        statements = cursor.fetchall()
        
        # Get total spending
        cursor.execute("""
            SELECT SUM(t.amount) as total_spending
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            WHERE s.customer_id = ? AND t.transaction_type = 'debit'
        """, (customer_id,))
        total_spending = cursor.fetchone()[0] or 0
        
        return {
            "customer": customer,
            "credit_cards": credit_cards,
            "statements": statements,
            "total_spending": float(total_spending)
        }
