"""
Loans - 贷款资格评估模块
集成标准化收入数据进行DSR/DSRC计算

⚠️ 债务来源：仅从 CTOS 报告获取（通过API参数传入）
⚠️ 不再从 monthly_statements 的信用卡字段推导
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..db import get_db
from ..services.income_service import IncomeService
from ..models import Customer

router = APIRouter(prefix="/api/loans", tags=["Loans"])


def calculate_loan_eligibility(
    db: Session,
    customer_id: int,
    monthly_commitment: Optional[float] = None,
    company_id: int = 1
) -> dict:
    """
    计算客户贷款资格（基于DSR规则 + CTOS commitment）
    
    Args:
        db: 数据库会话
        customer_id: 客户ID
        monthly_commitment: 月度承诺还款（从CTOS报告获取，必填）
        company_id: 公司ID
        
    Returns:
        包含DSR资格评估的字典
        
    DSR (Debt Service Ratio) 规则:
        DSR = monthly_debt / dsr_income
        - DSR ≤ 0.6 → Eligible（符合资格）
        - 0.6 < DSR ≤ 0.8 → Borderline（边缘资格）
        - DSR > 0.8 → Not Eligible（不符合资格）
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户ID {customer_id} 不存在")
    
    try:
        income_data = IncomeService.get_customer_income(db, customer_id, company_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取收入数据失败: {str(e)}"
        )
    
    if not income_data:
        raise HTTPException(
            status_code=404,
            detail=f"客户ID {customer_id} 未找到收入数据，请先上传收入证明文件（salary_slip/tax_return/epf/bank_inflow）"
        )
    
    dsr_income = income_data.get("dsr_income", 0.0)
    dsrc_income = income_data.get("dsrc_income", 0.0)
    
    if dsr_income <= 0:
        raise HTTPException(
            status_code=400,
            detail="收入数据无效，DSR收入必须大于0。请检查上传的收入文件是否正确。"
        )
    
    # ⚠️ 债务数据必须从CTOS报告获取
    if monthly_commitment is None:
        raise HTTPException(
            status_code=400,
            detail="Debt commitment is required based on CTOS."
        )
    
    dsr_ratio = monthly_commitment / dsr_income if dsr_income > 0 else 0.0
    
    if dsr_ratio <= 0.6:
        status = "Eligible"
        status_cn = "符合资格"
        dsr_limit_used = 0.6
    elif dsr_ratio <= 0.8:
        status = "Borderline"
        status_cn = "边缘资格"
        dsr_limit_used = 0.8
    else:
        status = "Not Eligible"
        status_cn = "不符合资格"
        dsr_limit_used = 0.8
    
    suggested_loan_amount = dsr_income * 8
    
    max_monthly_commitment_at_60 = dsr_income * 0.6
    available_capacity = max(0, max_monthly_commitment_at_60 - monthly_commitment)
    
    return {
        "customer_id": customer_id,
        "customer_name": customer.name,
        "income": round(dsr_income, 2),
        "commitment": round(monthly_commitment, 2),
        "dsr_ratio": round(dsr_ratio, 4),
        "eligibility": status,
        "threshold": dsr_limit_used,
        "threshold_type": "Standard",
        "data_source": income_data.get("best_source"),
        "available_capacity": round(available_capacity, 2),
        "status_cn": status_cn,
        "source": income_data.get("best_source"),
        "confidence": round(income_data.get("confidence", 0.0), 4),
        "suggested_loan_amount": round(suggested_loan_amount, 2),
        "income_timestamp": income_data.get("timestamp"),
        "components": income_data.get("components", [])
    }


@router.get("/eligibility/{customer_id}")
async def get_loan_eligibility(
    customer_id: int,
    monthly_commitment: Optional[float] = None,
    company_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    获取客户贷款资格评估（基于CTOS commitment）
    
    Args:
        customer_id: 客户ID
        monthly_commitment: 月度承诺还款（从CTOS报告获取，必填）
        company_id: 公司ID（默认1）
        
    Returns:
        包含以下信息的JSON:
        - customer_id: 客户ID
        - dsr_income: DSR计算用收入
        - total_debt: 月度债务
        - dsr_ratio: DSR比率
        - status: Eligible / Borderline / Not Eligible
        - source: 收入来源类型
        - confidence: 置信度
        - suggested_loan_amount: 建议贷款额度（= dsr_income × 8）
        - max_monthly_debt: 最大可承受月度债务
        - available_borrowing_capacity: 可用借款能力
        
    Raises:
        HTTPException 400: monthly_commitment缺失
    """
    try:
        result = calculate_loan_eligibility(
            db=db,
            customer_id=customer_id,
            monthly_commitment=monthly_commitment,
            company_id=company_id
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"计算贷款资格失败: {str(e)}"
        )


@router.get("/dsr-analysis/{customer_id}")
async def get_dsr_analysis(
    customer_id: int,
    company_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    获取客户的DSR详细分析
    包含不同债务水平下的资格状态
    
    Args:
        customer_id: 客户ID
        company_id: 公司ID
        
    Returns:
        DSR分析报告
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户ID {customer_id} 不存在")
    
    income_data = IncomeService.get_customer_income(db, customer_id, company_id)
    
    if not income_data:
        raise HTTPException(
            status_code=404,
            detail=f"客户ID {customer_id} 未找到收入数据"
        )
    
    dsr_income = income_data.get("dsr_income", 0.0)
    
    scenarios = []
    for dsr_target in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        max_debt = dsr_income * dsr_target
        scenarios.append({
            "dsr_ratio": dsr_target,
            "max_monthly_debt": round(max_debt, 2),
            "status": "Eligible" if dsr_target <= 0.6 else ("Borderline" if dsr_target <= 0.8 else "Not Eligible")
        })
    
    return {
        "customer_id": customer_id,
        "customer_name": customer.name,
        "dsr_income": round(dsr_income, 2),
        "source": income_data.get("best_source"),
        "confidence": income_data.get("confidence", 0.0),
        "scenarios": scenarios,
        "recommended_max_debt": round(dsr_income * 0.6, 2)
    }
