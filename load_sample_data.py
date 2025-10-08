from db.init_db import init_database
from db.database import get_db
from datetime import datetime, timedelta

def load_sample_data():
    init_database()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO customers (name, email, phone, monthly_income)
            VALUES (?, ?, ?, ?)
        ''', ('Ahmad Abdullah', 'ahmad@email.com', '+60123456789', 8500.00))
        customer1_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO customers (name, email, phone, monthly_income)
            VALUES (?, ?, ?, ?)
        ''', ('Siti Nurhaliza', 'siti@email.com', '+60198765432', 6200.00))
        customer2_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, card_type, credit_limit, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer1_id, 'Maybank', '1234', 'Platinum', 15000.00, 15))
        card1_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, card_type, credit_limit, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer1_id, 'CIMB', '5678', 'Gold', 10000.00, 20))
        card2_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, card_type, credit_limit, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer2_id, 'Public Bank', '9012', 'Platinum', 12000.00, 10))
        card3_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, card_type, credit_limit, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer2_id, 'Hong Leong', '3456', 'Classic', 8000.00, 25))
        card4_id = cursor.lastrowid
        
        statement_date = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO statements (card_id, statement_date, statement_total, file_type, validation_score, is_confirmed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (card1_id, statement_date, 2458.50, 'sample', 1.0, 1))
        statement1_id = cursor.lastrowid
        
        sample_transactions_1 = [
            ('2024-10-01', 'TESCO SUPERMARKET', 156.80, 'Groceries', 0.9),
            ('2024-10-02', 'GRAB FOOD DELIVERY', 38.50, 'Food & Dining', 0.9),
            ('2024-10-03', 'SHELL PETROL STATION', 85.00, 'Transport', 0.9),
            ('2024-10-05', 'PAVILION KL SHOPPING', 420.00, 'Shopping', 0.8),
            ('2024-10-07', 'STARBUCKS COFFEE', 28.90, 'Food & Dining', 0.9),
            ('2024-10-08', 'UNIFI MONTHLY BILL', 189.00, 'Bills & Utilities', 0.9),
            ('2024-10-10', 'NETFLIX SUBSCRIPTION', 55.00, 'Entertainment', 0.9),
            ('2024-10-12', 'GUARDIAN PHARMACY', 67.30, 'Healthcare', 0.9),
            ('2024-10-15', 'LAZADA ONLINE SHOPPING', 245.00, 'Shopping', 0.8),
            ('2024-10-18', 'MAMAK RESTAURANT', 45.00, 'Food & Dining', 0.9),
            ('2024-10-20', 'PETRONAS FUEL', 95.00, 'Transport', 0.9),
            ('2024-10-22', 'AEON MALL', 380.00, 'Shopping', 0.8),
            ('2024-10-25', 'GSC CINEMA', 58.00, 'Entertainment', 0.9),
            ('2024-10-27', 'JAYA GROCER', 195.00, 'Groceries', 0.9),
            ('2024-10-28', 'GRAB TRANSPORT', 32.00, 'Transport', 0.9),
            ('2024-10-30', 'KOPITIAM BREAKFAST', 18.00, 'Food & Dining', 0.9),
            ('2024-10-31', 'ASTRO BILL', 150.00, 'Bills & Utilities', 0.9)
        ]
        
        for trans in sample_transactions_1:
            cursor.execute('''
                INSERT INTO transactions (statement_id, transaction_date, description, amount, category, category_confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (statement1_id, trans[0], trans[1], trans[2], trans[3], trans[4]))
        
        cursor.execute('''
            INSERT INTO statements (card_id, statement_date, statement_total, file_type, validation_score, is_confirmed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (card3_id, statement_date, 1876.30, 'sample', 1.0, 1))
        statement2_id = cursor.lastrowid
        
        sample_transactions_2 = [
            ('2024-10-02', 'MYDIN SUPERMARKET', 189.50, 'Groceries', 0.9),
            ('2024-10-04', 'MAXIS BILL', 98.00, 'Bills & Utilities', 0.9),
            ('2024-10-06', 'VILLAGE GROCER', 234.00, 'Groceries', 0.9),
            ('2024-10-08', 'SUSHI KING', 125.80, 'Food & Dining', 0.9),
            ('2024-10-10', 'WATSONS PHARMACY', 78.50, 'Healthcare', 0.9),
            ('2024-10-12', 'SHOPEE PURCHASE', 315.00, 'Shopping', 0.8),
            ('2024-10-14', 'TNB ELECTRICITY', 156.00, 'Bills & Utilities', 0.9),
            ('2024-10-16', 'KLINIK KESIHATAN', 45.00, 'Healthcare', 0.9),
            ('2024-10-18', 'IKEA FURNITURE', 450.00, 'Shopping', 0.8),
            ('2024-10-20', 'SPOTIFY PREMIUM', 19.90, 'Entertainment', 0.9),
            ('2024-10-22', 'NASI KANDAR', 28.50, 'Food & Dining', 0.9),
            ('2024-10-24', 'INDAH WATER', 8.00, 'Bills & Utilities', 0.9),
            ('2024-10-26', 'TGV CINEMA', 48.00, 'Entertainment', 0.9),
            ('2024-10-28', '99 SPEEDMART', 80.10, 'Groceries', 0.9)
        ]
        
        for trans in sample_transactions_2:
            cursor.execute('''
                INSERT INTO transactions (statement_id, transaction_date, description, amount, category, category_confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (statement2_id, trans[0], trans[1], trans[2], trans[3], trans[4]))
        
        due_date_1 = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO repayment_reminders (card_id, due_date, amount_due, reminder_sent_7days)
            VALUES (?, ?, ?, ?)
        ''', (card1_id, due_date_1, 2458.50, 1))
        
        due_date_2 = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO repayment_reminders (card_id, due_date, amount_due)
            VALUES (?, ?, ?)
        ''', (card3_id, due_date_2, 1876.30))
        
        cursor.execute('''
            INSERT INTO banking_news (bank_name, news_type, title, content, effective_date)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Maybank', 'Interest Rate', 'Fixed Deposit Rate Increase', 
              'Maybank increases FD rates by 0.25% for 12-month tenure', 
              datetime.now().strftime('%Y-%m-%d')))
        
        cursor.execute('''
            INSERT INTO banking_news (bank_name, news_type, title, content, effective_date)
            VALUES (?, ?, ?, ?, ?)
        ''', ('CIMB', 'Promotion', 'Cashback Campaign', 
              'Get 10% cashback on all online purchases up to RM100',
              datetime.now().strftime('%Y-%m-%d')))
        
        cursor.execute('''
            INSERT INTO banking_news (bank_name, news_type, title, content, effective_date)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Public Bank', 'Interest Rate', 'Home Loan Rate Reduction',
              'Public Bank reduces home loan interest rates by 0.15%',
              (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')))
        
        cursor.execute('''
            INSERT INTO bnm_rates (rate_type, rate_value, effective_date)
            VALUES (?, ?, ?)
        ''', ('OPR', 3.00, datetime.now().strftime('%Y-%m-%d')))
        
        cursor.execute('''
            INSERT INTO bnm_rates (rate_type, rate_value, effective_date)
            VALUES (?, ?, ?)
        ''', ('SBR', 3.15, datetime.now().strftime('%Y-%m-%d')))
        
        conn.commit()
        print("Sample data loaded successfully!")
        print(f"- Created 2 customers: Ahmad Abdullah and Siti Nurhaliza")
        print(f"- Created 4 credit cards (Maybank, CIMB, Public Bank, Hong Leong)")
        print(f"- Loaded 31 sample transactions")
        print(f"- Created 2 payment reminders")
        print(f"- Added 3 banking news items")
        print(f"- Initialized BNM rates (OPR: 3.00%, SBR: 3.15%)")

if __name__ == "__main__":
    load_sample_data()
