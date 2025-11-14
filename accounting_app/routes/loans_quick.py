"""
Phase 8.1: Quick Estimate API Endpoints
快速评估API - 收入估算 & 收入+债务估算
"""
from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


# ===============================
# MODE 1 — INCOME ONLY
# ===============================
class QuickIncomeRequest(BaseModel):
    income: float


@router.post("/api/loans/quick-income")
def quick_income_api(req: QuickIncomeRequest):
    """Quick Estimate - Income Only"""
    from accounting_app.services.risk_engine.personal_rules import estimate_risk_income_only
    return estimate_risk_income_only(req.income)


# ===============================
# MODE 2 — INCOME + COMMITMENTS
# ===============================
class QuickIncomeCommitRequest(BaseModel):
    income: float
    commitments: float


@router.post("/api/loans/quick-income-commitment")
def quick_income_commit_api(req: QuickIncomeCommitRequest):
    """Quick Estimate - Income + Commitments"""
    from accounting_app.services.risk_engine.personal_rules import estimate_risk_income_commitments
    return estimate_risk_income_commitments(req.income, req.commitments)
