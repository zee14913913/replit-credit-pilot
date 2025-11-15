"""
银行流水月结单Excel解析器
=======================
支持银行：Public Bank, Maybank, CIMB, RHB, Hong Leong Bank

功能：
- 自动识别银行格式
- 提取账户信息（账号、户名、账户类型）
- 解析交易明细（日期、描述、DR/CR、余额）
- 智能分类（30+类别）
- 余额核对验证
"""

import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .bank_detector import BankDetector
from .transaction_classifier import TransactionClassifier


class BankStatementExcelParser:
    """银行流水Excel解析器"""
    
    def __init__(self):
        self.detector = BankDetector()
        self.classifier = TransactionClassifier()
        self.bank_code = None
        self.bank_name = None
        self.template = None
    
    def parse(self, file_path: str) -> Dict:
        """
        解析银行流水Excel/CSV文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            标准JSON格式数据
        """
        try:
            if file_path.endswith('.csv'):
                return self._parse_csv(file_path)
            else:
                return self._parse_excel(file_path)
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': f'文件解析失败: {e}'
            }
    
    def _parse_excel(self, file_path: str) -> Dict:
        """解析Excel文件"""
        self.bank_code, confidence = self.detector.detect_from_excel(file_path)
        
        if not self.bank_code:
            return {
                'status': 'error',
                'error': 'BANK_NOT_DETECTED',
                'message': '无法识别银行格式'
            }
        
        self.template = self.detector.get_bank_template(self.bank_code)
        self.bank_name = self.template['name']
        
        df_full = pd.read_excel(file_path)
        
        account_info = self._extract_account_info(df_full)
        transactions = self._extract_transactions(df_full)
        summary = self._generate_summary(transactions, account_info)
        
        return {
            'status': 'success',
            'document_type': 'bank_statement',
            'bank_detected': self.bank_name,
            'confidence_score': confidence,
            'account_info': account_info,
            'transactions': transactions,
            'summary': summary
        }
    
    def _parse_csv(self, file_path: str) -> Dict:
        """解析CSV文件"""
        self.bank_code, confidence = self.detector.detect_from_csv(file_path)
        
        if not self.bank_code:
            return {
                'status': 'error',
                'error': 'BANK_NOT_DETECTED',
                'message': '无法识别银行格式'
            }
        
        self.template = self.detector.get_bank_template(self.bank_code)
        self.bank_name = self.template['name']
        
        try:
            df_full = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df_full = pd.read_csv(file_path, encoding='gbk')
        
        account_info = self._extract_account_info(df_full)
        transactions = self._extract_transactions(df_full)
        summary = self._generate_summary(transactions, account_info)
        
        return {
            'status': 'success',
            'document_type': 'bank_statement',
            'bank_detected': self.bank_name,
            'confidence_score': confidence,
            'account_info': account_info,
            'transactions': transactions,
            'summary': summary
        }
    
    def _extract_account_info(self, df: pd.DataFrame) -> Dict:
        """提取账户基本信息"""
        text = df.to_string()
        
        account_number = self._extract_account_number(text)
        account_holder = self._extract_account_holder(text)
        account_type = self._extract_account_type(text)
        statement_date = self._extract_statement_date(text)
        
        opening_balance = self._extract_opening_balance(df)
        closing_balance = self._extract_closing_balance(df)
        
        return {
            'account_number': account_number or 'N/A',
            'account_type': account_type or 'N/A',
            'account_holder': account_holder or 'N/A',
            'bank': self.bank_name,
            'statement_date': statement_date or 'N/A',
            'opening_balance': opening_balance,
            'closing_balance': closing_balance,
            'total_debits': 0.0,
            'total_credits': 0.0
        }
    
    def _extract_account_number(self, text: str) -> Optional[str]:
        """提取账号"""
        pattern = self.template.get('account_number_pattern', r'Account[:\s]+(\d+)')
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _extract_account_holder(self, text: str) -> Optional[str]:
        """提取户名"""
        patterns = [
            r'Account Holder[:\s]+([A-Z\s]+)',
            r'Name[:\s]+([A-Z\s]+)',
            r'Customer Name[:\s]+([A-Z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 50:
                    return name
        return None
    
    def _extract_account_type(self, text: str) -> Optional[str]:
        """提取账户类型"""
        account_types = {
            'CURRENT': 'Current Account',
            'SAVINGS': 'Savings Account',
            'ACE': 'RM ACE Account',
            'ISLAMIC': 'Islamic Account'
        }
        
        text_upper = text.upper()
        for keyword, account_type in account_types.items():
            if keyword in text_upper:
                return account_type
        return None
    
    def _extract_statement_date(self, text: str) -> Optional[str]:
        """提取账单日期"""
        patterns = [
            r'Statement Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'As [Aa]t[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_opening_balance(self, df: pd.DataFrame) -> float:
        """提取期初余额"""
        text = df.to_string().upper()
        
        patterns = [
            r'OPENING BALANCE[:\s]+([\d,]+\.?\d*)',
            r'PREVIOUS BALANCE[:\s]+([\d,]+\.?\d*)',
            r'BALANCE B/F[:\s]+([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1).replace(',', '')
                return float(value)
        
        return 0.0
    
    def _extract_closing_balance(self, df: pd.DataFrame) -> float:
        """提取期末余额"""
        text = df.to_string().upper()
        
        patterns = [
            r'CLOSING BALANCE[:\s]+([\d,]+\.?\d*)',
            r'CURRENT BALANCE[:\s]+([\d,]+\.?\d*)',
            r'BALANCE C/F[:\s]+([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1).replace(',', '')
                return float(value)
        
        balance_col = self.template.get('balance_column', 'Balance')
        for col in df.columns:
            if balance_col.upper() in str(col).upper():
                values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(values) > 0:
                    return float(values.iloc[-1])
        
        return 0.0
    
    def _extract_transactions(self, df: pd.DataFrame) -> List[Dict]:
        """提取交易明细"""
        transactions = []
        
        date_col = self._find_column(df, self.template.get('date_column', 'Date'))
        desc_col = self._find_column(df, self.template.get('description_column', 'Description'))
        debit_col = self._find_column(df, self.template.get('debit_column', 'Debit'))
        credit_col = self._find_column(df, self.template.get('credit_column', 'Credit'))
        balance_col = self._find_column(df, self.template.get('balance_column', 'Balance'))
        
        if not date_col or not desc_col:
            return transactions
        
        for idx, row in df.iterrows():
            date_val = row.get(date_col)
            
            if pd.isna(date_val):
                continue
            
            try:
                if isinstance(date_val, str):
                    transaction_date = self._parse_date(date_val)
                else:
                    transaction_date = date_val.strftime('%d-%m-%Y')
            except:
                continue
            
            description = str(row.get(desc_col, ''))
            if not description or description == 'nan':
                continue
            
            debit = self._parse_amount(row.get(debit_col, 0))
            credit = self._parse_amount(row.get(credit_col, 0))
            running_balance = self._parse_amount(row.get(balance_col, 0))
            
            amount = credit - debit
            
            main_cat, sub_cat = self.classifier.classify(description, amount)
            
            transactions.append({
                'date': transaction_date,
                'description': description.strip(),
                'debit': debit,
                'credit': credit,
                'running_balance': running_balance,
                'category': main_cat,
                'sub_category': sub_cat
            })
        
        return transactions
    
    def _find_column(self, df: pd.DataFrame, column_name: str) -> Optional[str]:
        """模糊匹配列名"""
        for col in df.columns:
            if column_name.upper() in str(col).upper():
                return col
        return None
    
    def _parse_date(self, date_str: str) -> str:
        """解析日期字符串"""
        formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d.%m.%Y']
        
        for fmt in formats:
            try:
                dt = datetime.strptime(str(date_str).strip(), fmt)
                return dt.strftime('%d-%m-%Y')
            except:
                continue
        
        return date_str
    
    def _parse_amount(self, value) -> float:
        """解析金额"""
        if pd.isna(value):
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        value_str = str(value).replace(',', '').strip()
        try:
            return float(value_str)
        except:
            return 0.0
    
    def _generate_summary(self, transactions: List[Dict], account_info: Dict) -> Dict:
        """生成汇总统计"""
        total_debits = sum(txn['debit'] for txn in transactions)
        total_credits = sum(txn['credit'] for txn in transactions)
        
        account_info['total_debits'] = total_debits
        account_info['total_credits'] = total_credits
        
        category_breakdown = self.classifier.get_category_summary(transactions)
        
        calculated_closing = account_info['opening_balance'] + total_credits - total_debits
        balance_verified = abs(calculated_closing - account_info['closing_balance']) < 0.01
        
        return {
            'total_transactions': len(transactions),
            'category_breakdown': category_breakdown,
            'balance_verified': balance_verified,
            'balance_difference': round(calculated_closing - account_info['closing_balance'], 2)
        }
