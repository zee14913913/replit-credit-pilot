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
        'Alliance Bank': parse_alliance_savings,
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
        'Alliance Bank': ['alliance bank', 'alliance', 'alliancebank'],
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
            
            # 检查是否有分开的Withdrawal/Deposit列（Maybank格式）
            withdrawal_col = next((col for col in df.columns if 'withdrawal' in col.lower() or 'debit' in col.lower()), None)
            deposit_col = next((col for col in df.columns if 'deposit' in col.lower() or 'credit' in col.lower()), None)
            
            # 或者单一的amount列
            amount_col = next((col for col in df.columns if 'amount' in col.lower()), None)
            
            if date_col and desc_col:
                for _, row in df.iterrows():
                    if pd.notna(row[date_col]) and pd.notna(row[desc_col]):
                        # 格式1: 分开的Withdrawal/Deposit列
                        if withdrawal_col and deposit_col:
                            # 检查Withdrawal列
                            if pd.notna(row[withdrawal_col]) and float(row[withdrawal_col]) > 0:
                                transactions.append({
                                    'date': str(row[date_col]),
                                    'description': str(row[desc_col]).strip(),
                                    'amount': float(row[withdrawal_col]),
                                    'type': 'debit'
                                })
                            # 检查Deposit列
                            elif pd.notna(row[deposit_col]) and float(row[deposit_col]) > 0:
                                transactions.append({
                                    'date': str(row[date_col]),
                                    'description': str(row[desc_col]).strip(),
                                    'amount': float(row[deposit_col]),
                                    'type': 'credit'
                                })
                        # 格式2: 单一amount列
                        elif amount_col and pd.notna(row[amount_col]):
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
    """Public Bank储蓄账户解析器 - 处理DEBIT/CREDIT列格式"""
    info = {
        'bank_name': 'Public Bank',
        'account_last4': '',
        'statement_date': '',
        'total_transactions': 0
    }
    
    transactions = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                full_text += page.extract_text() + '\n'
            
            lines = full_text.split('\n')
            
            # 提取账号后4位
            for line in lines:
                if 'Nombor Akaun' in line or 'Account Number' in line:
                    match = re.search(r'(\d{10})', line)
                    if match:
                        info['account_last4'] = match.group(1)[-4:]
                
                # 提取账单日期
                if 'Tarikh Penyata' in line or 'Statement Date' in line:
                    match = re.search(r'(\d{2}\s+\w+\s+\d{4})', line)
                    if match:
                        info['statement_date'] = match.group(1)
            
            # 解析交易记录 - Public Bank格式
            # 格式: DD/MM Description DebitAmount CreditAmount Balance
            # 或: DD/MM Description Amount Balance (只有一个金额，在debit或credit列)
            i = 0
            current_year = info['statement_date'].split()[-1] if info['statement_date'] else '2025'
            
            while i < len(lines):
                line = lines[i].strip()
                
                # 匹配交易行: DD/MM开头
                trans_match = re.match(r'^(\d{2}/\d{2})\s+(.+)', line)
                
                if trans_match:
                    date_str = trans_match.group(1)
                    rest = trans_match.group(2).strip()
                    
                    # 跳过特殊行
                    if 'Balance From Last Statement' in rest or 'Balance C/F' in rest or 'Balance B/F' in rest or 'Closing Balance' in rest:
                        i += 1
                        continue
                    
                    # 解析金额和余额
                    # 尝试匹配: Description DebitAmount CreditAmount Balance
                    # 或: Description Amount Balance
                    parts = rest.rsplit(None, 2)  # 从右边分割出最后2个数字（可能是金额+余额）
                    
                    if len(parts) >= 2:
                        # 检查最后两个部分是否是数字
                        try:
                            # 尝试解析为金额格式
                            last_val = parts[-1].replace(',', '')
                            second_last_val = parts[-2].replace(',', '')
                            
                            balance = float(last_val)
                            amount = float(second_last_val)
                            
                            # 描述是除了最后两个数字的部分
                            description = ' '.join(parts[:-2]) if len(parts) > 2 else 'Transaction'
                            
                            # 收集完整描述（可能跨多行）
                            full_desc = description
                            j = i + 1
                            while j < len(lines) and j < i + 3:
                                next_line = lines[j].strip()
                                # 如果下一行不是新交易且不是空行
                                if next_line and not re.match(r'^\d{2}/\d{2}\s+', next_line) and not next_line.startswith('Balance') and not next_line.startswith('Penyata'):
                                    # 跳过纯数字行
                                    if not re.match(r'^[\d,\.]+$', next_line):
                                        full_desc += ' ' + next_line
                                else:
                                    break
                                j += 1
                            
                            # 判断是debit还是credit
                            # 如果描述中有DR，则是debit；否则检查金额的逻辑
                            # Public Bank: DEBIT列在左，CREDIT列在右
                            trans_type = 'credit'  # 默认credit
                            
                            # 检查是否是debit交易（转出）
                            if 'TRSF DR' in full_desc or 'MISC DR' in full_desc or 'DUITNOW TRSF DR' in full_desc or 'TSFR FUND DR' in full_desc:
                                trans_type = 'debit'
                            elif 'DEP-' in full_desc or 'TRSF CR' in full_desc or 'DUITNOW TRSF CR' in full_desc:
                                trans_type = 'credit'
                            
                            # 转换日期格式 DD/MM -> DD-MM-YYYY
                            day, month = date_str.split('/')
                            formatted_date = f"{day}-{month}-{current_year}"
                            
                            if amount > 0:
                                transactions.append({
                                    'date': formatted_date,
                                    'description': full_desc.strip(),
                                    'amount': amount,
                                    'type': trans_type
                                })
                        
                        except ValueError:
                            pass  # 不是金额格式，跳过
                
                i += 1
        
        info['total_transactions'] = len(transactions)
        print(f"✅ Public Bank savings parsed: {len(transactions)} transactions from {file_path}")
        
    except Exception as e:
        print(f"❌ Error parsing Public Bank statement: {e}")
        import traceback
        traceback.print_exc()
    
    return info, transactions

def parse_alliance_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """Alliance Bank储蓄账户解析器 - 专门处理多行交易格式"""
    info = {
        'bank_name': 'Alliance Bank',
        'account_last4': '',
        'statement_date': '',
        'total_transactions': 0
    }
    
    transactions = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                full_text += page.extract_text() + '\n'
            
            lines = full_text.split('\n')
            
            # 提取账号后4位
            for line in lines:
                if 'Account No' in line or 'No. Akaun' in line:
                    match = re.search(r'(\d{4})\s*$', line)
                    if match:
                        info['account_last4'] = match.group(1)
                
                # 提取账单日期
                if 'Statement Date' in line or 'Tarikh Penyata' in line:
                    match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                    if match:
                        info['statement_date'] = match.group(1)
            
            # 解析交易记录 - Alliance Bank格式特殊，每笔交易跨多行
            # 支持CR (credit) 和 DR (debit) 两种交易类型
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 匹配交易行：DDMMYY TransactionType Amount Balance CR/DR
                # CR格式: DDMMYY Description Amount Balance CR
                trans_cr_match = re.match(r'^(\d{6})\s+(.+?)\s+([\d,]+\.?\d*)\s+([\d,]+\.\d{2})\s+CR\s*$', line)
                # DR格式: DDMMYY Description Amount Balance DR
                trans_dr_match = re.match(r'^(\d{6})\s+(.+?)\s+([\d,]+\.?\d*)\s+([\d,]+\.\d{2})\s+DR\s*$', line)
                
                if trans_cr_match or trans_dr_match:
                    # 使用匹配到的对象
                    match = trans_cr_match if trans_cr_match else trans_dr_match
                    trans_type = 'credit' if trans_cr_match else 'debit'
                    
                    date_str = match.group(1)
                    description = match.group(2).strip()
                    amount_str = match.group(3).replace(',', '')
                    
                    # 转换日期格式 DDMMYY -> DD-MM-20YY
                    day = date_str[:2]
                    month = date_str[2:4]
                    year = '20' + date_str[4:6]
                    formatted_date = f"{day}-{month}-{year}"
                    
                    amount = float(amount_str) if amount_str else 0
                    
                    # 收集完整描述（可能跨多行）
                    full_desc = description
                    j = i + 1
                    while j < len(lines) and j < i + 5:
                        next_line = lines[j].strip()
                        # 如果下一行不是新交易，且不是空行，加入描述
                        if next_line and not re.match(r'^\d{6}\s+', next_line) and not next_line.startswith('The items'):
                            # 跳过纯数字行和特定关键字
                            if not re.match(r'^[\d,\.]+$', next_line) and next_line not in ['Transfer from ABMB', 'PBB-PBCS AC 3']:
                                full_desc += ' ' + next_line
                        else:
                            break
                        j += 1
                    
                    if amount > 0:
                        transactions.append({
                            'date': formatted_date,
                            'description': full_desc.strip(),
                            'amount': amount,
                            'type': trans_type
                        })
                
                i += 1
        
        info['total_transactions'] = len(transactions)
        print(f"✅ Alliance Bank savings parsed: {len(transactions)} transactions from {file_path}")
        
    except Exception as e:
        print(f"❌ Error parsing Alliance Bank statement: {e}")
        import traceback
        traceback.print_exc()
        # 如果专用解析器失败，尝试通用解析器
        info, transactions = parse_generic_savings(file_path)
        info['bank_name'] = 'Alliance Bank'
    
    return info, transactions
