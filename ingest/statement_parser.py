import pdfplumber
import pandas as pd
import openpyxl
import re
from datetime import datetime
import os

def detect_bank(file_path):
    bank = "UNKNOWN"
    try:
        ext = os.path.splitext(file_path.lower())[1]
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                text = pdf.pages[0].extract_text().upper()
                if "MAYBANK" in text:
                    bank = "MAYBANK"
                elif "CIMB" in text:
                    bank = "CIMB"
                elif "HSBC" in text:
                    bank = "HSBC"
        elif ext in [".xlsx", ".xls"]:
            excel = pd.ExcelFile(file_path)
            sheet_names = [name.upper() for name in excel.sheet_names]
            if "CIMB" in sheet_names or "SUMMARY" in sheet_names:
                bank = "CIMB"
            elif "MAYBANK" in sheet_names:
                bank = "MAYBANK"
            elif "HSBC" in sheet_names:
                bank = "HSBC"
    except Exception as e:
        print(f"⚠️ Error detecting bank: {e}")
    print(f"🏦 Detected Bank: {bank}")
    return bank

def parse_cimb_statement(file_path):
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": "CIMB"}
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
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": "MAYBANK"}
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(p.extract_text() for p in pdf.pages)
            for m in re.findall(r"(\d{2}\s[A-Za-z]+)\s+([A-Za-z\s\-&.,]+?)\s+([\-]?\d{1,3}(?:,\d{3})*\.\d{2})", text):
                transactions.append({"date": m[0], "description": m[1].strip(), "amount": float(m[2].replace(",", ""))})
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

def parse_hsbc_statement(file_path):
    transactions, info = [], {"statement_date": None, "total": 0.0, "card_last4": "HSBC"}
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

def parse_statement_auto(file_path):
    bank = detect_bank(file_path)
    if bank == "CIMB": return parse_cimb_statement(file_path)
    elif bank == "MAYBANK": return parse_maybank_statement(file_path)
    elif bank == "HSBC": return parse_hsbc_statement(file_path)
    print("⚠️ Unsupported or unrecognized bank format.")
    return None, []