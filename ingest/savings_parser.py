"""
储蓄账户月结单解析器
支持银行：Maybank, GX Bank, Hong Leong Bank, CIMB, UOB, OCBC, Public Bank
完整记录所有转账交易，不遗漏任何一笔
"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional

def clean_balance_string(value: str) -> Optional[float]:
    """
    清理balance字符串，处理多种格式：
    - 移除货币符号（RM, MYR等）
    - 移除千位分隔符逗号
    - 处理括号表示的负数：(1,234.56) → -1234.56
    - 处理CR/DR后缀
    - 处理负号
    """
    if not value or pd.isna(value):
        return None
    
    # 转为字符串并清理
    s = str(value).strip().upper()
    
    # 跳过无效值
    if s in ['', 'NAN', 'NULL', 'NONE', '-']:
        return None
    
    # 记录是否是负数
    is_negative = False
    
    # 检查括号格式（表示负数）
    if s.startswith('(') and s.endswith(')'):
        is_negative = True
        s = s[1:-1].strip()  # 移除括号
    
    # 检查负号
    if s.startswith('-'):
        is_negative = True
        s = s[1:].strip()
    
    # 移除货币符号和CR/DR标记
    s = s.replace('RM', '').replace('MYR', '').replace('CR', '').replace('DR', '').strip()
    
    # 移除千位分隔符
    s = s.replace(',', '')
    
    # 转换为float
    try:
        balance = float(s)
        return -balance if is_negative else balance
    except ValueError:
        return None

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
                
                # 通用交易提取模式 - 日期 + 描述 + 金额 + 余额（可选）
                # 支持多种格式: DD/MM/YYYY, DD MMM YYYY, DD-MM-YYYY
                # Balance支持：正数、负数（带-号）、括号表示负数、带CR/DR后缀
                transaction_patterns = [
                    # 格式1: DD/MM/YYYY Description Amount Balance (支持负数和括号)
                    r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+([\-]?[\d,]+\.\d{2})\s+([\-\(]?[\d,]+\.\d{2}\)?(?:\s+[CDR]+)?)\s*$',
                    # 格式2: DD MMM YYYY Description Amount Balance
                    r'(\d{1,2}\s+[A-Z]{3}\s+\d{4})\s+(.+?)\s+([\-]?[\d,]+\.\d{2})\s+([\-\(]?[\d,]+\.\d{2}\)?(?:\s+[CDR]+)?)\s*$',
                    # 格式3: DD-MM-YYYY Description Amount Balance
                    r'(\d{1,2}-\d{1,2}-\d{2,4})\s+(.+?)\s+([\-]?[\d,]+\.\d{2})\s+([\-\(]?[\d,]+\.\d{2}\)?(?:\s+[CDR]+)?)\s*$',
                    # 格式4: DD/MM/YYYY Description Amount (无Balance)
                    r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+([\-]?[\d,]+\.\d{2})\s*$',
                    # 格式5: DD MMM YYYY Description Amount (无Balance)
                    r'(\d{1,2}\s+[A-Z]{3}\s+\d{4})\s+(.+?)\s+([\-]?[\d,]+\.\d{2})\s*$',
                    # 格式6: DD-MM-YYYY Description Amount (无Balance)
                    r'(\d{1,2}-\d{1,2}-\d{2,4})\s+(.+?)\s+([\-]?[\d,]+\.\d{2})\s*$',
                ]
                
                for pattern in transaction_patterns:
                    for match in re.finditer(pattern, full_text, re.MULTILINE):
                        trans_date = match.group(1).strip()
                        trans_desc = match.group(2).strip()
                        trans_amount = match.group(3).strip()
                        # Balance可能不存在（格式4-6），使用clean_balance_string清理
                        trans_balance_raw = match.group(4).strip() if match.lastindex >= 4 else None
                        trans_balance = clean_balance_string(trans_balance_raw) if trans_balance_raw else None
                        
                        # 跳过表头和无效行
                        if any(kw in trans_desc.upper() for kw in ['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'TOTAL', 'OPENING', 'CLOSING']):
                            continue
                        
                        # 跳过描述太短的行
                        if len(trans_desc) < 3:
                            continue
                        
                        try:
                            # 使用clean_balance_string清理amount（支持负数、千位分隔符等）
                            amount = clean_balance_string(trans_amount)
                            if amount is None:
                                continue
                            
                            # trans_balance已经被clean_balance_string处理过，是float或None
                            balance = trans_balance
                            
                            # 判断借贷方向（根据原始字符串）
                            trans_type = 'debit' if '-' in trans_amount or trans_amount.startswith('(') else 'credit'
                            
                            trans_dict = {
                                'date': trans_date,
                                'description': trans_desc,
                                'amount': abs(amount),  # 存储绝对值
                                'type': trans_type
                            }
                            if balance is not None:
                                trans_dict['balance'] = balance
                            
                            transactions.append(trans_dict)
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
            
            # 检查是否有balance列
            balance_col = next((col for col in df.columns if 'balance' in col.lower()), None)
            
            if date_col and desc_col:
                for _, row in df.iterrows():
                    if pd.notna(row[date_col]) and pd.notna(row[desc_col]):
                        # 提取balance（如果有）- 使用robust清理函数
                        balance = clean_balance_string(row[balance_col]) if balance_col else None
                        
                        # 格式1: 分开的Withdrawal/Deposit列
                        if withdrawal_col and deposit_col:
                            # 检查Withdrawal列
                            if pd.notna(row[withdrawal_col]) and float(row[withdrawal_col]) > 0:
                                trans_dict = {
                                    'date': str(row[date_col]),
                                    'description': str(row[desc_col]).strip(),
                                    'amount': float(row[withdrawal_col]),
                                    'type': 'debit'
                                }
                                if balance is not None:
                                    trans_dict['balance'] = balance
                                transactions.append(trans_dict)
                            # 检查Deposit列
                            elif pd.notna(row[deposit_col]) and float(row[deposit_col]) > 0:
                                trans_dict = {
                                    'date': str(row[date_col]),
                                    'description': str(row[desc_col]).strip(),
                                    'amount': float(row[deposit_col]),
                                    'type': 'credit'
                                }
                                if balance is not None:
                                    trans_dict['balance'] = balance
                                transactions.append(trans_dict)
                        # 格式2: 单一amount列
                        elif amount_col and pd.notna(row[amount_col]):
                            trans_dict = {
                                'date': str(row[date_col]),
                                'description': str(row[desc_col]).strip(),
                                'amount': abs(float(row[amount_col])),
                                'type': 'debit' if float(row[amount_col]) < 0 else 'credit'
                            }
                            if balance is not None:
                                trans_dict['balance'] = balance
                            transactions.append(trans_dict)
        
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
    """GX Bank储蓄账户解析器 - 处理Money in/Money out双列格式"""
    info = {
        'bank_name': 'GX Bank',
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
            
            # 提取账号后4位: Account number 8888-01098373-2
            for line in lines:
                if 'Account number' in line:
                    match = re.search(r'(\d{4})-(\d{8})-(\d)', line)
                    if match:
                        info['account_last4'] = match.group(1)  # 前4位
                
                # 提取账单日期: January 2025, February 2025等
                month_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', line)
                if month_match:
                    month = month_match.group(1)
                    year = month_match.group(2)
                    # 转换为标准格式
                    month_map = {'January': 'Jan', 'February': 'Feb', 'March': 'Mar', 'April': 'Apr',
                                'May': 'May', 'June': 'Jun', 'July': 'Jul', 'August': 'Aug',
                                'September': 'Sep', 'October': 'Oct', 'November': 'Nov', 'December': 'Dec'}
                    info['statement_date'] = f"{month_map[month]} {year}"
            
            # 解析交易记录 - GX Bank格式
            # 格式: Date  Description  Money in (RM)  Money out (RM)  Interest earned (RM)  Closing balance (RM)
            # 提取年份用于补全交易日期
            statement_year = info['statement_date'].split()[-1] if info['statement_date'] else '2025'
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 匹配交易行: DD MMM开头，例如 "1 Jan", "2 Feb"
                trans_match = re.match(r'^(\d{1,2}\s+[A-Z][a-z]{2})\s+(.+)', line)
                
                if trans_match:
                    date_str = trans_match.group(1)
                    rest = trans_match.group(2).strip()
                    
                    # 跳过特殊行
                    if 'Opening balance' in rest or 'Closing balance' in rest:
                        i += 1
                        continue
                    
                    # 收集完整描述（可能跨多行）
                    description = rest
                    j = i + 1
                    money_in = None
                    money_out = None
                    closing_balance = None
                    
                    # 查找后续行直到找到金额和余额
                    # GX Bank格式: Description | Money in | Money out | Interest | Closing balance
                    while j < len(lines) and j < i + 5:
                        next_line = lines[j].strip()
                        
                        # 检查是否包含金额（+或-符号，或纯数字）
                        # 格式：可能有多个金额在同一行（Money in, Money out, Balance）
                        amounts = re.findall(r'([+-])?([\d,]+\.\d{2})', next_line)
                        
                        if amounts:
                            # 第一个金额可能是money in/out
                            for idx, (sign, amount_str) in enumerate(amounts):
                                # 构建完整金额字符串（包括符号）用于清理
                                full_amount_str = f"{sign or ''}{amount_str}"
                                amount = clean_balance_string(full_amount_str) or 0
                                
                                if idx == 0:  # 第一个金额
                                    if sign == '+' or (not sign and any(word in description.lower() for word in ['transfer from', 'received', 'deposit', 'interest', 'cashback'])):
                                        money_in = abs(amount)
                                    else:
                                        money_out = abs(amount)
                                elif idx == len(amounts) - 1:  # 最后一个金额通常是closing balance
                                    closing_balance = amount  # 可能是正数或负数
                            break
                        elif next_line and not re.match(r'^\d{1,2}\s+[A-Z][a-z]{2}', next_line) and 'GX' not in next_line and 'QR' not in next_line:
                            # 继续收集描述
                            description += ' ' + next_line
                        
                        j += 1
                    
                    # 如果找到了金额，创建交易记录（附加年份到日期）
                    if money_in or money_out:
                        full_date = f"{date_str} {statement_year}"  # 添加年份: "1 Jan 2025"
                        transactions.append({
                            'date': full_date,
                            'description': description.strip(),
                            'amount': money_in if money_in else money_out,
                            'type': 'credit' if money_in else 'debit',
                            'balance': closing_balance  # 添加closing balance
                        })
                
                i += 1
        
        info['total_transactions'] = len(transactions)
        print(f"✅ GX Bank savings parsed: {len(transactions)} transactions")
        
    except Exception as e:
        print(f"❌ Error parsing GX Bank statement: {e}")
        import traceback
        traceback.print_exc()
    
    return info, transactions

def parse_hlb_savings(file_path: str) -> Tuple[Dict, List[Dict]]:
    """Hong Leong Bank储蓄账户解析器 - 处理Deposit/Withdrawal/Balance列格式"""
    info = {
        'bank_name': 'Hong Leong Bank',
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
                if 'A/C No' in line or 'No Akaun' in line:
                    match = re.search(r'(\d{11})', line)
                    if match:
                        info['account_last4'] = match.group(1)[-4:]
                
                # 提取账单日期
                if 'Date / Tarikh' in line:
                    match = re.search(r'(\d{2}-\d{2}-\d{4})', line)
                    if match:
                        info['statement_date'] = match.group(1)
            
            # 解析交易记录 - HLB格式: Date | Description | Deposit | Withdrawal | Balance
            # 格式: DD-MM-YYYY Description [Deposit] [Withdrawal] Balance
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # 匹配交易行: DD-MM-YYYY开头
                trans_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+(.+)', line)
                
                if trans_match:
                    date_str = trans_match.group(1)
                    rest = trans_match.group(2).strip()
                    
                    # 跳过特殊行
                    if 'Balance from previous statement' in rest.lower() or 'balance c/f' in rest.lower() or 'balance b/f' in rest.lower():
                        i += 1
                        continue
                    
                    # HLB格式: Description可能很长，后面跟1-3个数字（Deposit, Withdrawal, Balance）
                    # 从右边提取数字：最后一个总是Balance
                    numbers = re.findall(r'([\d,]+\.\d{2})', rest)
                    
                    if len(numbers) >= 1:
                        # 最后一个数字是Balance
                        balance_str = numbers[-1]
                        balance = clean_balance_string(balance_str)
                        
                        # 提取Description（移除所有数字部分）
                        desc_parts = re.split(r'[\d,]+\.\d{2}', rest)
                        description = desc_parts[0].strip()
                        
                        # 判断是Deposit还是Withdrawal
                        if len(numbers) == 2:
                            # 有2个数字：[Deposit/Withdrawal] Balance
                            amount_str = numbers[0]
                            amount = clean_balance_string(amount_str)
                            
                            # 根据描述判断类型（HLB的存入通常包含Transfer/Deposit/CR等关键词）
                            trans_type = 'credit' if any(kw in description.upper() for kw in ['TRANSFER AT KLM', 'DEPOSIT', 'CR ADVICE', 'CR ADV']) else 'debit'
                        elif len(numbers) == 3:
                            # 有3个数字：Deposit Withdrawal Balance
                            deposit_str = numbers[0]
                            withdrawal_str = numbers[1]
                            
                            deposit = clean_balance_string(deposit_str) or 0
                            withdrawal = clean_balance_string(withdrawal_str) or 0
                            
                            if deposit > 0:
                                amount = deposit
                                trans_type = 'credit'
                            else:
                                amount = withdrawal
                                trans_type = 'debit'
                        else:
                            # 只有1个数字（Balance），无法确定金额
                            i += 1
                            continue
                        
                        # 收集完整描述（可能跨多行）
                        full_desc = description
                        j = i + 1
                        while j < len(lines) and j < i + 5:
                            next_line = lines[j].strip()
                            # 如果下一行不是新交易，且不以日期开头，加入描述
                            if next_line and not re.match(r'^\d{2}-\d{2}-\d{4}\s+', next_line):
                                # 跳过包含数字的行（可能是金额行）
                                if not re.match(r'^[\d,\.]+$', next_line) and 'Total Withdrawals' not in next_line:
                                    full_desc += ' ' + next_line
                            else:
                                break
                            j += 1
                        
                        if amount and amount > 0:
                            transactions.append({
                                'date': date_str,
                                'description': full_desc.strip(),
                                'amount': amount,
                                'type': trans_type,
                                'balance': balance
                            })
                
                i += 1
        
        info['total_transactions'] = len(transactions)
        print(f"✅ HLB savings parsed: {len(transactions)} transactions from {file_path}")
        
    except Exception as e:
        print(f"❌ Error parsing HLB statement: {e}")
        import traceback
        traceback.print_exc()
        # 如果专用解析器失败，尝试通用解析器
        info, transactions = parse_generic_savings(file_path)
        info['bank_name'] = 'Hong Leong Bank'
    
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
                            # 使用clean_balance_string清理金额和余额
                            balance = clean_balance_string(parts[-1])
                            amount = clean_balance_string(parts[-2]) or 0
                            
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
                            # Public Bank: DEBIT列在左，CREDIT列在右
                            # 更robust的检测方法：检查描述中是否包含"DR"或"CR"标记
                            trans_type = 'credit'  # 默认credit
                            
                            # 检查是否是debit交易（转出）- 更通用的DR检测
                            if ' DR' in full_desc or full_desc.startswith('DR') or ' DR-' in full_desc:
                                trans_type = 'debit'
                            # 明确的credit标记
                            elif ' CR' in full_desc or full_desc.startswith('CR') or 'DEP-' in full_desc or 'DEPOSIT' in full_desc.upper():
                                trans_type = 'credit'
                            
                            # 转换日期格式 DD/MM -> DD-MM-YYYY
                            day, month = date_str.split('/')
                            formatted_date = f"{day}-{month}-{current_year}"
                            
                            if amount > 0:
                                transactions.append({
                                    'date': formatted_date,
                                    'description': full_desc.strip(),
                                    'amount': amount,
                                    'type': trans_type,
                                    'balance': balance  # 添加balance字段
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
                    amount_str = match.group(3)
                    balance_str = match.group(4)  # 提取Balance字段（可能带CR/DR）
                    
                    # 转换日期格式 DDMMYY -> DD-MM-20YY
                    day = date_str[:2]
                    month = date_str[2:4]
                    year = '20' + date_str[4:6]
                    formatted_date = f"{day}-{month}-{year}"
                    
                    # 使用clean_balance_string清理amount和balance
                    amount = clean_balance_string(amount_str) or 0
                    balance = clean_balance_string(balance_str)
                    
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
                            'type': trans_type,
                            'balance': balance  # 添加balance字段
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
