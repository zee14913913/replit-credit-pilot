import pdfplumber
import pandas as pd
import re
from datetime import datetime
import os

def parse_pdf_statement(file_path):
    transactions = []
    statement_info = {
        'statement_date': None,
        'total': 0,
        'card_last4': None
    }
    
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            
            date_pattern = r'Statement Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            date_match = re.search(date_pattern, text, re.IGNORECASE)
            if date_match:
                statement_info['statement_date'] = date_match.group(1)
            
            total_pattern = r'Total[:\s]+(?:RM)?[\s]*([0-9,]+\.?\d*)'
            total_match = re.search(total_pattern, text, re.IGNORECASE)
            if total_match:
                statement_info['total'] = float(total_match.group(1).replace(',', ''))
            
            card_pattern = r'(?:Card.*?)?(\d{4})\s*$'
            card_match = re.search(card_pattern, text, re.MULTILINE)
            if card_match:
                statement_info['card_last4'] = card_match.group(1)
            
            transaction_pattern = r'(\d{1,2}/\d{1,2})\s+([A-Za-z\s&\'\-\.]+?)\s+([\d,]+\.?\d{2})'
            transactions_found = re.findall(transaction_pattern, text)
            
            for trans in transactions_found:
                date_str, description, amount_str = trans
                current_year = datetime.now().year
                trans_date = f"{date_str}/{current_year}"
                
                transactions.append({
                    'date': trans_date,
                    'description': description.strip(),
                    'amount': float(amount_str.replace(',', ''))
                })
    
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return None, None
    
    return statement_info, transactions

def parse_excel_statement(file_path):
    transactions = []
    statement_info = {
        'statement_date': None,
        'total': 0,
        'card_last4': None
    }
    
    try:
        df = pd.read_excel(file_path)
        
        if 'Statement Date' in df.columns:
            statement_info['statement_date'] = str(df['Statement Date'].iloc[0])
        elif 'Date' in df.columns and len(df) > 0:
            statement_info['statement_date'] = str(df['Date'].iloc[0])
        
        if 'Card' in df.columns:
            card_val = str(df['Card'].iloc[0])
            statement_info['card_last4'] = card_val[-4:] if len(card_val) >= 4 else card_val
        
        date_col = None
        desc_col = None
        amount_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'date' in col_lower and not date_col:
                date_col = col
            elif any(x in col_lower for x in ['description', 'merchant', 'details']) and not desc_col:
                desc_col = col
            elif any(x in col_lower for x in ['amount', 'total', 'debit']) and not amount_col:
                amount_col = col
        
        if date_col and desc_col and amount_col:
            for _, row in df.iterrows():
                if pd.notna(row[date_col]) and pd.notna(row[amount_col]):
                    amount = float(row[amount_col]) if isinstance(row[amount_col], (int, float)) else float(str(row[amount_col]).replace(',', '').replace('RM', '').strip())
                    
                    transactions.append({
                        'date': str(row[date_col]),
                        'description': str(row[desc_col]) if pd.notna(row[desc_col]) else 'Unknown',
                        'amount': amount
                    })
        
        if transactions:
            statement_info['total'] = sum(t['amount'] for t in transactions)
    
    except Exception as e:
        print(f"Error parsing Excel: {e}")
        return None, None
    
    return statement_info, transactions

def parse_statement(file_path, file_type):
    if file_type.lower() == 'pdf':
        return parse_pdf_statement(file_path)
    elif file_type.lower() in ['xlsx', 'xls', 'excel']:
        return parse_excel_statement(file_path)
    else:
        return None, None
