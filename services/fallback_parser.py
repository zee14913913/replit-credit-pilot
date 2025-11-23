
#!/usr/bin/env python3
"""
Fallback Parser - 免费本地PDF解析器
完全替代 Google Document AI
支持马来西亚所有银行的信用卡账单
"""
import re
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class FallbackParser:
    """免费本地解析器 - 无需任何外部API"""
    
    def __init__(self):
        self.bank_patterns = {
            'AMBANK': {
                'customer_name': r'([A-Z][A-Z\s]+)\s+NO\s+\d+\s+JLN',
                'card_number': r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})',
                'statement_date': r'Statement Date[\s\S]*?(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2,4})',
                'payment_due_date': r'Payment Due Date[\s\S]*?(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2,4})',
                'current_balance': r'Current Balance[\s\S]*?([\.\d,]+)',
                'minimum_payment': r'Minimum Payment[\s\S]*?([\.\d,]+)',
                'credit_limit': r'Total Credit Limit[\s\S]*?([\.\d,]+)',
                'previous_balance': r'Previous Balance[\s\S]*?([\.\d,]+)',
            },
            'AMBANK_ISLAMIC': {
                'customer_name': r'^([A-Z][A-Z\s]+)$',  # 单独一行的大写姓名
                'card_number': r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})',
                'statement_date': r'Statement Date[^\d]*(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2})',
                'payment_due_date': r'Payment Due Date[^\d]*(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2})',
                'current_balance': r'Total Current Balance\s+([\d,]+\.\d{2})',
                'minimum_payment': r'Total\s+[\d,]+\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})',  # 第二个数字
                'credit_limit': r'Total Credit Limit[^\d]*([\d,]+)',
                'previous_balance': r'PREVIOUS BALANCE\s+([\d,]+\.\d{2})',
            },
            'HSBC': {
                'customer_name': r'([A-Z][A-Z\s]+)',
                'card_number': r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})',
                'statement_date': r'Statement Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'payment_due_date': r'Payment Due Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'current_balance': r'New Balance[\s\S]*?([\.\d,]+)',
                'minimum_payment': r'Minimum Payment[\s\S]*?([\.\d,]+)',
            },
            'UOB': {
                'customer_name': r'([A-Z][A-Z\s]+)',
                'card_number': r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})',
                'statement_date': r'Statement Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'payment_due_date': r'Payment Due Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'current_balance': r'Total Amount Due[\s\S]*?([\.\d,]+)',
                'minimum_payment': r'Minimum Payment[\s\S]*?([\.\d,]+)',
            },
            'HONG_LEONG': {
                'customer_name': r'([A-Z][A-Z\s]+)',
                'card_number': r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})',
                'statement_date': r'Statement Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'payment_due_date': r'Payment Due Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'current_balance': r'Total Amount Due[\s\S]*?([\.\d,]+)',
                'minimum_payment': r'Minimum Payment[\s\S]*?([\.\d,]+)',
            },
            'OCBC': {
                'customer_name': r'([A-Z][A-Z\s]+)',
                'card_number': r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})',
                'statement_date': r'Statement Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'payment_due_date': r'Payment Due Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'current_balance': r'New Balance[\s\S]*?([\.\d,]+)',
                'minimum_payment': r'Minimum Payment[\s\S]*?([\.\d,]+)',
            },
            'STANDARD_CHARTERED': {
                'customer_name': r'([A-Z][A-Z\s]+)',
                'card_number': r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})',
                'statement_date': r'Statement Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'payment_due_date': r'Payment Due Date[\s\S]*?(\d{1,2}\s+[A-Z]{3}\s+\d{4})',
                'current_balance': r'Total Amount Due[\s\S]*?([\.\d,]+)',
                'minimum_payment': r'Minimum Payment[\s\S]*?([\.\d,]+)',
            },
        }
    
    def parse_pdf(self, pdf_path: str) -> Tuple[Dict, List[Dict]]:
        """解析PDF文件，返回(info, transactions)"""
        try:
            # 使用 pdfplumber 提取文本
            import pdfplumber
            
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            
            logger.info(f"✅ 提取文本完成（{len(text)} 字符）")
            
            # 识别银行
            bank_name = self._detect_bank(text)
            logger.info(f"🏦 识别银行: {bank_name}")
            
            # 提取字段
            info = self._extract_fields(text, bank_name)
            
            # 提取交易
            transactions = self._extract_transactions(text, bank_name)
            
            logger.info(f"✅ 解析完成: {len(transactions)}笔交易")
            
            return info, transactions
            
        except Exception as e:
            logger.error(f"❌ Fallback解析失败: {e}")
            raise
    
    def _detect_bank(self, text: str) -> str:
        """识别银行"""
        text_upper = text.upper()
        
        if 'AMBANK' in text_upper:
            if 'ISLAMIC' in text_upper:
                return 'AMBANK_ISLAMIC'
            return 'AMBANK'
        elif 'HSBC' in text_upper:
            return 'HSBC'
        elif 'UOB' in text_upper:
            return 'UOB'
        elif 'HONG LEONG' in text_upper or 'HLB' in text_upper:
            return 'HONG_LEONG'
        elif 'OCBC' in text_upper:
            return 'OCBC'
        elif 'STANDARD CHARTERED' in text_upper or 'SCB' in text_upper:
            return 'STANDARD_CHARTERED'
        
        return 'UNKNOWN'
    
    def _extract_fields(self, text: str, bank_name: str) -> Dict:
        """提取账单字段"""
        info = {
            'bank_name': bank_name,
            'customer_name': None,
            'card_last4': None,
            'statement_date': None,
            'payment_due_date': None,
            'current_balance': 0.0,
            'minimum_payment': 0.0,
            'previous_balance': 0.0,
            'credit_limit': 0.0,
        }
        
        patterns = self.bank_patterns.get(bank_name, {})
        
        # 提取客户姓名
        if 'customer_name' in patterns:
            match = re.search(patterns['customer_name'], text)
            if match:
                info['customer_name'] = match.group(1).strip()
        
        # 提取卡号
        if 'card_number' in patterns:
            match = re.search(patterns['card_number'], text)
            if match:
                full_card = match.group(1).replace(' ', '')
                info['card_last4'] = full_card[-4:]
        
        # 提取账单日期
        if 'statement_date' in patterns:
            match = re.search(patterns['statement_date'], text, re.IGNORECASE)
            if match:
                info['statement_date'] = match.group(1)
        
        # 提取到期日期
        if 'payment_due_date' in patterns:
            match = re.search(patterns['payment_due_date'], text, re.IGNORECASE)
            if match:
                info['payment_due_date'] = match.group(1)
        
        # 提取余额信息
        for field in ['current_balance', 'minimum_payment', 'previous_balance', 'credit_limit']:
            if field in patterns:
                match = re.search(patterns[field], text, re.IGNORECASE)
                if match:
                    info[field] = self._parse_amount(match.group(1))
        
        return info
    
    def _extract_transactions(self, text: str, bank_name: str) -> List[Dict]:
        """提取交易记录"""
        transactions = []
        lines = text.split('\n')
        
        # 通用交易匹配模式
        # 格式: 日期 + 日期 + 描述 + 金额 + 可选CR标记
        # 修复：直接捕获紧贴或空格分隔的CR标记
        trans_pattern = r'(\d{2}\s+[A-Z]{3}(?:\s+\d{2,4})?)\s+(\d{2}\s+[A-Z]{3}(?:\s+\d{2,4})?)\s+(.{10,80}?)\s+([\d,]+\.\d{2})\s*(CR)?'
        
        for line in lines:
            match = re.search(trans_pattern, line)
            if match:
                trans_date = match.group(1)
                post_date = match.group(2)
                description = match.group(3).strip()
                amount_str = match.group(4)  # 纯数字金额
                cr_marker = match.group(5)    # CR标记（如果存在）
                
                # 判断 CR/DR（仅依赖cr_marker组）
                is_credit = cr_marker is not None
                amount = self._parse_amount(amount_str)
                
                transactions.append({
                    'transaction_date': trans_date,
                    'posting_date': post_date,
                    'description': description,
                    'amount': float(amount),
                    'type': 'CR' if is_credit else 'DR'
                })
        
        # 如果没有提取到交易，尝试简化模式
        if len(transactions) == 0:
            simple_pattern = r'(\d{2}\s+[A-Z]{3})\s+(.{15,60}?)\s+([\d,]+\.\d{2})\s*(CR)?'
            for line in lines:
                match = re.search(simple_pattern, line)
                if match:
                    date = match.group(1)
                    description = match.group(2).strip()
                    amount_str = match.group(3)
                    cr_marker = match.group(4)
                    amount = self._parse_amount(amount_str)
                    
                    # 判断类型（仅依赖cr_marker组）
                    is_credit = cr_marker is not None
                    
                    transactions.append({
                        'transaction_date': date,
                        'posting_date': date,
                        'description': description,
                        'amount': float(amount),
                        'type': 'CR' if is_credit else 'DR'
                    })
        
        return transactions
    
    def _parse_amount(self, text: str) -> float:
        """解析金额"""
        try:
            cleaned = re.sub(r'[^\d.]', '', text)
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0


# 便捷函数
def parse_statement_fallback(pdf_path: str) -> Tuple[Dict, List[Dict]]:
    """使用Fallback Parser解析账单"""
    parser = FallbackParser()
    return parser.parse_pdf(pdf_path)
