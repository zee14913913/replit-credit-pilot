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
    """HSBC - International bank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            for m in re.findall(r"(\d{2}\s[A-Za-z]+)\s+([A-Za-z\s\-&.,]+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})", text):
                transactions.append({"date": m[0], "description": m[1].strip(), "amount": float(m[2].replace(",", ""))})
        else:
            df = pd.read_excel(file_path, sheet_name="Sheet1")
            for _, r in df.iterrows():
                transactions.append({"date": str(r["Date"]), "description": str(r["Details"]), "amount": float(r["Amount"])})
        info["total"] = sum(t["amount"] for t in transactions)
        print(f"✅ HSBC parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing HSBC: {e}")
        return info, transactions


def parse_standard_chartered_statement(file_path):
    """Standard Chartered - Premium international bank"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": None}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            pattern = r"(\d{2}\s[A-Za-z]{3})\s+(.+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})"
            
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
        print(f"✅ Standard Chartered parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing Standard Chartered: {e}")
        return info, transactions


def parse_ocbc_statement(file_path):
    """OCBC Bank - Singapore bank"""
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
        print(f"✅ OCBC parsed {len(transactions)} transactions.")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing OCBC: {e}")
        return info, transactions


def parse_uob_statement(file_path):
    """UOB - United Overseas Bank (Singapore)"""
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": "UOB"}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            
            card_num_match = re.search(r"Card\s+(?:No|Number|Ending)?[\s:]*[*X\d\s-]*(\d{4})", text, re.IGNORECASE)
            if card_num_match:
                info["card_last4"] = card_num_match.group(1)
            
            date_match = re.search(r"Statement\s+Date[\s:]*(\d{2}[/-]\d{2}[/-]\d{2,4})", text, re.IGNORECASE)
            if not date_match:
                date_match = re.search(r"(?:Date|As of)[\s:]*(\d{2}[/-]\d{2}[/-]\d{2,4})", text, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1).replace("/", "-")
                try:
                    from datetime import datetime
                    if len(date_str.split("-")[-1]) == 2:
                        parsed_date = datetime.strptime(date_str, "%d-%m-%y")
                    else:
                        parsed_date = datetime.strptime(date_str, "%d-%m-%Y")
                    info["statement_date"] = parsed_date.strftime("%Y-%m-%d")
                except:
                    info["statement_date"] = date_str
            
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
        print(f"✅ UOB parsed {len(transactions)} transactions. Card: ****{info['card_last4']}, Date: {info['statement_date']}")
        return info, transactions
    except Exception as e:
        print(f"❌ Error parsing UOB: {e}")
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
