import pdfplumber
import pandas as pd
import openpyxl
import re
from datetime import datetime
import os
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

def detect_bank(file_path):
    """
    Enhanced bank detection supporting 15 Malaysian banks
    Covers 95%+ of Malaysian credit card market
    """
    bank = "UNKNOWN"
    try:
        ext = os.path.splitext(file_path.lower())[1]
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                text = pdf.pages[0].extract_text()
                
                if text and len(text.strip()) > 50:
                    text_upper = text.upper()
                    
                    if "MAYBANK" in text_upper or "MALAYAN BANKING" in text_upper:
                        bank = "MAYBANK"
                    elif "CIMB" in text_upper:
                        bank = "CIMB"
                    elif "PUBLIC BANK" in text_upper:
                        bank = "PUBLIC BANK"
                    elif "RHB BANK" in text_upper or "RHB" in text_upper:
                        bank = "RHB"
                    elif "HONG LEONG" in text_upper or "HONGLEONG" in text_upper:
                        bank = "HONG LEONG"
                    elif "AMBANK" in text_upper or "AM BANK" in text_upper:
                        bank = "AMBANK"
                    elif "ALLIANCE BANK" in text_upper or "ALLIANCE" in text_upper:
                        bank = "ALLIANCE"
                    elif "AFFIN BANK" in text_upper or "AFFIN" in text_upper:
                        bank = "AFFIN"
                    elif "HSBC" in text_upper:
                        bank = "HSBC"
                    elif "STANDARD CHARTERED" in text_upper or "STANCHART" in text_upper:
                        bank = "STANDARD CHARTERED"
                    elif "OCBC" in text_upper:
                        bank = "OCBC"
                    elif "UOB" in text_upper or "UNITED OVERSEAS" in text_upper:
                        bank = "UOB"
                    elif "BANK ISLAM" in text_upper:
                        bank = "BANK ISLAM"
                    elif "BANK RAKYAT" in text_upper:
                        bank = "BANK RAKYAT"
                    elif "BANK MUAMALAT" in text_upper or "MUAMALAT" in text_upper:
                        bank = "BANK MUAMALAT"
                else:
                    print("🧠 Using OCR for bank detection...")
                    images = convert_from_path(file_path, first_page=1, last_page=1, dpi=300)
                    if images:
                        ocr_text = pytesseract.image_to_string(images[0]).upper()
                        
                        if "MAYBANK" in ocr_text or "MALAYAN BANKING" in ocr_text:
                            bank = "MAYBANK"
                        elif "CIMB" in ocr_text:
                            bank = "CIMB"
                        elif "PUBLIC BANK" in ocr_text or "PUBLIC" in ocr_text:
                            bank = "PUBLIC BANK"
                        elif "RHB" in ocr_text:
                            bank = "RHB"
                        elif "HONG LEONG" in ocr_text or "HONGLEONG" in ocr_text:
                            bank = "HONG LEONG"
                        elif "AMBANK" in ocr_text or "AM BANK" in ocr_text:
                            bank = "AMBANK"
                        elif "ALLIANCE" in ocr_text:
                            bank = "ALLIANCE"
                        elif "AFFIN" in ocr_text:
                            bank = "AFFIN"
                        elif "HSBC" in ocr_text:
                            bank = "HSBC"
                        elif "STANDARD CHARTERED" in ocr_text or "STANCHART" in ocr_text:
                            bank = "STANDARD CHARTERED"
                        elif "OCBC" in ocr_text:
                            bank = "OCBC"
                        elif "UOB" in ocr_text or "UNITED OVERSEAS" in ocr_text:
                            bank = "UOB"
                        elif "BANK ISLAM" in ocr_text:
                            bank = "BANK ISLAM"
                        elif "BANK RAKYAT" in ocr_text:
                            bank = "BANK RAKYAT"
                        elif "MUAMALAT" in ocr_text:
                            bank = "BANK MUAMALAT"
                        
        elif ext in [".xlsx", ".xls"]:
            excel = pd.ExcelFile(file_path)
            sheet_names = [name.upper() for name in excel.sheet_names]
            
            if "CIMB" in str(sheet_names):
                bank = "CIMB"
            elif "MAYBANK" in str(sheet_names):
                bank = "MAYBANK"
            elif "PUBLIC" in str(sheet_names):
                bank = "PUBLIC BANK"
            elif "RHB" in str(sheet_names):
                bank = "RHB"
            elif "HONG LEONG" in str(sheet_names) or "HONGLEONG" in str(sheet_names):
                bank = "HONG LEONG"
            elif "AMBANK" in str(sheet_names):
                bank = "AMBANK"
            elif "ALLIANCE" in str(sheet_names):
                bank = "ALLIANCE"
            elif "AFFIN" in str(sheet_names):
                bank = "AFFIN"
            elif "HSBC" in str(sheet_names):
                bank = "HSBC"
            elif "STANDARD CHARTERED" in str(sheet_names) or "STANCHART" in str(sheet_names):
                bank = "STANDARD CHARTERED"
            elif "OCBC" in str(sheet_names):
                bank = "OCBC"
            elif "UOB" in str(sheet_names):
                bank = "UOB"
            elif "ISLAM" in str(sheet_names):
                bank = "BANK ISLAM"
            elif "RAKYAT" in str(sheet_names):
                bank = "BANK RAKYAT"
            elif "MUAMALAT" in str(sheet_names):
                bank = "BANK MUAMALAT"
                
    except Exception as e:
        print(f"⚠️ Error detecting bank: {e}")
    
    print(f"✅ Detected Bank: {bank}")
    return bank


def parse_cimb_statement(file_path):
    """CIMB Bank - Malaysia's 2nd largest bank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            for m in re.findall(r"(\d{1,2}/\d{1,2})\s+([A-Za-z\s]+)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})", text):
                transactions.append({"date": m[0], "description": m[1].strip(), "amount": float(m[2].replace(",", ""))})
        else:
            df = pd.read_excel(file_path, sheet_name="Transactions")
            for _, r in df.iterrows():
                transactions.append({"date": str(r["Date"]), "description": str(r["Description"]), "amount": float(r["Amount (RM)"])})
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ CIMB parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing CIMB: {e}")
        return info, transactions


def parse_maybank_statement(file_path):
    """Maybank - Malaysia's largest bank (40% market share)"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+\d{2}/\d{2}\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})(CR)?\s*$"
            
            for line in text.split('\n'):
                m = re.search(pattern, line)
                if m:
                    date = m.group(1)
                    description = m.group(2).strip()
                    amount_str = m.group(3).replace(",", "")
                    is_credit = m.group(4) == "CR"
                    
                    description = re.sub(r'\s+[A-Z\s]+MY\s*$', '', description)
                    description = re.sub(r'\s+:[0-9A-Z/]+\s*$', '', description)
                    description = re.sub(r'\s+[0-9A-Z]+\s+MY\s*$', '', description)
                    
                    amount = float(amount_str)
                    if is_credit:
                        amount = -amount
                    
                    transactions.append({
                        "date": date, 
                        "description": description.strip(), 
                        "amount": amount
                    })
        else:
            df = pd.read_excel(file_path, sheet_name="Transactions")
            for _, r in df.iterrows():
                transactions.append({"date": str(r["Txn Date"]), "description": str(r["Merchant"]), "amount": float(r["Amount (RM)"])})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ Maybank parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Maybank: {e}")
        return info, transactions


def parse_public_bank_statement(file_path):
    """Public Bank - Malaysia's 3rd largest bank (15% market share)"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})(CR)?"
            
            for m in re.finditer(pattern, text):
                date = m.group(1)
                description = m.group(2).strip()
                amount_str = m.group(3).replace(",", "")
                is_credit = m.group(4) == "CR"
                
                amount = float(amount_str)
                if is_credit:
                    amount = -amount
                
                transactions.append({"date": date, "description": description, "amount": amount})
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ Public Bank parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Public Bank: {e}")
        return info, transactions


def parse_rhb_statement(file_path):
    """RHB Bank - Malaysia's 4th largest bank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+([A-Z\s\-&.,]+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})"
            
            for m in re.finditer(pattern, text):
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": float(m.group(3).replace(",", ""))
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ RHB Bank parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing RHB: {e}")
        return info, transactions


def parse_hong_leong_statement(file_path):
    """Hong Leong Bank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})"
            
            for m in re.finditer(pattern, text):
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": float(m.group(3).replace(",", ""))
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ Hong Leong Bank parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Hong Leong: {e}")
        return info, transactions


def parse_ambank_statement(file_path):
    """AmBank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})"
            
            for m in re.finditer(pattern, text):
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": float(m.group(3).replace(",", ""))
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ AmBank parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing AmBank: {e}")
        return info, transactions


def parse_alliance_statement(file_path):
    """Alliance Bank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})"
            
            for m in re.finditer(pattern, text):
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": float(m.group(3).replace(",", ""))
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ Alliance Bank parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Alliance: {e}")
        return info, transactions


def parse_affin_statement(file_path):
    """Affin Bank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})"
            
            for m in re.finditer(pattern, text):
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": float(m.group(3).replace(",", ""))
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ Affin Bank parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Affin: {e}")
        return info, transactions


def parse_hsbc_statement(file_path):
    """HSBC Bank Malaysia - Live+ Credit Card"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(p.extract_text() for p in pdf.pages)
                
                # Extract statement date - "Statement Date 13 May 2025"
                date_match = re.search(r"Statement\s+Date[\s:]*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})", full_text, re.IGNORECASE)
                if date_match:
                    try:
                        from datetime import datetime
                        date_str = date_match.group(1).strip()
                        parsed_date = datetime.strptime(date_str, "%d %b %Y")
                        info["statement_date"] = parsed_date.strftime("%Y-%m-%d")
                    except:
                        pass
                
                # Extract card number - "4364800001380034" or "4364 8000 0138 0034"
                card_match = re.search(r"(\d{4})\s*(\d{4})\s*(\d{4})\s*(\d{4})", full_text)
                if card_match:
                    info["card_last4"] = card_match.group(4)
                
                # Extract Statement Balance
                total_match = re.search(r"(?:Statement\s+Balance|Your\s+statement\s+balance)[\s:]*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if total_match:
                    info["total"] = float(total_match.group(1).replace(",", ""))
                
                # Extract transactions - Pattern: "DD MMM  DD MMM  DESCRIPTION  AMOUNT [CR]"
                # Example: "07 MAY 07 MAY PAYMENT - THANK YOU 13,874.21 CR"
                # Example: "14 APR 13 APR PETRON JALAN AMPANGAN SEREMBAN MY 60.00"
                pattern = r'(\d{1,2}\s+[A-Z]{3})\s+\d{1,2}\s+[A-Z]{3}\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?$'
                
                for match in re.finditer(pattern, full_text, re.MULTILINE):
                    trans_date = match.group(1).strip()
                    trans_desc = match.group(2).strip()
                    trans_amount = abs(float(match.group(3).replace(",", "")))
                    trans_cr_marker = match.group(4)
                    
                    # Skip summary/header lines
                    skip_keywords = ['Your Previous Statement Balance', 'Your statement balance', 'Total credit limit used',
                                   'Your charge', 'Credit Limit', 'MINIMUM PAYMENT', 'Please forward']
                    if any(kw in trans_desc for kw in skip_keywords):
                        continue
                    
                    # Skip if description is too short or just numbers
                    if len(trans_desc) < 3 or re.match(r'^[\d\s,\.]+$', trans_desc):
                        continue
                    
                    # CR means credit/repayment
                    trans_type = "credit" if trans_cr_marker else "debit"
                    
                    transactions.append({
                        "date": trans_date,
                        "description": trans_desc,
                        "amount": trans_amount,
                        "type": trans_type
                    })
        else:
            df = pd.read_excel(file_path, sheet_name="Sheet1")
            for _, r in df.iterrows():
                transactions.append({"date": str(r["Date"]), "description": str(r["Details"]), "amount": float(r["Amount"])})
        
        if info["total"] == 0.0:
            info["total"] = sum(t["amount"] for t in transactions)
        
        print(f"✅ HSBC parsed {len(transactions)} transactions. Card: ****{info.get('card_last4', 'N/A')}, Date: {info.get('statement_date', 'N/A')}")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing HSBC: {e}")
        import traceback
        traceback.print_exc()
        return info, transactions


def parse_standard_chartered_statement(file_path):
    """Standard Chartered Bank (SCB) - Malaysia"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(p.extract_text() for p in pdf.pages)
                
                # Extract statement date - "Statement Date / Tarikh Penyata: 14 May 2025"
                date_match = re.search(r"Statement\s+Date[^\:]*:\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})", full_text, re.IGNORECASE)
                if date_match:
                    try:
                        from datetime import datetime
                        date_str = date_match.group(1).strip()
                        parsed_date = datetime.strptime(date_str, "%d %b %Y")
                        info["statement_date"] = parsed_date.strftime("%Y-%m-%d")
                    except:
                        pass
                
                # Extract card number - "5520-40XX-XXXX-1237"
                card_match = re.search(r"(\d{4})-\d{2}XX-XXXX-(\d{4})", full_text)
                if card_match:
                    info["card_last4"] = card_match.group(2)
                
                # Extract New Balance/Total
                total_match = re.search(r"New Balance[^\d]+([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if total_match:
                    info["total"] = float(total_match.group(1).replace(",", ""))
                
                # Extract transactions - Pattern: "07 May       DUITNOW PAY-TO-ACCOUNT       1,250.00CR"
                # Use greedy match to get the last amount on each line
                pattern = r'(\d{1,2}\s+[A-Za-z]{3})\s+(.+)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:CR)?$'
                
                for match in re.finditer(pattern, full_text, re.MULTILINE | re.IGNORECASE):
                    trans_date = match.group(1).strip()
                    trans_desc = match.group(2).strip()
                    trans_amount = abs(float(match.group(3).replace(",", "")))
                    
                    # Filter out header/summary lines
                    skip_keywords = ['previous balance', 'new balance', 'minimum payment', 'payment due', 
                                   'baki', 'jumlah', 'pembayaran', 'statement', 'total']
                    if any(kw in trans_desc.lower() for kw in skip_keywords):
                        continue
                    
                    # Skip if description is too short or just numbers
                    if len(trans_desc) < 5 or re.match(r'^[\d\s,\.]+$', trans_desc):
                        continue
                    
                    # CR means credit/repayment
                    trans_type = "credit" if 'CR' in match.group(0).upper() else "debit"
                    
                    transactions.append({
                        "date": trans_date,
                        "description": trans_desc,
                        "amount": trans_amount,
                        "type": trans_type
                    })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        if info["total"] == 0.0:
            info["total"] = sum(t["amount"] for t in transactions)
        
        print(f"✅ Standard Chartered parsed {len(transactions)} transactions. Card: ****{info.get('card_last4', 'N/A')}, Date: {info.get('statement_date', 'N/A')}")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Standard Chartered: {e}")
        import traceback
        traceback.print_exc()
        return info, transactions


def parse_ocbc_statement(file_path):
    """OCBC Bank (Malaysia) Berhad - GE Mastercard"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(p.extract_text() for p in pdf.pages)
                
                # Extract statement date - "Statement Date 13 May 2025"
                date_match = re.search(r"Statement\s+Date[\s:]*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})", full_text, re.IGNORECASE)
                if date_match:
                    try:
                        from datetime import datetime
                        date_str = date_match.group(1).strip()
                        parsed_date = datetime.strptime(date_str, "%d %b %Y")
                        info["statement_date"] = parsed_date.strftime("%Y-%m-%d")
                    except:
                        pass
                
                # Extract card number - "5401-6200-0093-3506"
                card_match = re.search(r"(\d{4})-(\d{4})-(\d{4})-(\d{4})", full_text)
                if card_match:
                    info["card_last4"] = card_match.group(4)
                
                # Extract Statement Balance Due
                total_match = re.search(r"Statement\s+Balance\s+Due[\s:]*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if total_match:
                    info["total"] = float(total_match.group(1).replace(",", ""))
                
                # Extract transactions - Pattern: "DD/MM/YYYY  DD/MM/YYYY  DESCRIPTION  DR/CR  AMOUNT"
                # Example: "30/04/2025 30/04/2025 GREATEASTERN1060542015 DR 385.00"
                pattern = r'(\d{2}/\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}\s+(.+?)\s+(DR|CR)\s+([\d,]+\.\d{2})'
                
                for match in re.finditer(pattern, full_text, re.IGNORECASE):
                    trans_date = match.group(1).strip()
                    trans_desc = match.group(2).strip()
                    trans_type_marker = match.group(3).upper()
                    trans_amount = abs(float(match.group(4).replace(",", "")))
                    
                    # Skip summary/header lines
                    skip_keywords = ['BALANCE OF LAST MONTH', 'NEW BALANCE', 'Retail Interest', 
                                   'MINIMUM PAYMENT', 'PAYMENT DUE', 'TOTAL']
                    if any(kw.upper() in trans_desc.upper() for kw in skip_keywords):
                        continue
                    
                    # Skip if description is too short
                    if len(trans_desc) < 3:
                        continue
                    
                    # DR = Debit (消费), CR = Credit (还款/返现)
                    trans_type = "credit" if trans_type_marker == "CR" else "debit"
                    
                    # Convert date format from DD/MM/YYYY to DD MMM
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(trans_date, "%d/%m/%Y")
                        formatted_date = date_obj.strftime("%d %b")
                    except:
                        formatted_date = trans_date
                    
                    transactions.append({
                        "date": formatted_date,
                        "description": trans_desc,
                        "amount": trans_amount,
                        "type": trans_type
                    })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        if info["total"] == 0.0:
            info["total"] = sum(t["amount"] for t in transactions)
        
        print(f"✅ OCBC parsed {len(transactions)} transactions. Card: ****{info.get('card_last4', 'N/A')}, Date: {info.get('statement_date', 'N/A')}")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing OCBC: {e}")
        import traceback
        traceback.print_exc()
        return info, transactions


def parse_uob_statement(file_path):
    """UOB - United Overseas Bank (Malaysia/Singapore)"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": "UOB"}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(p.extract_text() for p in pdf.pages)
                
                # Extract card number
                card_patterns = [
                    r"\*\*(\d{4})-\d{4}-\d{4}-(\d{4})\*\*",  # **4141-7000-0828-3530**
                    r"Card\s+(?:No|Number|Ending)?[\s:]*[*X\d\s-]*(\d{4})"
                ]
                for pattern in card_patterns:
                    card_match = re.search(pattern, full_text, re.IGNORECASE)
                    if card_match:
                        info["card_last4"] = card_match.group(card_match.lastindex)
                        break
                
                # Extract statement date - "Statement Date 13 MAY 25"
                date_match = re.search(r"Statement\s+Date[\s:]*(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s+\d{2,4})", full_text, re.IGNORECASE)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(date_str.upper().strip(), "%d %b %y") if len(date_str.split()[-1]) == 2 else datetime.strptime(date_str.upper().strip(), "%d %B %Y")
                        info["statement_date"] = parsed_date.strftime("%Y-%m-%d")
                    except:
                        pass
                
                # Extract Total Balance Due
                total_match = re.search(r"Total Balance Due[^\d]+([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if total_match:
                    info["total"] = float(total_match.group(1).replace(",", ""))
                
                # Extract transactions using table extraction
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 2:
                            # Check if this is the transaction table
                            header_row = " ".join(str(cell) for cell in table[0] if cell).upper()
                            if "TRANSACTION DATE" in header_row or "TRANSACTION DESCRIPTION" in header_row or "TARIKH TRANSAKSI" in header_row:
                                # Found transaction table
                                for row in table[3:]:  # Skip headers
                                    if row and len(row) >= 2:
                                        date_cell = str(row[0]) if row[0] else ""
                                        desc_cell = str(row[1]) if row[1] else ""
                                        amount_cell = str(row[-1]) if row[-1] else ""
                                        
                                        # Parse transactions from combined cell format
                                        # Format: "07 MAY PAYMENT REC'D WITH THANKS-DUITNOW 1,763.62 CR"
                                        lines = desc_cell.split('\n')
                                        for line in lines:
                                            # Match: DD MMM DESCRIPTION AMOUNT [CR]
                                            trans_match = re.match(r'(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s+CR)?', line, re.IGNORECASE)
                                            if trans_match:
                                                trans_date = trans_match.group(1)
                                                trans_desc = trans_match.group(2).strip()
                                                trans_amount = abs(float(trans_match.group(3).replace(",", "")))
                                                
                                                # CR means credit/repayment (type marker, not negative)
                                                trans_type = "credit" if 'CR' in line.upper() else "debit"
                                                
                                                transactions.append({
                                                    "date": trans_date,
                                                    "description": trans_desc,
                                                    "amount": trans_amount,
                                                    "type": trans_type
                                                })
                
                # Fallback: text-based extraction if table extraction fails
                if len(transactions) == 0:
                    print("⚠️ UOB: Table extraction failed, trying text-based extraction")
                    # Match pattern: "07 MAY PAYMENT REC'D WITH THANKS-DUITNOW 1,763.62 CR"
                    # Use greedy match (.+) to capture everything, then get the LAST amount
                    pattern = r'(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))\s+(.+)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s+CR)?$'
                    for match in re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE):
                        trans_date = match.group(1)
                        trans_desc = match.group(2).strip()
                        trans_amount = abs(float(match.group(3).replace(",", "")))
                        
                        # Filter out non-transaction lines (like headers, totals, due dates)
                        skip_keywords = ['minimum payment due', 'payment due date', 'statement date', 'credit limit', 'balance due']
                        if any(kw in trans_desc.lower() for kw in skip_keywords):
                            continue
                        
                        if len(trans_desc) > 5 and not re.match(r'^\d+[\s,\.]*$', trans_desc):
                            # CR means credit/repayment (type marker, not negative)
                            trans_type = "credit" if 'CR' in match.group(0).upper() else "debit"
                            
                            transactions.append({
                                "date": trans_date,
                                "description": trans_desc,
                                "amount": trans_amount,
                                "type": trans_type
                            })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        if info["total"] == 0.0:
            info["total"] = sum(t["amount"] for t in transactions)
        
        print(f"✅ UOB parsed {len(transactions)} transactions. Card: ****{info['card_last4']}, Date: {info['statement_date']}, Total: RM {info['total']:.2f}")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing UOB: {e}")
        import traceback
        traceback.print_exc()
        return info, transactions


def parse_bank_islam_statement(file_path):
    """Bank Islam - Islamic banking"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})"
            
            for m in re.finditer(pattern, text):
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": float(m.group(3).replace(",", ""))
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ Bank Islam parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Bank Islam: {e}")
        return info, transactions


def parse_bank_rakyat_statement(file_path):
    """Bank Rakyat - Cooperative bank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})"
            
            for m in re.finditer(pattern, text):
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": float(m.group(3).replace(",", ""))
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ Bank Rakyat parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Bank Rakyat: {e}")
        return info, transactions


def parse_bank_muamalat_statement(file_path):
    """Bank Muamalat - Islamic banking"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})"
            
            for m in re.finditer(pattern, text):
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": float(m.group(3).replace(",", ""))
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ Bank Muamalat parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Bank Muamalat: {e}")
        return info, transactions


def parse_statement_auto(file_path):
    """
    Auto-detect and parse credit card statements
    Supports 15 Malaysian banks covering 95%+ of market
    Returns: (info_dict, transactions_list) where info_dict contains:
        - bank: detected bank name
        - card_last4: last 4 digits of card
        - statement_date: statement date (YYYY-MM-DD format)
        - total: total amount
    """
    bank = detect_bank(file_path)
    
    bank_parsers = {
        "MAYBANK": parse_maybank_statement,
        "CIMB": parse_cimb_statement,
        "PUBLIC BANK": parse_public_bank_statement,
        "RHB": parse_rhb_statement,
        "HONG LEONG": parse_hong_leong_statement,
        "AMBANK": parse_ambank_statement,
        "ALLIANCE": parse_alliance_statement,
        "AFFIN": parse_affin_statement,
        "HSBC": parse_hsbc_statement,
        "STANDARD CHARTERED": parse_standard_chartered_statement,
        "OCBC": parse_ocbc_statement,
        "UOB": parse_uob_statement,
        "BANK ISLAM": parse_bank_islam_statement,
        "BANK RAKYAT": parse_bank_rakyat_statement,
        "BANK MUAMALAT": parse_bank_muamalat_statement
    }
    
    if bank in bank_parsers:
        info, transactions = bank_parsers[bank](file_path)
        if info and isinstance(info, dict):
            info['bank'] = bank
        return info, transactions
    else:
        print(f"⚠️ Unsupported or unrecognized bank format: {bank}")
        return None, []
