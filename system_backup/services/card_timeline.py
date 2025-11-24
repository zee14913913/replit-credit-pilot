"""
Card Timeline Service
Provides 12-month timeline view for credit cards based on statement_date
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import get_db

def get_card_12month_timeline(card_id):
    """
    Get 12-month timeline for a credit card showing statement distribution
    Returns list of 12 months with statement data
    """
    today = datetime.now()
    timeline = []
    
    # Generate 12 months (current month + past 11 months)
    for i in range(11, -1, -1):
        month_date = today - relativedelta(months=i)
        month_key = month_date.strftime("%Y-%m")
        month_display = month_date.strftime("%b %Y")
        
        timeline.append({
            'month_key': month_key,
            'month_display': month_display,
            'year': month_date.year,
            'month': month_date.month,
            'has_statement': False,
            'statement_id': None,
            'statement_date': None,
            'total_amount': 0.0,
            'transaction_count': 0,
            'is_confirmed': False
        })
    
    # Fetch statements for this card
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, statement_date, statement_total, is_confirmed,
                   strftime('%Y-%m', statement_date) as month_key
            FROM statements
            WHERE card_id = ? AND statement_date IS NOT NULL
            ORDER BY statement_date DESC
        ''', (card_id,))
        
        statements = cursor.fetchall()
        
        # Map statements to timeline
        for stmt in statements:
            stmt_month = stmt['month_key']
            
            # Find matching month in timeline
            for month_data in timeline:
                if month_data['month_key'] == stmt_month:
                    # Get transaction count
                    cursor.execute('''
                        SELECT COUNT(*) as count 
                        FROM transactions 
                        WHERE statement_id = ?
                    ''', (stmt['id'],))
                    txn_count = cursor.fetchone()['count']
                    
                    month_data['has_statement'] = True
                    month_data['statement_id'] = stmt['id']
                    month_data['statement_date'] = stmt['statement_date']
                    month_data['total_amount'] = stmt['statement_total'] or 0.0
                    month_data['transaction_count'] = txn_count
                    month_data['is_confirmed'] = bool(stmt['is_confirmed'])
                    break
    
    return timeline


def get_customer_cards_timeline(customer_id):
    """
    Get timeline for all cards of a customer
    Returns dict mapping card_id to 12-month timeline
    """
    timelines = {}
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, bank_name, card_number_last4 
            FROM credit_cards 
            WHERE customer_id = ?
            ORDER BY id DESC
        ''', (customer_id,))
        
        cards = cursor.fetchall()
        
        for card in cards:
            timelines[card['id']] = {
                'card_info': {
                    'id': card['id'],
                    'bank_name': card['bank_name'],
                    'last4': card['card_number_last4']
                },
                'timeline': get_card_12month_timeline(card['id'])
            }
    
    return timelines


def get_missing_months(card_id, months=12):
    """
    Get list of months that are missing statements for a card
    """
    timeline = get_card_12month_timeline(card_id)
    missing = [
        month for month in timeline 
        if not month['has_statement']
    ]
    return missing


def get_month_coverage_percentage(card_id):
    """
    Calculate what percentage of the last 12 months have statements
    """
    timeline = get_card_12month_timeline(card_id)
    with_statements = sum(1 for m in timeline if m['has_statement'])
    return (with_statements / 12) * 100 if timeline else 0
