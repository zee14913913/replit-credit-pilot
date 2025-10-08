import schedule
import time
from datetime import datetime, timedelta
from db.database import get_db

def check_and_send_reminders():
    today = datetime.now().date()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, c.card_number_last4, c.bank_name, cu.name, cu.email
            FROM repayment_reminders r
            JOIN credit_cards c ON r.card_id = c.id
            JOIN customers cu ON c.customer_id = cu.id
            WHERE r.is_paid = 0
        ''')
        reminders = cursor.fetchall()
        
        for reminder in reminders:
            due_date = datetime.strptime(reminder['due_date'], '%Y-%m-%d').date()
            days_until_due = (due_date - today).days
            
            if days_until_due == 7 and not reminder['reminder_sent_7days']:
                send_reminder(reminder, 7)
                cursor.execute('''
                    UPDATE repayment_reminders 
                    SET reminder_sent_7days = 1 
                    WHERE id = ?
                ''', (reminder['id'],))
                conn.commit()
                
            elif days_until_due == 3 and not reminder['reminder_sent_3days']:
                send_reminder(reminder, 3)
                cursor.execute('''
                    UPDATE repayment_reminders 
                    SET reminder_sent_3days = 1 
                    WHERE id = ?
                ''', (reminder['id'],))
                conn.commit()
                
            elif days_until_due == 1 and not reminder['reminder_sent_1day']:
                send_reminder(reminder, 1)
                cursor.execute('''
                    UPDATE repayment_reminders 
                    SET reminder_sent_1day = 1 
                    WHERE id = ?
                ''', (reminder['id'],))
                conn.commit()

def send_reminder(reminder, days_before):
    message = f"""
    ========================================
    PAYMENT REMINDER - {days_before} DAY(S) BEFORE DUE
    ========================================
    
    Customer: {reminder['name']}
    Bank: {reminder['bank_name']}
    Card: ****{reminder['card_number_last4']}
    Amount Due: RM {reminder['amount_due']:.2f}
    Due Date: {reminder['due_date']}
    
    Please ensure payment is made before the due date.
    ========================================
    """
    
    print(message)

def mark_as_paid(reminder_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE repayment_reminders 
            SET is_paid = 1, paid_date = ? 
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d'), reminder_id))
        conn.commit()

def get_pending_reminders():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, c.card_number_last4, c.bank_name, cu.name
            FROM repayment_reminders r
            JOIN credit_cards c ON r.card_id = c.id
            JOIN customers cu ON c.customer_id = cu.id
            WHERE r.is_paid = 0
            ORDER BY r.due_date
        ''')
        return [dict(row) for row in cursor.fetchall()]

def create_reminder(card_id, due_date, amount_due):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO repayment_reminders (card_id, due_date, amount_due)
            VALUES (?, ?, ?)
        ''', (card_id, due_date, amount_due))
        conn.commit()
        return cursor.lastrowid
