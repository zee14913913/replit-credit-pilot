"""
Phase 8.2: AI & Product Matching Router
提供产品推荐和AI贷款顾问功能
"""
from fastapi import APIRouter
from pydantic import BaseModel

from accounting_app.services.loan_products import LoanProductMatcher
from accounting_app.services.risk_engine.personal_rules import (
    personal_risk_grade_explainer
)

router = APIRouter()


# ============================================================
# MODE: PRODUCT RECOMMENDATIONS
# ============================================================

class ProductRequest(BaseModel):
    risk_grade: str | None = None
    income: float | None = None
    dti: float | None = None
    max_loan_amount: float | None = None


@router.post("/api/loans/product-recommendations")
def product_recommendations(req: ProductRequest):
    """根据风险评级和收入推荐贷款产品"""
    
    # default max loan if missing (for income-only mode)
    max_loan = req.max_loan_amount or (req.income or 0) * 30

    products = LoanProductMatcher.match_personal_loan_v2(
        risk_grade=req.risk_grade or "B",
        income=req.income or 0,
        monthly_commitment=(req.dti or 0) * (req.income or 1),
        ccris_bucket=0,
        credit_score=700,
        max_loan_amount=max_loan,
        top_n=10
    )

    return {"products": products}


# ============================================================
# MODE: AI LOAN ADVISOR
# ============================================================

class AdvisorRequest(BaseModel):
    risk_grade: str | None = None
    dti: float | None = None
    income: float | None = None
    commitments: float | None = None


@router.post("/api/loans/advisor")
def advisor(req: AdvisorRequest):
    """AI贷款顾问 - 提供风险评级解释和建议"""
    
    text = personal_risk_grade_explainer(
        risk_grade=req.risk_grade or "B",
        dti=req.dti or 0,
        income=req.income or 0,
        commitments=req.commitments or 0
    )

    return {"explanation": text}
