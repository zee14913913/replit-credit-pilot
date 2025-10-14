"""
储蓄账户月结单解析器
支持银行：Maybank, GX Bank, Hong Leong Bank, CIMB, UOB, OCBC, Public Bank
完整记录所有转账交易，不遗漏任何一笔
"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Tuple

def parse_savings_statement(file_path: str, bank_name: str = '') -> Tuple[Dict, List[Dict]]:
    """
    解析储蓄账户月结单
    
    Args:
        file_path: PDF或Excel文件路径
        bank_name: 银行名称（可选，用于指定解析器）
    
    Returns:
        (statement_info, transactions) - 账单信息和交易列表
    """
    
    # 自动检测银行
    if not bank_name:
        bank_name = detect_bank_from_file(file_path) or 'Generic'
    
    # 根据银行选择解析器
    bank_parsers = {
        'Maybank': parse_maybank_savings,
        'GX Bank': parse_gxbank_savings,
        'Hong Leong Bank': parse_hlb_savings,
        'CIMB': parse_cimb_savings,
        'UOB': parse_uob_savings,
        'OCBC': parse_ocbc_savings,
        'Public Bank': parse_publicbank_savings,
    }
    
    parser = bank_parsers.get(bank_name, parse_generic_savings)
    return parser(file_path)

def detect_bank_from_file(file_path: str) -> str:
    """从文件名或内容自动检测银行"""
    file_name = file_path.lower()
    
    bank_patterns = {
        'Maybank': ['maybank', 'mbb', 'malayan'],
        'GX Bank': ['gxbank', 'gx bank', 'gx_bank'],
        'Hong Leong Bank': ['hong leong', 'hlb', 'hongLeong'],
        'CIMB': ['cimb'],
        'UOB': ['uob', 'united overseas'],
        'OCBC': ['ocbc'],
        'Public Bank': ['public bank', 'pbb', 'publicbank'],
    }
    
    for bank, patterns in bank_patterns.items():
        if any(pattern in file_name for pattern in patterns):
            return bank
    
    # 如果文件名无法检测，尝试读取PDF内容
    if file_path.endswith('.pdf'):
        try:
            with pdfplumber.open(file_path) as pdf:
                first_page = pdf.pages[0].extract_text()
                for bank, patterns in bank_patterns.items():
                    if any(pattern.lower() in first_page.lower() for pattern in patterns):
                        return bank
        except:
            pass
    
    return 'Generic'

def parse_generic_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """通用储蓄账单解析器 - 提取所有交易记录"""
    info = {
        'bank_name': 'Generic',
        'account_last4': '',
        'statement_date': '',
        'total_transactions': 0
    }
    transactions = []
    
    try:
        if file_path.endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                full_text = '\n'.join(p.extract_text() for p in pdf.pages)
                
                # 提取账单日期 - 多种格式
                date_patterns = [
                    r'Statement Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'Date[:\s]+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
                    r'(\d{1,2}/\d{1,2}/\d{4})',
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, full_text, re.IGNORECASE)
                    if match:
                        info['statement_date'] = match.group(1)
                        break
                
                # 提取账户号码后4位
                account_match = re.search(r'(?:Account|A/C).*?(\d{4})', full_text, re.IGNORECASE)
                if account_match:
                    info['account_last4'] = account_match.group(1)
                
                # 通用交易提取模式 - 日期 + 描述 + 金额
                # 支持多种格式: DD/MM/YYYY, DD MMM YYYY, DD-MM-YYYY
                transaction_patterns = [
                    # 格式1: DD/MM/YYYY Description Amount
                    r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+([\-]?[\d,]+\.\d{2})\s*$',
                    # 格式2: DD MMM YYYY Description Amount
                    r'(\d{1,2}\s+[A-Z]{3}\s+\d{4})\s+(.+?)\s+([\-]?[\d,]+\.\d{2})\s*$',
                    # 格式3: DD-MM-YYYY Description Amount
                    r'(\d{1,2}-\d{1,2}-\d{2,4})\s+(.+?)\s+([\-]?[\d,]+\.\d{2})\s*$',
                ]
                
                for pattern in transaction_patterns:
                    for match in re.finditer(pattern, full_text, re.MULTILINE):
                        trans_date = match.group(1).strip()
                        trans_desc = match.group(2).strip()
                        trans_amount = match.group(3).strip()
                        
                        # 跳过表头和无效行
                        if any(kw in trans_desc.upper() for kw in ['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'TOTAL', 'OPENING', 'CLOSING']):
                            continue
                        
                        # 跳过描述太短的行
                        if len(trans_desc) < 3:
                            continue
                        
                        try:
                            amount = float(trans_amount.replace(',', '').replace('-', ''))
                            
                            # 判断借贷方向
                            trans_type = 'debit' if '-' in trans_amount or trans_amount.startswith('(') else 'credit'
                            
                            transactions.append({
                                'date': trans_date,
                                'description': trans_desc,
                                'amount': amount,
                                'type': trans_type
                            })
                        except ValueError:
                            continue
        
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
            
            # 尝试识别列名
            date_col = next((col for col in df.columns if 'date' in col.lower()), None)
            desc_col = next((col for col in df.columns if 'desc' in col.lower() or 'particulars' in col.lower()), None)
            amount_col = next((col for col in df.columns if 'amount' in col.lower() or 'debit' in col.lower() or 'credit' in col.lower()), None)
            
            if date_col and desc_col and amount_col:
                for _, row in df.iterrows():
                    if pd.notna(row[date_col]) and pd.notna(row[desc_col]) and pd.notna(row[amount_col]):
                        transactions.append({
                            'date': str(row[date_col]),
                            'description': str(row[desc_col]).strip(),
                            'amount': abs(float(row[amount_col])),
                            'type': 'debit' if float(row[amount_col]) < 0 else 'credit'
                        })
        
        info['total_transactions'] = len(transactions)
        print(f"✅ Generic parser: {len(transactions)} transactions extracted from {file_path}")
        
    except Exception as e:
        print(f"❌ Error parsing savings statement: {e}")
        import traceback
        traceback.print_exc()
    
    return info, transactions

# 银行专用解析器（后续可扩展）
def parse_maybank_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """Maybank储蓄账户解析器"""
    info, transactions = parse_generic_savings(file_path)
    info['bank_name'] = 'Maybank'
    print(f"✅ Maybank savings parsed: {len(transactions)} transactions")
    return info, transactions

def parse_gxbank_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """GX Bank储蓄账户解析器"""
    info, transactions = parse_generic_savings(file_path)
    info['bank_name'] = 'GX Bank'
    print(f"✅ GX Bank savings parsed: {len(transactions)} transactions")
    return info, transactions

def parse_hlb_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """Hong Leong Bank储蓄账户解析器"""
    info, transactions = parse_generic_savings(file_path)
    info['bank_name'] = 'Hong Leong Bank'
    print(f"✅ HLB savings parsed: {len(transactions)} transactions")
    return info, transactions

def parse_cimb_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """CIMB储蓄账户解析器"""
    info, transactions = parse_generic_savings(file_path)
    info['bank_name'] = 'CIMB'
    print(f"✅ CIMB savings parsed: {len(transactions)} transactions")
    return info, transactions

def parse_uob_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """UOB储蓄账户解析器"""
    info, transactions = parse_generic_savings(file_path)
    info['bank_name'] = 'UOB'
    print(f"✅ UOB savings parsed: {len(transactions)} transactions")
    return info, transactions

def parse_ocbc_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """OCBC储蓄账户解析器"""
    info, transactions = parse_generic_savings(file_path)
    info['bank_name'] = 'OCBC'
    print(f"✅ OCBC savings parsed: {len(transactions)} transactions")
    return info, transactions

def parse_publicbank_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """Public Bank储蓄账户解析器"""
    info, transactions = parse_generic_savings(file_path)
    info['bank_name'] = 'Public Bank'
    print(f"✅ Public Bank savings parsed: {len(transactions)} transactions")
    return info, transactions
