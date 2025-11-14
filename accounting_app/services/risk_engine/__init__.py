"""
Risk Engine - 马来西亚银行风控引擎
Modern Malaysian banking approval engine (DTI/FOIR/BRR/DSCR)
"""
from .personal_rules import PersonalLoanRules
from .sme_rules import SMELoanRules
from .risk_utils import RiskUtils
from .scoring_matrix import ScoringMatrix

__all__ = [
    "PersonalLoanRules",
    "SMELoanRules",
    "RiskUtils",
    "ScoringMatrix"
]
