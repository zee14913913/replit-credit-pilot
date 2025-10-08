import requests
from datetime import datetime
from db.database import get_db

BNM_API_BASE = "https://api.bnm.gov.my"

def fetch_opr_data():
    try:
        response = requests.get(f"{BNM_API_BASE}/public/opr", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                return {
                    'rate_value': float(latest.get('rate', 0)),
                    'effective_date': latest.get('date', datetime.now().strftime('%Y-%m-%d'))
                }
    except Exception as e:
        print(f"Error fetching OPR data: {e}")
    
    return {
        'rate_value': 3.00,
        'effective_date': datetime.now().strftime('%Y-%m-%d')
    }

def fetch_sbr_data():
    try:
        response = requests.get(f"{BNM_API_BASE}/public/base-rate", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                return {
                    'rate_value': float(latest.get('rate', 0)),
                    'effective_date': latest.get('date', datetime.now().strftime('%Y-%m-%d'))
                }
    except Exception as e:
        print(f"Error fetching SBR data: {e}")
    
    return {
        'rate_value': 3.15,
        'effective_date': datetime.now().strftime('%Y-%m-%d')
    }

def save_bnm_rates():
    opr = fetch_opr_data()
    sbr = fetch_sbr_data()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bnm_rates (rate_type, rate_value, effective_date)
            VALUES (?, ?, ?)
        ''', ('OPR', opr['rate_value'], opr['effective_date']))
        
        cursor.execute('''
            INSERT INTO bnm_rates (rate_type, rate_value, effective_date)
            VALUES (?, ?, ?)
        ''', ('SBR', sbr['rate_value'], sbr['effective_date']))
        
        conn.commit()
    
    return {'opr': opr, 'sbr': sbr}

def get_latest_rates():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM bnm_rates 
            WHERE rate_type = 'OPR' 
            ORDER BY fetched_at DESC LIMIT 1
        ''')
        opr_row = cursor.fetchone()
        opr = dict(opr_row) if opr_row else {'rate_value': 3.00, 'effective_date': datetime.now().strftime('%Y-%m-%d')}
        
        cursor.execute('''
            SELECT * FROM bnm_rates 
            WHERE rate_type = 'SBR' 
            ORDER BY fetched_at DESC LIMIT 1
        ''')
        sbr_row = cursor.fetchone()
        sbr = dict(sbr_row) if sbr_row else {'rate_value': 3.15, 'effective_date': datetime.now().strftime('%Y-%m-%d')}
        
        return {'opr': opr, 'sbr': sbr}

def fetch_bnm_rates():
    """Simplified version for financial optimizer - returns just rate values"""
    rates = get_latest_rates()
    return {
        'opr': rates['opr'].get('rate_value', 3.00) if isinstance(rates['opr'], dict) else 3.00,
        'sbr': rates['sbr'].get('rate_value', 3.15) if isinstance(rates['sbr'], dict) else 3.15
    }

def add_banking_news(bank_name, news_type, title, content, effective_date=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO banking_news (bank_name, news_type, title, content, effective_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (bank_name, news_type, title, content, effective_date or datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        return cursor.lastrowid

def get_all_banking_news(limit=20):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM banking_news 
            ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
