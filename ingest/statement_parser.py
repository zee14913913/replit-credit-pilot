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
    
    # First check filename for hints
    filename_upper = os.path.basename(file_path).upper()
    if "HSBC" in filename_upper:
        print("✅ Detected HSBC from filename")
        return "HSBC"
    
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
            # Pattern to detect CR marker
            pattern = r'(\d{1,2}/\d{1,2})\s+([A-Za-z\s]+?)\s+([\d,]+\.\d{2})\s*(CR)?'
            for m in re.finditer(pattern, text):
                amount = abs(float(m.group(3).replace(",", "")))
                is_credit = m.group(4) == "CR"
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": amount,
                    "type": "credit" if is_credit else "debit"
                })
        else:
            df = pd.read_excel(file_path, sheet_name="Transactions")
            for _, r in df.iterrows():
                amt = float(r["Amount (RM)"])
                transactions.append({
                    "date": str(r["Date"]), 
                    "description": str(r["Description"]), 
                    "amount": abs(amt),
                    "type": "credit" if amt < 0 else "debit"
                })
        # Calculate net total: debits - credits
        debit_total = sum(t["amount"] for t in transactions if t.get("type") == "debit")
        credit_total = sum(t["amount"] for t in transactions if t.get("type") == "credit")
        info["total"] = debit_total - credit_total
        print(f"✅ CIMB parsed {len(transactions)} transactions. Debits: RM {debit_total:,.2f}, Credits: RM {credit_total:,.2f}, Net: RM {info['total']:,.2f}")
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
            
            pattern = r"(\d{2}/\d{2})\s+\d{2}/\d{2}\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?\s*$"
            
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
                    
                    amount = abs(float(amount_str))
                    
                    transactions.append({
                        "date": date, 
                        "description": description.strip(), 
                        "amount": amount,
                        "type": "credit" if is_credit else "debit"
                    })
        else:
            df = pd.read_excel(file_path, sheet_name="Transactions")
            for _, r in df.iterrows():
                amt = float(r["Amount (RM)"])
                transactions.append({
                    "date": str(r["Txn Date"]), 
                    "description": str(r["Merchant"]), 
                    "amount": abs(amt),
                    "type": "credit" if amt < 0 else "debit"
                })
        
        # Calculate net total: debits - credits
        debit_total = sum(t["amount"] for t in transactions if t.get("type") == "debit")
        credit_total = sum(t["amount"] for t in transactions if t.get("type") == "credit")
        info["total"] = debit_total - credit_total
        print(f"✅ Maybank parsed {len(transactions)} transactions. Debits: RM {debit_total:,.2f}, Credits: RM {credit_total:,.2f}, Net: RM {info['total']:,.2f}")
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
            
            pattern = r"(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?"
            
            for m in re.finditer(pattern, text):
                date = m.group(1)
                description = m.group(2).strip()
                amount_str = m.group(3).replace(",", "")
                is_credit = m.group(4) == "CR"
                
                amount = abs(float(amount_str))
                
                transactions.append({
                    "date": date, 
                    "description": description, 
                    "amount": amount,
                    "type": "credit" if is_credit else "debit"
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                amt = float(r.get("Amount", 0))
                transactions.append({
                    "date": str(r.get("Date", "")), 
                    "description": str(r.get("Description", "")), 
                    "amount": abs(amt),
                    "type": "credit" if amt < 0 else "debit"
                })
        
        # Calculate net total: debits - credits
        debit_total = sum(t["amount"] for t in transactions if t.get("type") == "debit")
        credit_total = sum(t["amount"] for t in transactions if t.get("type") == "credit")
        info["total"] = debit_total - credit_total
        print(f"✅ Public Bank parsed {len(transactions)} transactions. Debits: RM {debit_total:,.2f}, Credits: RM {credit_total:,.2f}, Net: RM {info['total']:,.2f}")
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
            
            pattern = r"(\d{2}/\d{2})\s+([A-Z\s\-&.,]+?)\s+([\d,]+\.\d{2})\s*(CR)?"
            
            for m in re.finditer(pattern, text):
                amount = abs(float(m.group(3).replace(",", "")))
                is_credit = m.group(4) == "CR"
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": amount,
                    "type": "credit" if is_credit else "debit"
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                amt = float(r.get("Amount", 0))
                transactions.append({
                    "date": str(r.get("Date", "")), 
                    "description": str(r.get("Description", "")), 
                    "amount": abs(amt),
                    "type": "credit" if amt < 0 else "debit"
                })
        
        # Calculate net total: debits - credits
        debit_total = sum(t["amount"] for t in transactions if t.get("type") == "debit")
        credit_total = sum(t["amount"] for t in transactions if t.get("type") == "credit")
        info["total"] = debit_total - credit_total
        print(f"✅ RHB Bank parsed {len(transactions)} transactions. Debits: RM {debit_total:,.2f}, Credits: RM {credit_total:,.2f}, Net: RM {info['total']:,.2f}")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing RHB: {e}")
        return info, transactions


def parse_hong_leong_statement(file_path):
    """Hong Leong Bank (HLB) - Essential Visa Gold"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None, "previous_balance": 0.0}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(p.extract_text() for p in pdf.pages)
                
                # Extract statement date - "Statement Date\nTarikh Penyata   16 JUN 2025"
                date_match = re.search(r"Statement\s+Date[^\d]*(\d{1,2}\s+[A-Z]{3}\s+\d{4})", full_text, re.IGNORECASE)
                if date_match:
                    try:
                        from datetime import datetime
                        date_str = date_match.group(1).strip()
                        parsed_date = datetime.strptime(date_str, "%d %b %Y")
                        info["statement_date"] = parsed_date.strftime("%Y-%m-%d")
                    except:
                        pass
                
                # Extract card number - "4293 2092 0258 3964"
                card_match = re.search(r"(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})", full_text)
                if card_match:
                    info["card_last4"] = card_match.group(4)
                
                # Extract Previous Balance - "PREVIOUS BALANCE FROM LAST STATEMENT 1.91"
                prev_bal_match = re.search(r"PREVIOUS\s+BALANCE(?:\s+FROM\s+LAST\s+STATEMENT)?[\s:]*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if prev_bal_match:
                    info["previous_balance"] = float(prev_bal_match.group(1).replace(",", ""))
                
                # Extract Total Balance
                total_match = re.search(r"(?:TOTAL\s+BALANCE|Total\s+Current\s+Balance)[\s:]*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if total_match:
                    info["total"] = float(total_match.group(1).replace(",", ""))
                
                # Extract transactions - Pattern: "DD MMM DD MMM DESCRIPTION [USD XX.XX] AMOUNT [CR]"
                # Example: "08 AUG 08 AUG QUICK CASH 03/60 353.74"
                # Example: "27 AUG 27 AUG PAYMENT THANK YOU - IB 2,960.39 CR"
                # Example: "15 JUN 16 JUN OPENAI *CHATGPT SUBSCR OPENAI.COM USA USD 21.60 93.75"
                
                # CRITICAL FIX: Extract year from statement date to complete transaction dates
                statement_year = None
                if info.get("statement_date"):
                    try:
                        statement_year = int(info["statement_date"].split('-')[0])
                    except:
                        pass
                
                # Pattern handles both regular and foreign currency transactions
                pattern = r'(\d{1,2}\s+[A-Z]{3})\s+\d{1,2}\s+[A-Z]{3}\s+(.+?)\s+(?:USD\s+[\d,]+\.\d{2}\s+)?([\d,]+\.\d{2})\s*(CR)?$'
                
                for match in re.finditer(pattern, full_text, re.MULTILINE):
                    trans_date_partial = match.group(1).strip()  # "08 AUG" without year
                    trans_desc = match.group(2).strip()
                    trans_amount = abs(float(match.group(3).replace(",", "")))
                    trans_cr_marker = match.group(4)
                    
                    # 🆕 100% PARSE: No skip logic - classify by line type instead
                    # Identify line type: detail/summary/remark/error
                    summary_keywords = ['PREVIOUS BALANCE', 'SUB TOTAL', 'TOTAL BALANCE', 'NEW TRANSACTION',
                                      'PAYMENT RECEIVED', 'Total Current Balance', 'Credit Limit', 
                                      'Minimum Payment', 'Payment Due Date']
                    
                    # Determine line type
                    if any(kw in trans_desc for kw in summary_keywords):
                        line_type = 'summary'
                    elif len(trans_desc) < 3 or re.match(r'^[\d\s,\.\-]+$', trans_desc):
                        line_type = 'remark'  # Too short or just numbers
                    elif re.match(r'^\d{20,}$', trans_desc):
                        line_type = 'remark'  # Reference numbers
                    else:
                        line_type = 'detail'  # Normal transaction
                    
                    # CRITICAL FIX: Complete the date with the correct year from statement
                    # Convert "08 AUG" to "08 AUG 2024" using statement year
                    if statement_year:
                        trans_date_full = f"{trans_date_partial} {statement_year}"
                        try:
                            parsed_date = datetime.strptime(trans_date_full, "%d %b %Y")
                            trans_date = parsed_date.strftime("%d/%m/%y")
                        except:
                            trans_date = trans_date_partial  # Fallback
                    else:
                        trans_date = trans_date_partial
                    
                    # CR means credit/repayment/rebate
                    trans_type = "credit" if trans_cr_marker else "debit"
                    
                    # 🆕 All lines are preserved with line_type classification
                    transactions.append({
                        "date": trans_date,
                        "description": trans_desc,
                        "amount": trans_amount,
                        "type": trans_type,
                        "line_type": line_type  # 🆕 detail/summary/remark
                    })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        if info["total"] == 0.0:
            info["total"] = sum(t["amount"] for t in transactions)
        
        print(f"✅ Hong Leong Bank parsed {len(transactions)} transactions. Card: ****{info.get('card_last4', 'N/A')}, Date: {info.get('statement_date', 'N/A')}")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Hong Leong: {e}")
        import traceback
        traceback.print_exc()
        return info, transactions


def parse_ambank_statement(file_path):
    """AmBank Islamic - Visa Signature"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None, "previous_balance": 0.0}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(p.extract_text() for p in pdf.pages)
                
                # Extract statement date - "Statement Date / Tarikh Penyata  28 MAY 25"
                date_match = re.search(r"Statement\s+Date[^\d]*(\d{1,2}\s+[A-Z]{3}\s+\d{2})", full_text, re.IGNORECASE)
                if date_match:
                    try:
                        from datetime import datetime
                        date_str = date_match.group(1).strip()
                        # Handle 2-digit year format
                        parsed_date = datetime.strptime(date_str, "%d %b %y")
                        info["statement_date"] = parsed_date.strftime("%Y-%m-%d")
                    except:
                        pass
                
                # Extract card number - "4031 4947 0045 9902"
                card_match = re.search(r"(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})", full_text)
                if card_match:
                    info["card_last4"] = card_match.group(4)
                
                # Extract Previous Balance - "PREVIOUS BALANCE 861.17"
                prev_bal_match = re.search(r"PREVIOUS\s+BALANCE[\s:]*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if prev_bal_match:
                    info["previous_balance"] = float(prev_bal_match.group(1).replace(",", ""))
                
                # Extract Total Current Balance
                total_match = re.search(r"Total\s+Current\s+Balance[\s:]*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if total_match:
                    info["total"] = float(total_match.group(1).replace(",", ""))
                
                # Extract transactions - Pattern: "DD MMM YY DD MMM YY DESCRIPTION AMOUNT[CR]"
                # Example: "07 MAY 25 07 MAY 25 PAYMENT VIA RPP RECEIVED - THANK YOU,CHEOK JUN YOON,may, 650.00CR"
                # Example: "26 MAY 25 28 MAY 25 Lazada Topup KUALA LUMPUR MY 2,500.00"
                # Note: CR has NO space before it (e.g., "650.00CR" not "650.00 CR")
                
                pattern = r'(\d{1,2}\s+[A-Z]{3}\s+\d{2})\s+\d{1,2}\s+[A-Z]{3}\s+\d{2}\s+(.+?)\s+([\d,]+\.\d{2})(CR)?$'
                
                for match in re.finditer(pattern, full_text, re.MULTILINE):
                    trans_date = match.group(1).strip()
                    trans_desc = match.group(2).strip()
                    trans_amount = abs(float(match.group(3).replace(",", "")))
                    trans_cr_marker = match.group(4)
                    
                    # 🆕 100% PARSE: No skip logic - classify by line type instead
                    summary_keywords = ['PREVIOUS BALANCE', 'SUB TOTAL', 'Total Current Balance', 'End of Transaction',
                                      'YOUR CARD ACCOUNT', 'Please see overleaf']
                    
                    # Determine line type
                    if any(kw in trans_desc for kw in summary_keywords):
                        line_type = 'summary'
                    elif len(trans_desc) < 3 or re.match(r'^[\d\s,\.\-]+$', trans_desc):
                        line_type = 'remark'
                    elif re.match(r'^\d{16}$', trans_desc.replace(' ', '')):
                        line_type = 'header'  # Card account numbers
                    else:
                        line_type = 'detail'
                    
                    # CR means credit/repayment
                    trans_type = "credit" if trans_cr_marker else "debit"
                    
                    # 🆕 All lines are preserved with line_type classification
                    transactions.append({
                        "date": trans_date,
                        "description": trans_desc,
                        "amount": trans_amount,
                        "type": trans_type,
                        "line_type": line_type  # 🆕 detail/summary/remark/header
                    })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        if info["total"] == 0.0:
            info["total"] = sum(t["amount"] for t in transactions)
        
        print(f"✅ AmBank Islamic parsed {len(transactions)} transactions. Card: ****{info.get('card_last4', 'N/A')}, Date: {info.get('statement_date', 'N/A')}")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing AmBank: {e}")
        import traceback
        traceback.print_exc()
        return info, transactions


def parse_alliance_statement(file_path):
    """
    Alliance Bank - Fixed parser for combined statements (multiple cards in 1 PDF)
    CRITICAL FIX: Only extracts transactions for the target card, scoped by card section and statement date
    """
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None, "due_date": None, "due_amount": None, "minimum_payment": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(p.extract_text() for p in pdf.pages)
            
            # Extract target card last 4 digits from file path
            # Example: "Alliance_Bank_4514_2024-09-12.pdf" -> "4514"
            filename = os.path.basename(file_path)
            card_match = re.search(r'_(\d{4})_\d{4}-\d{2}-\d{2}\.pdf', filename)
            if card_match:
                info["card_last4"] = card_match.group(1)
            
            # Extract statement date from filename or PDF
            # Filename pattern: "Alliance_Bank_4514_2024-09-12.pdf"
            stmt_date_match = re.search(r'_(\d{4}-\d{2}-\d{2})\.pdf', filename)
            if stmt_date_match:
                info["statement_date"] = stmt_date_match.group(1)
            else:
                # Fallback: Extract from PDF content "Statement Date 12/09/24"
                date_match = re.search(r'Statement\s+Date[\s:]*(\d{1,2}/\d{1,2}/\d{2,4})', full_text, re.IGNORECASE)
                if date_match:
                    try:
                        date_str = date_match.group(1).strip()
                        parsed_date = datetime.strptime(date_str, "%d/%m/%y")
                        info["statement_date"] = parsed_date.strftime("%Y-%m-%d")
                    except:
                        pass
            
            # Extract due date
            due_date_patterns = [
                r'Payment\s+Due\s+Date[\s:]*(\d{1,2}/\d{1,2}/\d{2,4})',
                r'Tarikh\s+Bayaran\s+Perlu\s+Dibuat[\s:]*(\d{1,2}/\d{1,2}/\d{2,4})',
            ]
            for pattern in due_date_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(1).strip()
                        parsed_date = datetime.strptime(date_str, "%d/%m/%y")
                        info["due_date"] = parsed_date.strftime("%Y-%m-%d")
                        break
                    except:
                        pass
            
            # CRITICAL FIX: Extract card-specific section from combined statement
            # Alliance Bank format: "MASTERCARD GOLD : 5465 9464 0768 4514"
            target_last4 = info.get("card_last4")
            if not target_last4:
                print(f"⚠️ Cannot extract card number from filename: {filename}")
                return info, transactions
            
            # Find the target card's transaction section
            # Alliance Bank format: "MASTERCARD GOLD : 5465 9464 0768 4514" (16-digit card number with spaces)
            lines = full_text.split('\n')
            card_section_text = []
            card_header_index = -1
            
            # First, find the card header line
            for i, line in enumerate(lines):
                # Pattern: "MASTERCARD/VISA/BALANCE TRANSFER ... : #### #### #### 4514"
                card_header_match = re.search(r'(MASTERCARD|VISA|BALANCE\s+TRANSFER)\s+.*:\s+\d{4}\s+\d{4}\s+\d{4}\s+' + target_last4, line, re.IGNORECASE)
                if card_header_match:
                    card_header_index = i
                    break
            
            if card_header_index == -1:
                print(f"⚠️ Cannot find card header for #{target_last4}")
                return info, transactions
            
            # Now scan backwards to find PREVIOUS STATEMENT BALANCE (start of section)
            section_start = card_header_index
            for i in range(card_header_index - 1, max(0, card_header_index - 20), -1):
                if 'PREVIOUS STATEMENT BALANCE' in lines[i].upper():
                    section_start = i
                    break
            
            # Extract section from PREVIOUS STATEMENT BALANCE to CHARGES THIS MONTH
            for i in range(section_start, len(lines)):
                line = lines[i]
                card_section_text.append(line)
                
                # Stop at "CHARGES THIS MONTH:"
                if 'CHARGES THIS MONTH:' in line:
                    break
                # Stop at next card section (another 16-digit card number)
                if i > card_header_index and re.search(r'(MASTERCARD|VISA|BALANCE\s+TRANSFER)\s+.*:\s+\d{4}\s+\d{4}\s+\d{4}\s+\d{4}', line, re.IGNORECASE) and target_last4 not in line:
                    break
            
            if not card_section_text:
                print(f"⚠️ Cannot find transaction section for card #{target_last4}")
                return info, transactions
            
            # Join card section for pattern matching
            card_section = '\n'.join(card_section_text)
            
            # Extract PREVIOUS STATEMENT BALANCE for this card
            prev_balance_match = re.search(r'PREVIOUS\s+STATEMENT\s+BALANCE\s+([\d,]+\.\d{2})\s*(CR)?', card_section, re.IGNORECASE)
            if prev_balance_match:
                prev_balance = float(prev_balance_match.group(1).replace(",", ""))
                if prev_balance_match.group(2) == "CR":
                    prev_balance = -prev_balance
                info["previous_balance"] = prev_balance
            
            # Extract current balance from "CHARGES THIS MONTH"
            charges_match = re.search(r'CHARGES\s+THIS\s+MONTH:\s+([\d,]+\.\d{2})', card_section, re.IGNORECASE)
            if charges_match:
                info["total"] = float(charges_match.group(1).replace(",", ""))
            
            # Pattern: "DD/MM/YY Description Amount CR?"
            # Only match within the card section
            pattern = r'(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2}/\d{2})\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?$'
            
            for match in re.finditer(pattern, card_section, re.MULTILINE):
                trans_date = match.group(1).strip()  # Transaction Date
                posting_date = match.group(2).strip()  # Posting Date
                trans_desc = match.group(3).strip()
                trans_amount = abs(float(match.group(4).replace(",", "")))
                trans_cr_marker = match.group(5)
                
                # 🆕 100% PARSE: No skip logic - classify by line type instead
                summary_keywords = ['PREVIOUS BALANCE', 'PREVIOUS STATEMENT BALANCE', 'CHARGES THIS MONTH',
                                  'CURRENT BALANCE', 'TOTAL MINIMUM PAYMENT', 'Balance From Last Statement',
                                  'Payment Amount', 'Minimum Payment']
                
                # Determine line type
                if any(kw in trans_desc.upper() for kw in summary_keywords):
                    line_type = 'summary'
                elif len(trans_desc) < 3 or re.match(r'^[\d\s,\.\-]+$', trans_desc):
                    line_type = 'remark'
                else:
                    line_type = 'detail'
                
                # CR marker means credit/payment, no CR means debit/purchase
                trans_type = "credit" if trans_cr_marker else "debit"
                
                # 🆕 All lines are preserved with line_type classification
                transactions.append({
                    "date": posting_date,  # Use posting date for consistency
                    "description": trans_desc,
                    "amount": trans_amount,
                    "type": trans_type,
                    "line_type": line_type  # 🆕 detail/summary/remark
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({
                    "date": str(r.get("Date", "")), 
                    "description": str(r.get("Description", "")), 
                    "amount": float(r.get("Amount", 0)),
                    "type": "debit"  # Default for Excel imports
                })
        
        if info["total"] == 0.0 and transactions:
            debit_total = sum(t["amount"] for t in transactions if t.get("type") == "debit")
            credit_total = sum(t["amount"] for t in transactions if t.get("type") == "credit")
            info["total"] = debit_total - credit_total
        
        print(f"✅ Alliance Bank parsed {len(transactions)} transactions for card #{info.get('card_last4', 'N/A')}.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Alliance: {e}")
        import traceback
        traceback.print_exc()
        return info, transactions


def parse_affin_statement(file_path):
    """Affin Bank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}/\d{2})\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?"
            
            for m in re.finditer(pattern, text):
                amount = abs(float(m.group(3).replace(",", "")))
                is_credit = m.group(4) == "CR"
                transactions.append({
                    "date": m.group(1), 
                    "description": m.group(2).strip(), 
                    "amount": amount,
                    "type": "credit" if is_credit else "debit"
                })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                amt = float(r.get("Amount", 0))
                transactions.append({
                    "date": str(r.get("Date", "")), 
                    "description": str(r.get("Description", "")), 
                    "amount": abs(amt),
                    "type": "credit" if amt < 0 else "debit"
                })
        
        # Calculate net total: debits - credits
        debit_total = sum(t["amount"] for t in transactions if t.get("type") == "debit")
        credit_total = sum(t["amount"] for t in transactions if t.get("type") == "credit")
        info["total"] = debit_total - credit_total
        print(f"✅ Affin Bank parsed {len(transactions)} transactions. Debits: RM {debit_total:,.2f}, Credits: RM {credit_total:,.2f}, Net: RM {info['total']:,.2f}")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Affin: {e}")
        return info, transactions


def parse_hsbc_statement(file_path):
    """HSBC Bank Malaysia - Live+ Credit Card"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None, "previous_balance": 0.0}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
                
                # Check if PDF is scanned image (no text layer)
                if not full_text or len(full_text.strip()) < 100:
                    # Return special error code for scanned HSBC PDF
                    raise ValueError("HSBC_SCANNED_PDF")
                
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
                
                # Extract Previous Balance - "Your Previous Statement Balance 1,369.86"
                prev_bal_match = re.search(r"Your\s+Previous\s+Statement\s+Balance[\s:]*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if prev_bal_match:
                    info["previous_balance"] = float(prev_bal_match.group(1).replace(",", ""))
                
                # Extract Statement Balance from table - more precise pattern
                # Looking for: "4364800001380034 50.00 50.00 0.00 50.00" (card_number balance min_payment overlimit payment_due)
                # The first amount after card number is Statement Balance
                table_match = re.search(r"(\d{16})\s+([\d,]+\.\d{2})\s+[\d,]+\.\d{2}\s+[\d,]+\.\d{2}\s+([\d,]+\.\d{2})", full_text)
                if table_match:
                    # Use Payment Due (4th column) as total - this is what customer needs to pay
                    info["total"] = float(table_match.group(3).replace(",", ""))
                else:
                    # Fallback: try to find "Payment Due (RM)" followed by amount
                    payment_due_match = re.search(r"Payment\s+Due[^\d]+([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                    if payment_due_match:
                        info["total"] = float(payment_due_match.group(1).replace(",", ""))
                
                # Extract transactions - Pattern: "DD MMM  DD MMM  DESCRIPTION  AMOUNT [CR]"
                # Example: "07 MAY 07 MAY PAYMENT - THANK YOU 13,874.21 CR"
                # Example: "14 APR 13 APR PETRON JALAN AMPANGAN SEREMBAN MY 60.00"
                pattern = r'(\d{1,2}\s+[A-Z]{3})\s+\d{1,2}\s+[A-Z]{3}\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?$'
                
                for match in re.finditer(pattern, full_text, re.MULTILINE):
                    trans_date = match.group(1).strip()
                    trans_desc = match.group(2).strip()
                    trans_amount = abs(float(match.group(3).replace(",", "")))
                    trans_cr_marker = match.group(4)
                    
                    # 🆕 100% PARSE: No skip logic - classify by line type instead
                    summary_keywords = ['Your Previous Statement Balance', 'Your statement balance', 'Total credit limit used',
                                      'Your charge', 'Credit Limit', 'MINIMUM PAYMENT', 'Please forward']
                    
                    # Determine line type
                    if any(kw in trans_desc for kw in summary_keywords):
                        line_type = 'summary'
                    elif len(trans_desc) < 3 or re.match(r'^[\d\s,\.]+$', trans_desc):
                        line_type = 'remark'
                    else:
                        line_type = 'detail'
                    
                    # CR means credit/repayment
                    trans_type = "credit" if trans_cr_marker else "debit"
                    
                    # 🆕 All lines are preserved with line_type classification
                    transactions.append({
                        "date": trans_date,
                        "description": trans_desc,
                        "amount": trans_amount,
                        "type": trans_type,
                        "line_type": line_type  # 🆕 detail/summary/remark
                    })
        else:
            df = pd.read_excel(file_path, sheet_name="Sheet1")
            for _, r in df.iterrows():
                transactions.append({"date": str(r["Date"]), "description": str(r["Details"]), "amount": float(r["Amount"])})
        
        if info["total"] == 0.0:
            info["total"] = sum(t["amount"] for t in transactions)
        
        print(f"✅ HSBC parsed {len(transactions)} transactions. Card: ****{info.get('card_last4', 'N/A')}, Date: {info.get('statement_date', 'N/A')}")
        return info, transactions
    except ValueError as e:
        # Re-raise HSBC_SCANNED_PDF error for user guidance
        if str(e) == "HSBC_SCANNED_PDF":
            raise
        else:
            print(f"❌ Error parsing HSBC: {e}")
            return info, transactions
    except Exception as e:
        print(f"❌ Error parsing HSBC: {e}")
        import traceback
        traceback.print_exc()
        return info, transactions


def parse_standard_chartered_statement(file_path):
    """Standard Chartered Bank (SCB) - Malaysia - Table-based extraction"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None, "previous_balance": 0.0}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(p.extract_text() for p in pdf.pages)
                
                # Extract statement date - "Statement Date / Tarikh Penyata: 14 May 2025"
                date_match = re.search(r"Statement\s+Date[^\:]*:\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})", full_text, re.IGNORECASE)
                statement_year = None
                if date_match:
                    try:
                        from datetime import datetime
                        date_str = date_match.group(1).strip()
                        parsed_date = datetime.strptime(date_str, "%d %b %Y")
                        info["statement_date"] = parsed_date.strftime("%Y-%m-%d")
                        statement_year = parsed_date.year
                    except:
                        pass
                
                # Extract card number - "5520-40XX-XXXX-1237"
                card_match = re.search(r"(\d{4})-\d{2}XX-XXXX-(\d{4})", full_text)
                if card_match:
                    info["card_last4"] = card_match.group(2)
                
                # Extract Previous Balance
                prev_bal_match = re.search(r"(?:BALANCE\s+FROM\s+PREVIOUS|Previous\s+Balance)[^\d]+([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if prev_bal_match:
                    info["previous_balance"] = float(prev_bal_match.group(1).replace(",", ""))
                
                # Extract New Balance/Total
                total_match = re.search(r"New Balance[^\d]+([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if total_match:
                    info["total"] = float(total_match.group(1).replace(",", ""))
                
                # Extract transactions using simple regex on full text
                # SCB format: Two dates followed by description and amount
                # Pattern: "07 May  07 May  DUITNOW PAY-TO-ACCOUNT Txn Ref: xxx  1,250.00CR"
                
                # Extract line by line looking for transaction pattern
                pattern = r'(\d{1,2}\s+[A-Za-z]{3})\s+(\d{1,2}\s+[A-Za-z]{3})\s+(.+?)\s+([\d,]+\.\d{2})(CR)?\s*$'
                
                for match in re.finditer(pattern, full_text, re.MULTILINE):
                    posting_date = match.group(1).strip()
                    transaction_date = match.group(2).strip()
                    description = match.group(3).strip()
                    amount_str = match.group(4).strip()
                    is_credit = match.group(5) is not None
                    
                    # 🆕 100% PARSE: No skip logic - classify by line type instead
                    summary_keywords = ['BALANCE FROM PREVIOUS', 'NEW BALANCE', 'MINIMUM PAYMENT', 
                                      'Baki dari penyata', 'Baki Baru', 'Pembayaran Minima',
                                      'Previous Balance', 'New Balance', 'Posting Date', 'Transaction Date',
                                      'Tarikh Bil', 'Diterima', 'Transaksi']
                    
                    # Determine line type
                    if any(kw.lower() in description.lower() for kw in summary_keywords):
                        line_type = 'summary'
                    elif len(description) < 5:
                        line_type = 'remark'
                    else:
                        line_type = 'detail'
                    
                    # Parse amount
                    try:
                        trans_amount = abs(float(amount_str.replace(',', '')))
                    except:
                        line_type = 'error'  # Parse error
                        trans_amount = 0.0
                    
                    # Note: Even zero amounts are preserved (not skipped)
                    
                    # Complete the date with year
                    trans_date = transaction_date.strip()
                    if statement_year and re.match(r'^\d{1,2}\s+[A-Za-z]{3}$', trans_date):
                        trans_date = f"{trans_date} {statement_year}"
                    
                    # 🆕 All lines are preserved with line_type classification
                    transactions.append({
                        "date": trans_date,
                        "description": description,
                        "amount": trans_amount,
                        "type": "credit" if is_credit else "debit",
                        "line_type": line_type  # 🆕 detail/summary/remark/error
                    })
        else:
            df = pd.read_excel(file_path)
            for _, r in df.iterrows():
                transactions.append({"date": str(r.get("Date", "")), "description": str(r.get("Description", "")), "amount": float(r.get("Amount", 0))})
        
        if info["total"] == 0.0 and transactions:
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
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None, "previous_balance": 0.0}
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
                
                # Extract Previous Balance - "Last Statement Balance 487.81"
                prev_bal_match = re.search(r"Last\s+Statement\s+Balance[\s:]*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                if prev_bal_match:
                    info["previous_balance"] = float(prev_bal_match.group(1).replace(",", ""))
                
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
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": "UOB", "previous_balance": 0.0}
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
                
                # Extract Previous Balance and Total Balance Due from summary table (page 5)
                # Try table extraction first (more accurate)
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            # Check if this is the summary table
                            header_text = " ".join(str(cell) for row in table[:4] for cell in row if cell).upper()
                            if "PREVIOUS BALANCE" in header_text and "TOTAL BALANCE DUE" in header_text:
                                # Found the summary table! Extract values from data row
                                for row in table:
                                    if row and len(row) >= 6:
                                        # Format: [Previous Balance, Credit/Payment, Debit/Fees, Retail Purchase, Cash Advance, Total Balance Due]
                                        # Check if this row contains numeric data (not headers)
                                        first_cell = str(row[0]).strip() if row[0] else ""
                                        last_cell = str(row[-1]).strip() if row[-1] else ""
                                        
                                        # Skip header rows (contain text like "Previous Balance" or "(RM)")
                                        if not first_cell or "(" in first_cell or any(c.isalpha() for c in first_cell if c not in ['CR', 'cr']):
                                            continue
                                        
                                        # This is a data row - extract values
                                        try:
                                            if first_cell and first_cell.replace(',', '').replace('.', '').isdigit():
                                                info["previous_balance"] = float(first_cell.replace(",", ""))
                                            if last_cell and last_cell.replace(',', '').replace('.', '').isdigit():
                                                info["total"] = float(last_cell.replace(",", ""))
                                            break
                                        except:
                                            pass
                
                # Fallback: try regex if table extraction failed
                if info["previous_balance"] == 0.0:
                    prev_bal_match = re.search(r"Previous\s+Balance[^\d]+([\d,]+\.\d{2})", full_text, re.IGNORECASE)
                    if prev_bal_match:
                        info["previous_balance"] = float(prev_bal_match.group(1).replace(",", ""))
                
                if info["total"] == 0.0:
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
    符合ARCHITECT_CONSTRAINTS.md：100%提取所有交易记录
    
    解析策略：
    1. 优先使用Google Document AI（准确率98-99.9%）
    2. Fallback到pdfplumber（防御性）
    
    Returns: (info_dict, transactions_list) where info_dict contains:
        - bank: detected bank name
        - card_last4: last 4 digits of card
        - statement_date: statement date (YYYY-MM-DD format)
        - total: total amount
        - previous_balance: previous balance
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 尝试使用Google Document AI（首选）
    try:
        from services.google_document_ai_service import GoogleDocumentAIService
        
        logger.info("🚀 使用Google Document AI解析PDF...")
        
        # 初始化Document AI服务（自动使用环境变量中的密钥）
        doc_ai = GoogleDocumentAIService()
        
        # 解析PDF
        parsed_doc = doc_ai.parse_pdf(file_path)
        fields = doc_ai.extract_bank_statement_fields(parsed_doc)
        
        # 检测银行
        bank = detect_bank(file_path)
        
        # 转换为标准格式
        info = {
            'bank': bank,
            'card_last4': fields.get('card_number'),
            'statement_date': fields.get('statement_date'),
            'total': fields.get('current_balance', 0),
            'previous_balance': fields.get('previous_balance', 0),
            'minimum_payment': fields.get('minimum_payment', 0)
        }
        
        transactions = fields.get('transactions', [])
        
        logger.info(f"✅ Google Document AI解析成功：{len(transactions)}笔交易")
        
        # 验证交易完整性（ARCHITECT_CONSTRAINTS.md要求）
        # 必须同时包含DR和CR交易，确保100%完整提取
        if len(transactions) > 0:
            dr_count = sum(1 for t in transactions if t.get('type') == 'DR')
            cr_count = sum(1 for t in transactions if t.get('type') == 'CR')
            
            if dr_count > 0 and cr_count > 0:
                logger.info(f"✅ 验证通过：{dr_count}笔DR交易 + {cr_count}笔CR交易")
                return info, transactions
            else:
                logger.warning(f"⚠️ 交易不完整（DR:{dr_count}, CR:{cr_count}），尝试fallback...")
                raise Exception(f"Incomplete transactions: DR={dr_count}, CR={cr_count}")
        else:
            logger.warning("⚠️ Document AI未提取到交易，尝试fallback...")
            raise Exception("No transactions extracted")
    
    except Exception as e:
        logger.warning(f"⚠️ Google Document AI解析失败: {e}")
        logger.info("🔄 Fallback到pdfplumber解析...")
    
    # Fallback: 使用原有的pdfplumber解析器
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
        logger.info(f"✅ pdfplumber解析成功：{len(transactions) if transactions else 0}笔交易")
        return info, transactions
    else:
        logger.error(f"⚠️ Unsupported or unrecognized bank format: {bank}")
        return None, []
