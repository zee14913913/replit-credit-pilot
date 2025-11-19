"""
字段格式标准化模块
处理日期、金额、卡号等字段的格式清洗
"""

import re
from datetime import datetime
from typing import Optional


class FieldNormalizer:
    """字段格式标准化处理器"""
    
    def __init__(self):
        self.month_map = {
            'jan': '01', 'january': '01',
            'feb': '02', 'february': '02',
            'mar': '03', 'march': '03', 'mac': '03',
            'apr': '04', 'april': '04',
            'may': '05',
            'jun': '06', 'june': '06',
            'jul': '07', 'july': '07',
            'aug': '08', 'august': '08',
            'sep': '09', 'september': '09',
            'oct': '10', 'october': '10',
            'nov': '11', 'november': '11',
            'dec': '12', 'december': '12'
        }
    
    def normalize_date(self, date_str: str) -> str:
        """
        标准化日期格式为 YYYY-MM-DD
        
        支持格式:
        - 28 OCT 25 -> 2025-10-28
        - 16 SEP 2025 -> 2025-09-16
        - 13/10/25 -> 2025-10-13
        - 2025-10-13 -> 2025-10-13 (已标准化)
        
        Args:
            date_str: 原始日期字符串
        
        Returns:
            YYYY-MM-DD 格式的日期，失败返回空字符串
        """
        if not date_str:
            return ''
        
        date_str = date_str.strip()
        
        # 已经是标准格式
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # 格式1: DD MMM YYYY 或 DD MMM YY (例: 28 OCT 25, 16 SEP 2025)
        match = re.search(r'(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{2,4})', date_str)
        if match:
            day = match.group(1).zfill(2)
            month_name = match.group(2).lower()
            year = match.group(3)
            
            month = self.month_map.get(month_name, '01')
            
            # 处理两位数年份
            if len(year) == 2:
                year = '20' + year
            
            return f"{year}-{month}-{day}"
        
        # 格式2: DD/MM/YYYY 或 DD-MM-YYYY
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            
            if len(year) == 2:
                year = '20' + year
            
            return f"{year}-{month}-{day}"
        
        # 格式3: YYYY/MM/DD
        match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', date_str)
        if match:
            year = match.group(1)
            month = match.group(2).zfill(2)
            day = match.group(3).zfill(2)
            
            return f"{year}-{month}-{day}"
        
        return ''
    
    def normalize_amount(self, amount_str: str) -> float:
        """
        标准化金额：去除 RM、逗号，转换为 float
        
        Examples:
        - "RM1,234.56" -> 1234.56
        - "1,234.56 CR" -> 1234.56
        - "RM 1234.56" -> 1234.56
        
        Args:
            amount_str: 原始金额字符串
        
        Returns:
            float 金额
        """
        if not amount_str:
            return 0.0
        
        # 去除 RM 标记
        cleaned = re.sub(r'RM\s*', '', str(amount_str), flags=re.IGNORECASE)
        
        # 去除 CR/DR 标记
        cleaned = re.sub(r'\s*(CR|DR)\s*', '', cleaned, flags=re.IGNORECASE)
        
        # 去除逗号
        cleaned = cleaned.replace(',', '')
        
        # 去除空格
        cleaned = cleaned.strip()
        
        # 提取数字（包括小数点和负号）
        match = re.search(r'(-?[\d.]+)', cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        
        return 0.0
    
    def normalize_card_number(self, card_no: str) -> str:
        """
        标准化卡号：保留数字、空格、破折号，移除其他字符
        
        Examples:
        - "4031 4899 9530 6354" -> "4031 4899 9530 6354"
        - "4031-4899-9530-6354" -> "4031-4899-9530-6354"
        - "4031*****6354" -> "4031*****6354"
        
        Args:
            card_no: 原始卡号
        
        Returns:
            清洗后的卡号
        """
        if not card_no:
            return ''
        
        # 只保留数字、空格、破折号、星号、X
        cleaned = re.sub(r'[^0-9\s\-*X]', '', card_no)
        
        # 移除多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def mask_card_number(self, card_no: str, keep_last: int = 4) -> str:
        """
        遮罩卡号（保护隐私）
        
        Args:
            card_no: 原始卡号
            keep_last: 保留最后几位数字
        
        Returns:
            遮罩后的卡号（例: **** **** **** 6354）
        """
        # 提取纯数字
        digits = re.sub(r'[^0-9]', '', card_no)
        
        if len(digits) < keep_last:
            return card_no
        
        # 保留最后N位，其他用星号替换
        masked = '*' * (len(digits) - keep_last) + digits[-keep_last:]
        
        # 每4位添加空格
        return ' '.join([masked[i:i+4] for i in range(0, len(masked), 4)])
    
    def normalize_ic_number(self, ic_no: str) -> str:
        """
        标准化 IC 号码（马来西亚身份证）
        
        Args:
            ic_no: 原始 IC 号码
        
        Returns:
            清洗后的 IC 号码（纯数字）
        """
        if not ic_no:
            return ''
        
        # 只保留数字
        cleaned = re.sub(r'[^0-9]', '', ic_no)
        
        return cleaned
    
    def normalize_all_fields(self, data: dict) -> dict:
        """
        标准化所有字段
        
        Args:
            data: 原始数据字典
        
        Returns:
            标准化后的数据字典
        """
        normalized = data.copy()
        
        # 标准化日期字段
        if 'statement_date' in normalized:
            normalized['statement_date'] = self.normalize_date(normalized['statement_date'])
        
        if 'payment_due_date' in normalized:
            normalized['payment_due_date'] = self.normalize_date(normalized['payment_due_date'])
        
        # 标准化金额字段
        for field in ['credit_limit', 'previous_balance', 'current_balance', 'minimum_payment']:
            if field in normalized:
                normalized[field] = self.normalize_amount(normalized[field])
        
        # 标准化卡号
        if 'card_no' in normalized:
            normalized['card_no'] = self.normalize_card_number(normalized['card_no'])
        
        # 标准化 IC 号码
        if 'ic_no' in normalized:
            normalized['ic_no'] = self.normalize_ic_number(normalized['ic_no'])
        
        # 标准化交易
        if 'transactions' in normalized:
            normalized['transactions'] = [
                self._normalize_transaction(t) for t in normalized['transactions']
            ]
        
        return normalized
    
    def _normalize_transaction(self, transaction: dict) -> dict:
        """标准化单条交易记录"""
        normalized = transaction.copy()
        
        # 标准化交易日期
        if 'transaction_date' in normalized:
            normalized['transaction_date'] = self.normalize_date(normalized['transaction_date'])
        
        # 标准化金额
        if 'amount_CR' in normalized:
            normalized['amount_CR'] = self.normalize_amount(normalized['amount_CR'])
        
        if 'amount_DR' in normalized:
            normalized['amount_DR'] = self.normalize_amount(normalized['amount_DR'])
        
        # 清理描述（去除多余空格）
        if 'transaction_description' in normalized:
            desc = normalized['transaction_description']
            normalized['transaction_description'] = re.sub(r'\s+', ' ', desc).strip()
        
        return normalized
