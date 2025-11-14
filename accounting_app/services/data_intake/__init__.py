"""
Data Intake Layer - 自动数据采集层
为Modern贷款引擎提供智能数据解析能力

负责从原始文档中自动提取：
- CCRIS Bucket & Behavior Score
- CTOS SME Score & Risk Band
- Bank Statement Cashflow Variance
- Employment Stability & Years
- Industry Classification (BNM标准)
- Multi-source Income Aggregation
"""
from .ccris_parser import CCRISParser
from .ctos_parser import CTOSParser
from .bank_statement_analyzer import BankStatementAnalyzer
from .employment_detector import EmploymentDetector
from .industry_classifier import IndustryClassifier
from .income_detector import IncomeDetector
from .auto_enrichment import AutoEnrichment

__all__ = [
    "CCRISParser",
    "CTOSParser",
    "BankStatementAnalyzer",
    "EmploymentDetector",
    "IndustryClassifier",
    "IncomeDetector",
    "AutoEnrichment"
]
