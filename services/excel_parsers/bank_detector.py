"""
银行格式自动识别器
================
自动检测Excel/CSV文件属于哪家银行，并返回对应的解析模板

支持银行：
- Public Bank (PBB)
- Maybank (MBB)
- CIMB Bank
- RHB Bank
- Hong Leong Bank (HLB)
- AmBank
- Alliance Bank
"""

import pandas as pd
import re
from typing import Dict, Optional, Tuple


class BankDetector:
    """银行格式自动识别器"""
    
    BANK_SIGNATURES = {
        'PUBLIC_BANK': [
            'PUBLIC BANK',
            'PBB',
            'Public Bank Berhad',
            'RM ACE Account',
            'Account Number: 3'
        ],
        'MAYBANK': [
            'MAYBANK',
            'Malayan Banking Berhad',
            'M2U',
            'Maybank2u'
        ],
        'CIMB': [
            'CIMB BANK',
            'CIMB Bank Berhad',
            'CIMB Clicks'
        ],
        'RHB': [
            'RHB BANK',
            'RHB Banking Group',
            'RHB Now'
        ],
        'HONG_LEONG': [
            'HONG LEONG BANK',
            'HLB',
            'Hong Leong Connect'
        ],
        'AMBANK': [
            'AMBANK',
            'AmBank Group'
        ],
        'ALLIANCE': [
            'ALLIANCE BANK',
            'Alliance Bank Malaysia'
        ]
    }
    
    def __init__(self):
        self.detected_bank = None
        self.confidence_score = 0.0
    
    def detect_from_excel(self, file_path: str) -> Tuple[Optional[str], float]:
        """
        从Excel文件检测银行
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            (银行代码, 置信度分数)
        """
        try:
            df = pd.read_excel(file_path, nrows=20)
            return self._detect_from_dataframe(df)
        except Exception as e:
            print(f"Excel读取错误: {e}")
            return None, 0.0
    
    def detect_from_csv(self, file_path: str) -> Tuple[Optional[str], float]:
        """
        从CSV文件检测银行
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            (银行代码, 置信度分数)
        """
        try:
            df = pd.read_csv(file_path, nrows=20, encoding='utf-8')
            return self._detect_from_dataframe(df)
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, nrows=20, encoding='gbk')
                return self._detect_from_dataframe(df)
            except Exception as e:
                print(f"CSV读取错误: {e}")
                return None, 0.0
        except Exception as e:
            print(f"CSV读取错误: {e}")
            return None, 0.0
    
    def _detect_from_dataframe(self, df: pd.DataFrame) -> Tuple[Optional[str], float]:
        """
        从DataFrame检测银行
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            (银行代码, 置信度分数)
        """
        text_content = df.to_string().upper()
        
        scores = {}
        
        for bank_code, signatures in self.BANK_SIGNATURES.items():
            match_count = 0
            for signature in signatures:
                if signature.upper() in text_content:
                    match_count += 1
            
            if match_count > 0:
                scores[bank_code] = match_count / len(signatures)
        
        if not scores:
            return None, 0.0
        
        best_match = max(scores.items(), key=lambda x: x[1])
        self.detected_bank = best_match[0]
        self.confidence_score = best_match[1]
        
        return self.detected_bank, self.confidence_score
    
    def get_bank_template(self, bank_code: str) -> Dict:
        """
        获取银行解析模板配置
        
        Args:
            bank_code: 银行代码
            
        Returns:
            解析模板字典
        """
        templates = {
            'PUBLIC_BANK': {
                'name': 'Public Bank',
                'date_format': '%d-%m-%Y',
                'date_column': 'Transaction Date',
                'description_column': 'Transaction Description',
                'debit_column': 'Debit',
                'credit_column': 'Credit',
                'balance_column': 'Balance',
                'header_rows': 10,
                'account_number_pattern': r'Account Number[:\s]+(\d+)'
            },
            'MAYBANK': {
                'name': 'Maybank',
                'date_format': '%d/%m/%Y',
                'date_column': 'Date',
                'description_column': 'Description',
                'debit_column': 'Withdrawal',
                'credit_column': 'Deposit',
                'balance_column': 'Balance',
                'header_rows': 8,
                'account_number_pattern': r'Account No[:\s]+(\d+)'
            },
            'CIMB': {
                'name': 'CIMB Bank',
                'date_format': '%d/%m/%Y',
                'date_column': 'Date',
                'description_column': 'Description',
                'debit_column': 'Debit',
                'credit_column': 'Credit',
                'balance_column': 'Running Balance',
                'header_rows': 7,
                'account_number_pattern': r'Account[:\s]+(\d+)'
            }
        }
        
        return templates.get(bank_code, templates['PUBLIC_BANK'])
    
    def detect_document_type(self, df: pd.DataFrame) -> str:
        """
        检测文档类型：bank_statement 或 credit_card
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            'bank_statement' 或 'credit_card'
        """
        text = df.to_string().upper()
        
        credit_card_keywords = [
            'CREDIT CARD',
            'CARD LIMIT',
            'MINIMUM PAYMENT',
            'CARD TYPE',
            'VISA',
            'MASTERCARD',
            'AMEX'
        ]
        
        bank_statement_keywords = [
            'ACCOUNT NUMBER',
            'OPENING BALANCE',
            'CLOSING BALANCE',
            'CURRENT ACCOUNT',
            'SAVINGS ACCOUNT'
        ]
        
        cc_score = sum(1 for kw in credit_card_keywords if kw in text)
        bs_score = sum(1 for kw in bank_statement_keywords if kw in text)
        
        return 'credit_card' if cc_score > bs_score else 'bank_statement'
