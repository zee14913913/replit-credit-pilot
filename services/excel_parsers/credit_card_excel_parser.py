"""
信用卡账单Excel解析器
====================
支持银行：Public Bank, Maybank, CIMB, RHB, Hong Leong Bank, HSBC, Alliance

功能：
- 自动识别银行格式
- 提取卡片信息（银行、卡号、卡类型、额度）
- 解析交易明细（日期、描述、DR/CR、余额）
- 智能分类（Purchases/Payment/Finance Charges/Instalment）
- 余额核对验证
"""

import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Optional
from .bank_detector import BankDetector
from .transaction_classifier import TransactionClassifier


class CreditCardExcelParser:
    """信用卡账单Excel解析器"""
    
    def __init__(self):
        self.detector = BankDetector()
        self.classifier = TransactionClassifier()
        self.bank_code = None
        self.bank_name = None
    
    def parse(self, file_path: str) -> Dict:
        """
        解析信用卡Excel/CSV文件
        
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
        df_full = pd.read_excel(file_path)
        
        self.bank_code, confidence = self.detector.detect_from_excel(file_path)
        
        if not self.bank_code:
            self.bank_name = 'Unknown Bank'
        else:
            template = self.detector.get_bank_template(self.bank_code)
            self.bank_name = template['name']
        
        account_info = self._extract_card_info(df_full)
        transactions = self._extract_transactions(df_full)
        summary = self._generate_summary(transactions, account_info)
        
        return {
            'status': 'success',
            'document_type': 'credit_card',
            'bank_detected': self.bank_name,
            'confidence_score': confidence if self.bank_code else 0.5,
            'account_info': account_info,
            'transactions': transactions,
            'summary': summary
        }
    
    def _parse_csv(self, file_path: str) -> Dict:
        """解析CSV文件"""
        try:
            df_full = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df_full = pd.read_csv(file_path, encoding='gbk')
        
        self.bank_code, confidence = self.detector.detect_from_csv(file_path)
        
        if not self.bank_code:
            self.bank_name = 'Unknown Bank'
        else:
            template = self.detector.get_bank_template(self.bank_code)
            self.bank_name = template['name']
        
        account_info = self._extract_card_info(df_full)
        transactions = self._extract_transactions(df_full)
        summary = self._generate_summary(transactions, account_info)
        
        return {
            'status': 'success',
            'document_type': 'credit_card',
            'bank_detected': self.bank_name,
            'confidence_score': confidence if self.bank_code else 0.5,
            'account_info': account_info,
            'transactions': transactions,
            'summary': summary
        }
    
    def _extract_card_info(self, df: pd.DataFrame) -> Dict:
        """提取信用卡基本信息"""
        text = df.to_string()
        
        owner_name = self._extract_owner_name(text)
        card_last_4 = self._extract_card_number(text)
        card_type = self._extract_card_type(text)
        statement_date = self._extract_statement_date(text)
        due_date = self._extract_due_date(text)
        card_limit = self._extract_card_limit(text)
        previous_balance = self._extract_previous_balance(text)
        closing_balance = self._extract_closing_balance(df)
        
        return {
            'owner_name': owner_name or 'N/A',
            'bank': self.bank_name,
            'card_last_4': card_last_4 or 'N/A',
            'card_type': card_type or 'N/A',
            'statement_date': statement_date or 'N/A',
            'due_date': due_date or 'N/A',
            'card_limit': card_limit,
            'previous_balance': previous_balance,
            'closing_balance': closing_balance
        }
    
    def _extract_owner_name(self, text: str) -> Optional[str]:
        """提取持卡人姓名"""
        patterns = [
            r'Card[hH]older[:\s]+([A-Z\s]+)',
            r'Name[:\s]+([A-Z\s]+)',
            r'Customer[:\s]+([A-Z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 50:
                    return name
        return None
    
    def _extract_card_number(self, text: str) -> Optional[str]:
        """提取卡号后4位"""
        patterns = [
            r'Card Number[:\s]+[X*]+(\d{4})',
            r'Card[:\s]+[X*]+(\d{4})',
            r'xxxx[- ]?(\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_card_type(self, text: str) -> Optional[str]:
        """提取卡类型"""
        text_upper = text.upper()
        
        card_types = ['VISA', 'MASTERCARD', 'AMEX', 'AMERICAN EXPRESS']
        
        for card_type in card_types:
            if card_type in text_upper:
                return card_type.title()
        
        return None
    
    def _extract_statement_date(self, text: str) -> Optional[str]:
        """提取账单日期"""
        patterns = [
            r'Statement Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'Billing Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """提取到期日"""
        patterns = [
            r'Due Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'Payment Due[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'Pay [Bb]y[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_card_limit(self, text: str) -> float:
        """提取信用额度"""
        patterns = [
            r'Credit Limit[:\s]+([\d,]+\.?\d*)',
            r'Card Limit[:\s]+([\d,]+\.?\d*)',
            r'Limit[:\s]+([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                return float(value)
        return 0.0
    
    def _extract_previous_balance(self, text: str) -> float:
        """提取上期余额"""
        patterns = [
            r'Previous Balance[:\s]+([\d,]+\.?\d*)',
            r'Opening Balance[:\s]+([\d,]+\.?\d*)',
            r'Balance B/F[:\s]+([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                return float(value)
        return 0.0
    
    def _extract_closing_balance(self, df: pd.DataFrame) -> float:
        """提取本期余额"""
        text = df.to_string().upper()
        
        patterns = [
            r'CLOSING BALANCE[:\s]+([\d,]+\.?\d*)',
            r'CURRENT BALANCE[:\s]+([\d,]+\.?\d*)',
            r'TOTAL AMOUNT DUE[:\s]+([\d,]+\.?\d*)',
            r'BALANCE C/F[:\s]+([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1).replace(',', '')
                return float(value)
        
        for col in df.columns:
            if 'BALANCE' in str(col).upper():
                values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(values) > 0:
                    return float(values.iloc[-1])
        
        return 0.0
    
    def _extract_transactions(self, df: pd.DataFrame) -> List[Dict]:
        """提取交易明细"""
        transactions = []
        
        date_col = self._find_column(df, 'Date')
        desc_col = self._find_column(df, 'Description')
        amount_col = self._find_column(df, 'Amount')
        
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
            
            amount = self._parse_amount(row.get(amount_col, 0))
            
            is_credit = 'CR' in description.upper() or amount < 0
            
            if is_credit:
                dr = 0.0
                cr = abs(amount)
            else:
                dr = abs(amount)
                cr = 0.0
            
            main_cat, sub_cat = self.classifier.classify_credit_card_transaction(description)
            
            transactions.append({
                'date': transaction_date,
                'posting_date': transaction_date,
                'description': description.strip(),
                'amount': abs(amount),
                'dr': dr,
                'cr': cr,
                'running_balance': 0.0,
                'category': main_cat,
                'sub_category': sub_cat
            })
        
        running_balance = transactions[0]['dr'] if transactions else 0
        for txn in transactions:
            running_balance += txn['dr'] - txn['cr']
            txn['running_balance'] = running_balance
        
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
        
        if value_str.startswith('(') and value_str.endswith(')'):
            value_str = '-' + value_str[1:-1]
        
        try:
            return float(value_str)
        except:
            return 0.0
    
    def _generate_summary(self, transactions: List[Dict], account_info: Dict) -> Dict:
        """生成汇总统计"""
        total_purchases = sum(txn['dr'] for txn in transactions if txn['category'] == 'Purchases')
        total_payments = sum(txn['cr'] for txn in transactions if txn['category'] == 'Payment')
        total_finance_charges = sum(txn['dr'] for txn in transactions if txn['category'] == 'Finance Charges')
        
        calculated_closing = account_info['previous_balance'] + total_purchases - total_payments + total_finance_charges
        balance_verified = abs(calculated_closing - account_info['closing_balance']) < 0.01
        
        return {
            'total_transactions': len(transactions),
            'total_purchases': total_purchases,
            'total_payments': total_payments,
            'total_finance_charges': total_finance_charges,
            'balance_verified': balance_verified,
            'balance_difference': round(calculated_closing - account_info['closing_balance'], 2)
        }
