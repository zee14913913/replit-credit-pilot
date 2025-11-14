"""
Loan Eligibility - 贷款资格评估路由
调用 LoanEligibilityEngine 进行DSR/DSRC计算
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..services.loan_eligibility_engine import LoanEligibilityEngine
from ..models import Customer

router = APIRouter(prefix="/api/loans", tags=["Loan Eligibility"])


@router.get("/eligibility/{customer_id}")
async def get_loan_eligibility(
    customer_id: int,
    company_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    获取客户贷款资格评估
    
    Args:
        customer_id: 客户ID
        company_id: 公司ID（默认1）
        
    Returns:
        包含以下信息的JSON:
        - customer_id: 客户ID
        - dsr_income: DSR计算用收入
        - dsrc_income: DSRC计算用收入
        - best_source: 收入来源类型
        - income_confidence: 收入置信度
        - total_monthly_debt: 月度债务（owner_payments + gz_payments + min_payment）
        - dsr_ratio: DSR比率（total_debt / dsr_income）
        - dsrc_ratio: DSRC比率（total_debt / dsrc_income）
        - eligibility_status: Eligible / Borderline / Not Eligible
        - recommended_loan_amount: 建议贷款额度（= dsrc_income × 8）
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户ID {customer_id} 不存在")
    
    try:
        result = LoanEligibilityEngine.calculate(
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
            detail=f"计算贷款资格失败: {str(e)}"
        )
