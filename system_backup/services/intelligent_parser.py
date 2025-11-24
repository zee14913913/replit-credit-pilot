"""
智能Parser引擎 - 基于System Instruction实现
实现16字段精确提取、CR/DR自动识别与修正、金额一致性校验
"""

import re
import json
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class IntelligentParser:
    """智能Parser引擎，支持多银行、多关键词匹配、CR/DR自动修正"""
    
    def __init__(self, config_path='config/parser_field_keywords.json'):
        """初始化Parser，加载关键词配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.field_keywords = self.config['field_keywords']
        self.transaction_keywords = self.config['transaction_keywords']
        self.date_patterns = self.config['date_patterns']
        self.amount_patterns = self.config['amount_patterns']
    
    def extract_field_by_keywords(self, text: str, field_name: str) -> Optional[str]:
        """
        使用多关键词匹配提取字段
        
        Args:
            text: 账单文本
            field_name: 字段名（如 'statement_date', 'credit_limit'）
        
        Returns:
            提取的字段值，如果未找到则返回None
        """
        keywords = self.field_keywords.get(field_name, [])
        
        for keyword in keywords:
            # 尝试匹配 "Keyword: Value" 或 "Keyword\nValue" 模式
            patterns = [
                rf'{re.escape(keyword)}\s*[:\-]?\s*([^\n]+)',
                rf'{re.escape(keyword)}\s+([A-Z][^\n]+)',
                rf'{re.escape(keyword)}\n\s*([^\n]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # 清理值
                    value = self._normalize_value(value, field_name)
                    if value:
                        return value
        
        return None
    
    def _normalize_value(self, value: str, field_name: str) -> str:
        """
        标准化字段值（去除RM、逗号、多余空格）
        """
        if not value:
            return ""
        
        # 去除多余空格
        value = re.sub(r'\s+', ' ', value).strip()
        
        # 金额字段特殊处理
        if field_name in ['credit_limit', 'current_balance', 'minimum_payment', 'previous_balance']:
            # 去除RM标记
            value = re.sub(r'RM\s*', '', value, flags=re.IGNORECASE)
            # 保留逗号和小数点
            match = re.search(r'([\d,]+\.\d{2})', value)
            if match:
                value = match.group(1)
                # 去除逗号转换为Decimal
                value = value.replace(',', '')
        
        # 日期字段标准化为 YYYY-MM-DD
        if field_name in ['statement_date', 'payment_due_date']:
            value = self._standardize_date(value)
        
        # 卡号只保留数字和空格/破折号
        if field_name == 'card_no':
            value = re.sub(r'[^0-9\s\-*X]', '', value)
        
        return value
    
    def _standardize_date(self, date_str: str) -> str:
        """
        标准化日期格式为 YYYY-MM-DD
        
        支持格式:
        - 28 OCT 25 -> 2025-10-28
        - 16 SEP 2025 -> 2025-09-16
        - 13/10/25 -> 2025-10-13
        """
        if not date_str:
            return ""
        
        # 月份映射
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'mac': '03',
            'apr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09',
            'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        # 尝试 "DD MMM YYYY" 或 "DD MMM YY" 格式
        match = re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2,4})', date_str)
        if match:
            day = match.group(1).zfill(2)
            month = month_map.get(match.group(2).lower(), '01')
            year = match.group(3)
            
            # 处理两位数年份
            if len(year) == 2:
                year = '20' + year
            
            return f"{year}-{month}-{day}"
        
        # 尝试 "DD/MM/YYYY" 或 "DD-MM-YYYY" 格式
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            
            if len(year) == 2:
                year = '20' + year
            
            return f"{year}-{month}-{day}"
        
        return date_str
    
    def extract_transactions(self, text: str, bank_name: str) -> List[Dict]:
        """
        智能提取交易记录，支持CR/DR自动识别与修正
        
        Args:
            text: 账单文本
            bank_name: 银行名称
        
        Returns:
            交易记录列表，每条交易包含: date, description, amount_CR, amount_DR
        """
        transactions = []
        lines = text.split('\n')
        
        # 定位交易区域（PREVIOUS BALANCE 之后）
        transaction_start_idx = 0
        for i, line in enumerate(lines):
            if re.search(r'PREVIOUS BALANCE|Transaction Date|Tarikh Transaksi', line, re.I):
                transaction_start_idx = i + 1
                break
        
        # 提取交易行
        i = transaction_start_idx
        while i < len(lines):
            line = lines[i]
            
            # 检测交易行（以日期开头）
            date_match = None
            for pattern in self.date_patterns:
                date_match = re.search(pattern, line)
                if date_match:
                    break
            
            if date_match:
                transaction = self._parse_transaction_line(lines, i, bank_name)
                if transaction:
                    # CR/DR自动修正
                    transaction = self._correct_cr_dr(transaction)
                    transactions.append(transaction)
            
            i += 1
        
        return transactions
    
    def _parse_transaction_line(self, lines: List[str], start_idx: int, bank_name: str) -> Optional[Dict]:
        """
        解析单条交易行（支持多行描述）
        
        Returns:
            {
                "transaction_date": "2025-10-28",
                "transaction_description": "Shopee Malaysia",
                "amount_CR": 0,
                "amount_DR": 16.39
            }
        """
        line = lines[start_idx]
        
        # 提取日期
        date_match = None
        for pattern in self.date_patterns:
            date_match = re.search(pattern, line)
            if date_match:
                break
        
        if not date_match:
            return None
        
        date_str = date_match.group(0)
        date_standardized = self._standardize_date(date_str)
        
        # 提取金额（CR/DR）
        amount_cr = Decimal('0')
        amount_dr = Decimal('0')
        
        # 查找金额（可能在同一行或下一行）
        combined_text = line
        if start_idx + 1 < len(lines):
            combined_text += " " + lines[start_idx + 1]
        
        # 查找 CR 金额
        cr_match = re.search(r'([\d,]+\.\d{2})\s*CR', combined_text)
        if cr_match:
            amount_cr = Decimal(cr_match.group(1).replace(',', ''))
        
        # 查找 DR 金额（没有CR标记的金额）
        all_amounts = re.findall(r'([\d,]+\.\d{2})(?!\s*CR)', combined_text)
        if all_amounts and amount_cr == 0:
            # 最后一个金额通常是交易金额
            amount_dr = Decimal(all_amounts[-1].replace(',', ''))
        elif all_amounts and amount_cr > 0:
            # 如果有CR，其他金额可能是DR
            for amt in all_amounts:
                amt_decimal = Decimal(amt.replace(',', ''))
                if amt_decimal != amount_cr:
                    amount_dr = amt_decimal
                    break
        
        # 提取描述（日期和金额之间的部分）
        description = line[date_match.end():].strip()
        # 移除金额部分
        description = re.sub(r'[\d,]+\.\d{2}\s*(CR|DR)?', '', description).strip()
        
        # 如果描述为空，尝试从下一行获取
        if not description and start_idx + 1 < len(lines):
            next_line = lines[start_idx + 1]
            if not re.search(r'^\d{1,2}\s+[A-Z]{3}', next_line):  # 不是新的交易行
                description = re.sub(r'[\d,]+\.\d{2}\s*(CR|DR)?', '', next_line).strip()
        
        return {
            "transaction_date": date_standardized,
            "transaction_description": description,
            "amount_CR": float(amount_cr),
            "amount_DR": float(amount_dr)
        }
    
    def _correct_cr_dr(self, transaction: Dict) -> Dict:
        """
        CR/DR自动识别与反转修正
        
        规则:
        - 描述含 "payment", "refund", "rebate" → 应该是CR
        - 描述含 "purchase", "spending", "charge", "interest" → 应该是DR
        
        如果检测到矛盾，自动交换CR/DR的值
        """
        description = transaction['transaction_description'].lower()
        amount_cr = transaction['amount_CR']
        amount_dr = transaction['amount_DR']
        
        # 检测是否应该是Credit（退款/还款）
        is_credit_transaction = any(
            keyword in description 
            for keyword in self.transaction_keywords['payment_refund']
        )
        
        # 检测是否应该是Debit（消费/费用）
        is_debit_transaction = any(
            keyword in description 
            for keyword in self.transaction_keywords['fee_charge']
        ) or 'interest' in description or 'charge' in description
        
        # 修正CR/DR矛盾
        if is_credit_transaction and amount_dr > 0 and amount_cr == 0:
            # 应该是CR但被标记为DR → 交换
            transaction['amount_CR'] = amount_dr
            transaction['amount_DR'] = 0
        elif is_debit_transaction and amount_cr > 0 and amount_dr == 0:
            # 应该是DR但被标记为CR → 交换
            transaction['amount_DR'] = amount_cr
            transaction['amount_CR'] = 0
        
        return transaction
    
    def validate_balance_consistency(self, 
                                     previous_balance: float,
                                     current_balance: float,
                                     transactions: List[Dict]) -> Dict:
        """
        金额一致性校验
        
        公式: previous_balance + sum(amount_DR) - sum(amount_CR) = current_balance
        
        Returns:
            {
                "is_valid": True/False,
                "calculated_balance": float,
                "difference": float,
                "message": str
            }
        """
        if not transactions:
            return {
                "is_valid": False,
                "calculated_balance": 0,
                "difference": 0,
                "message": "No transactions found"
            }
        
        total_dr = sum(t['amount_DR'] for t in transactions)
        total_cr = sum(t['amount_CR'] for t in transactions)
        
        calculated_balance = previous_balance + total_dr - total_cr
        difference = abs(calculated_balance - current_balance)
        
        # 允许0.01的误差（浮点数精度问题）
        is_valid = difference < 0.02
        
        return {
            "is_valid": is_valid,
            "calculated_balance": round(calculated_balance, 2),
            "difference": round(difference, 2),
            "message": "Balance validated" if is_valid else f"Difference: RM{difference:.2f}"
        }
    
    def parse_statement(self, text: str, bank_name: str) -> Dict:
        """
        解析完整账单，提取16个字段
        
        Returns:
            {
                "bank_name": str,
                "customer_name": str,
                "ic_no": str,
                "card_type": str,
                "card_no": str,
                "credit_limit": str,
                "statement_date": str,
                "payment_due_date": str,
                "previous_balance": str,
                "current_balance": str,
                "minimum_payment": str,
                "transactions": [
                    {
                        "transaction_date": str,
                        "transaction_description": str,
                        "amount_CR": float,
                        "amount_DR": float,
                        "earned_point": ""
                    }
                ],
                "validation": {
                    "is_valid": bool,
                    "calculated_balance": float,
                    "difference": float
                }
            }
        """
        result = {
            "bank_name": bank_name,
            "customer_name": self.extract_field_by_keywords(text, 'customer_name') or "",
            "ic_no": self.extract_field_by_keywords(text, 'ic_no') or "",
            "card_type": self.extract_field_by_keywords(text, 'card_type') or "",
            "card_no": self.extract_field_by_keywords(text, 'card_no') or "",
            "credit_limit": self.extract_field_by_keywords(text, 'credit_limit') or "",
            "statement_date": self.extract_field_by_keywords(text, 'statement_date') or "",
            "payment_due_date": self.extract_field_by_keywords(text, 'payment_due_date') or "",
            "previous_balance": self.extract_field_by_keywords(text, 'previous_balance') or "",
            "current_balance": self.extract_field_by_keywords(text, 'current_balance') or "",
            "minimum_payment": self.extract_field_by_keywords(text, 'minimum_payment') or "",
            "transactions": []
        }
        
        # 提取交易
        transactions = self.extract_transactions(text, bank_name)
        result['transactions'] = transactions
        
        # 验证余额一致性
        try:
            prev_bal = float(result['previous_balance']) if result['previous_balance'] else 0
            curr_bal = float(result['current_balance']) if result['current_balance'] else 0
            validation = self.validate_balance_consistency(prev_bal, curr_bal, transactions)
            result['validation'] = validation
        except (ValueError, TypeError):
            result['validation'] = {
                "is_valid": False,
                "message": "Unable to validate - missing balance data"
            }
        
        return result
