"""
Business Loans API Routes

提供企业贷款（SME Loan）评估功能，基于 DSCR 计算

Author: AI Loan Evaluation System
Date: 2025-01-14
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from accounting_app.db import get_db
from accounting_app.models import Customer
from accounting_app.services.business_loan_engine import BusinessLoanEngine


router = APIRouter(prefix="/api/business-loans", tags=["Business Loans"])


@router.get("/eligibility/{customer_id}")
def get_business_loan_eligibility(
    customer_id: int,
    company_id: int = Query(1, description="公司ID"),
    db: Session = Depends(get_db)
):
    """
    获取企业贷款资格评估（基于DSCR）
    
    DSCR (Debt Service Coverage Ratio) = Operating Income / Annual Debt Service
    
    功能：
    1. 从会计账目提取企业营业收入（operating_income）
    2. 从月结单计算年度债务服务（annual_debt_service = monthly × 12）
    3. 计算 DSCR 比率
    4. 判定资格状态（Eligible/Borderline/Not Eligible）
    5. 计算可承受债务额度和可借款能力
    
    分类规则：
    - DSCR ≥ 1.25 → Eligible
    - 1.00 ≤ DSCR < 1.25 → Borderline
    - DSCR < 1.00 → Not Eligible
    
    Args:
        customer_id: 客户ID
        company_id: 公司ID
        db: 数据库会话
        
    Returns:
        {
            "customer_id": 1,
            "operating_income": 500000.00,
            "annual_debt_service": 120000.00,
            "monthly_debt_service": 10000.00,
            "dscr": 4.1667,
            "eligibility_status": "Eligible",
            "max_debt_service": 400000.00,
            "available_capacity": 280000.00,
            "max_annual_loan": 280000.00,
            "max_monthly_loan": 23333.33
        }
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"客户ID {customer_id} 不存在"
        )
    
    try:
        result = BusinessLoanEngine.calculate_dscr(
            db=db,
            customer_id=customer_id,
            company_id=company_id
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"计算企业贷款资格失败: {str(e)}"
        )
