"""
Reporting Module - 银行级贷款报告生成系统
PHASE 5: 专业HTML/PDF报告 + Bank Loan Advisor AI

功能：
- 个人/SME贷款报告生成
- 风险评估解释
- 产品推荐摘要
- PDF导出
- AI顾问说明
"""
from .report_builder import LoanReportBuilder
from .report_sections import (
    build_customer_profile_section,
    build_income_commitment_section,
    build_risk_assessment_section,
    build_product_recommendation_section
)
from .advisor_explanations import (
    explain_risk_grade,
    explain_sme_brr,
    generate_overall_summary
)
from .pdf_renderer import generate_personal_pdf, generate_sme_pdf

__all__ = [
    'LoanReportBuilder',
    'build_customer_profile_section',
    'build_income_commitment_section',
    'build_risk_assessment_section',
    'build_product_recommendation_section',
    'explain_risk_grade',
    'explain_sme_brr',
    'generate_overall_summary',
    'generate_personal_pdf',
    'generate_sme_pdf'
]
