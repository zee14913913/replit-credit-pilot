"""
INFINITE GZ - Excel/CSV 解析器模块
==================================
双轨并行方案：Excel/CSV优先 + PDF OCR备用

模块包含：
- bank_statement_excel_parser.py: 银行流水Excel解析器
- credit_card_excel_parser.py: 信用卡Excel解析器
- bank_detector.py: 银行格式自动识别
- transaction_classifier.py: 30+智能分类系统
"""

from .bank_statement_excel_parser import BankStatementExcelParser
from .credit_card_excel_parser import CreditCardExcelParser
from .bank_detector import BankDetector
from .transaction_classifier import TransactionClassifier

__all__ = [
    'BankStatementExcelParser',
    'CreditCardExcelParser',
    'BankDetector',
    'TransactionClassifier'
]

__version__ = '1.0.0'
__author__ = 'INFINITE GZ SDN BHD'
