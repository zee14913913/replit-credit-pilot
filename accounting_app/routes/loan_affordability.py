"""
Loan Affordability Routes

个人贷款承受能力API端点
提供客户可承受的最大贷款额度查询

⚠️ 债务来源：仅从 CTOS 报告获取（通过API参数传入）
⚠️ 不再从 monthly_statements 的信用卡字段推导

Author: AI Loan Evaluation System
Date: 2025-01-14
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Optional

from ..db import get_db
from ..services.loan_affordability_engine import LoanAffordabilityEngine


router = APIRouter(prefix="/api/loans", tags=["Loan Affordability"])


@router.get("/affordability/{customer_id}")
def get_loan_affordability(
    customer_id: int,
    current_monthly_debt: Optional[float] = Query(None, description="当前月度债务（从CTOS报告获取）"),
    company_id: int = Query(1, description="公司ID"),
    db: Session = Depends(get_db)
) -> Dict:
    """
    获取客户的个人贷款承受能力评估（基于CTOS commitment）
    
    基于 Phase A (收入系统) + CTOS债务数据 计算可承受的最大贷款额度
    
    Args:
        customer_id: 客户ID
        current_monthly_debt: 当前月度债务（从CTOS报告获取，必填）
        company_id: 公司ID（默认1）
        db: 数据库会话
        
    Returns:
        {
            "customer_id": int,
            "status": str,
            "recommended_dsr_limit": float,
            "max_monthly_payment_recommended": float,
            "max_monthly_payment_strict": float,
            "max_loan_amounts": {
                "12m": float,
                "24m": float,
                "36m": float,
                "60m": float,
                "84m": float
            },
            "income_source": str,
            "confidence": float,
            "dsr_income": float,
            "current_monthly_debt": float
        }
        
    Raises:
        HTTPException 404: 客户不存在或无收入数据
        HTTPException 500: 系统错误
    """
    try:
        result = LoanAffordabilityEngine.calculate_affordability(
            db=db,
            customer_id=customer_id,
            company_id=company_id,
            current_monthly_debt=current_monthly_debt
        )
        
        # 检查是否有错误
        if "error" in result:
            error_msg = result["error"]
            if error_msg == "missing_commitment_data":
                raise HTTPException(status_code=400, detail=result.get("message", "月度债务数据缺失，请上传CTOS报告"))
            elif "不存在" in error_msg:
                raise HTTPException(status_code=404, detail=f"客户不存在: customer_id={customer_id}")
            elif "无法获取客户收入数据" in error_msg:
                raise HTTPException(status_code=404, detail=f"客户无收入数据: customer_id={customer_id}")
            elif "收入无效" in error_msg:
                raise HTTPException(status_code=404, detail=f"客户收入无效: customer_id={customer_id}")
            else:
                raise HTTPException(status_code=500, detail=f"无法计算承受能力: {error_msg}")
        
        # 重新格式化响应结构（符合需求文档）
        affordability = result.get("affordability", {})
        
        response = {
            "customer_id": result["customer_id"],
            "status": "OK",
            "recommended_dsr_limit": result["recommended_dsr_limit"],
            "max_dsr_limit": result["max_dsr_limit"],
            "max_monthly_payment_recommended": result["max_monthly_payment_recommended"],
            "max_monthly_payment_strict": result["max_monthly_payment_strict"],
            "max_loan_amounts": {
                "12m": affordability.get("tenure_12", 0.0),
                "24m": affordability.get("tenure_24", 0.0),
                "36m": affordability.get("tenure_36", 0.0),
                "60m": affordability.get("tenure_60", 0.0),
                "84m": affordability.get("tenure_84", 0.0)
            },
            "income_source": result["income_source"],
            "confidence": result["confidence"],
            "dsr_income": result["dsr_income"],
            "dsrc_income": result.get("dsrc_income", 0.0),
            "current_monthly_debt": result["current_monthly_debt"]
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 承受能力计算错误: {e}")
        raise HTTPException(status_code=500, detail=f"系统错误: {str(e)}")
