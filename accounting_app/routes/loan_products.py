"""
Loan Products API Routes

提供多贷款产品模拟功能

Author: AI Loan Evaluation System
Date: 2025-01-14
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from accounting_app.db import get_db
from accounting_app.models import Customer
from accounting_app.services.loan_product_engine import LoanProductEngine
from accounting_app.services.income_service import IncomeService


router = APIRouter(prefix="/api/loans", tags=["Loan Products"])


@router.get("/products/{customer_id}")
def get_loan_products(
    customer_id: int,
    loan_amount: Optional[float] = Query(None, description="指定贷款金额，若未提供则使用建议贷款额度"),
    company_id: int = Query(1, description="公司ID"),
    db: Session = Depends(get_db)
):
    """
    获取客户的多贷款产品模拟
    
    功能：
    1. 根据 customer_id 自动获取标准化收入（DSR/DSRC）
    2. 计算建议贷款额度（= dsrc_income × 8）
    3. 模拟多种贷款产品，返回月供、利率、总利息、总成本
    
    Args:
        customer_id: 客户ID
        loan_amount: 指定贷款金额（可选，默认使用建议贷款额度）
        company_id: 公司ID
        db: 数据库会话
        
    Returns:
        {
            "customer_id": 1,
            "dsr_income": 10000.00,
            "dsrc_income": 12000.00,
            "recommended_loan_amount": 96000.00,
            "loan_amount": 100000.00,
            "products": [
                {
                    "name": "Flat Rate Personal Loan",
                    "interest_rate": 0.08,
                    "tenure_months": 60,
                    "monthly_payment": 2500.00,
                    "total_interest": 12000.00,
                    "total_cost": 112000.00
                },
                ...
            ]
        }
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"客户ID {customer_id} 不存在"
        )
    
    try:
        income_data = IncomeService.get_customer_income(
            db=db,
            customer_id=customer_id,
            company_id=company_id
        )
        
        if not income_data:
            raise HTTPException(
                status_code=404,
                detail=f"客户ID {customer_id} 无收入数据"
            )
        
        dsr_income = income_data.get("dsr_income") or 0.0
        dsrc_income = income_data.get("dsrc_income") or 0.0
        
        recommended_loan_amount = dsrc_income * 8 if dsrc_income > 0 else 0.0
        
        final_loan_amount = loan_amount if loan_amount is not None else recommended_loan_amount
        
        if final_loan_amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="贷款金额必须大于0。请提供 loan_amount 参数或确保客户有有效的收入数据。"
            )
        
        products = LoanProductEngine.simulate_all_products(
            loan_amount=final_loan_amount
        )
        
        return {
            "customer_id": customer_id,
            "dsr_income": round(dsr_income, 2),
            "dsrc_income": round(dsrc_income, 2),
            "recommended_loan_amount": round(recommended_loan_amount, 2),
            "loan_amount": round(final_loan_amount, 2),
            "products": products
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"计算贷款产品失败: {str(e)}"
        )
