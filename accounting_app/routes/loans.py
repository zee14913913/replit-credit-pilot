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
    mode: str = "dsr",
    data_mode: str = "manual",
    ccris_bucket: Optional[int] = None,
    age: Optional[int] = None,
    employment_years: Optional[float] = None,
    credit_score: Optional[int] = None,
    target_bank: str = "maybank",
    db: Session = Depends(get_db)
):
    """
    获取客户贷款资格评估（双引擎模式 + 自动数据采集）
    
    Args:
        customer_id: 客户ID
        monthly_commitment: 月度承诺还款（从CTOS报告获取，必填）
        company_id: 公司ID（默认1）
        mode: 引擎模式 (dsr=传统DSR模式 | modern=马来西亚银行DTI/FOIR模式)
        data_mode: 数据模式 (manual=手动输入 | auto=自动采集)
        ccris_bucket: CCRIS bucket (0~3+) - manual模式需要
        age: 年龄 - manual模式需要
        employment_years: 工作年限 - manual模式需要
        credit_score: 信用分数 - manual模式需要
        target_bank: 目标银行 - 仅modern模式
        
    Returns:
        DSR模式: 传统输出格式
        Modern模式: 马来西亚银行标准格式（DTI/FOIR/Risk Grade/Product Matching）
        Auto模式: 自动填充缺失数据后再评估
        
    Raises:
        HTTPException 400: monthly_commitment缺失
    """
    try:
        # Modern模式：使用新的马来西亚银行标准
        if mode == "modern":
            from ..services.risk_engine import PersonalLoanRules
            from ..services.loan_products import LoanProductMatcher
            from ..services.data_intake import AutoEnrichment
            
            # 获取收入数据
            income_data = IncomeService.get_customer_income(db, customer_id, company_id)
            if not income_data:
                raise HTTPException(status_code=404, detail="客户无收入数据")
            
            income = income_data.get("dsr_income", 0.0)
            
            if monthly_commitment is None:
                raise HTTPException(status_code=400, detail="Debt commitment is required based on CTOS.")
            
            # Auto模式：自动填充缺失数据
            if data_mode == "auto":
                provided_data = {
                    "income": income,
                    "ccris_bucket": ccris_bucket,
                    "age": age,
                    "employment_years": employment_years,
                    "credit_score": credit_score
                }
                
                enriched_data = AutoEnrichment.enrich_personal_loan_data(
                    customer_id=customer_id,
                    db=db,
                    provided_data=provided_data
                )
                
                # 使用增强后的数据
                ccris_bucket = enriched_data.get("ccris_bucket", 0)
                age = enriched_data.get("age", 30)
                employment_years = enriched_data.get("employment_years", 3.0)
                credit_score = enriched_data.get("credit_score", 700)
                
                # 获取增强摘要
                enrichment_summary = AutoEnrichment.get_enrichment_summary(enriched_data)
            else:
                # Manual模式：使用默认值
                ccris_bucket = ccris_bucket if ccris_bucket is not None else 0
                age = age if age is not None else 30
                employment_years = employment_years if employment_years is not None else 3.0
                credit_score = credit_score if credit_score is not None else 700
                enrichment_summary = None
            
            # 调用新风控引擎
            result = PersonalLoanRules.evaluate_loan_eligibility(
                income=income,
                monthly_commitment=monthly_commitment,
                ccris_bucket=ccris_bucket,
                age=age,
                employment_years=employment_years,
                job_type="permanent",
                credit_score=credit_score,
                target_bank=target_bank
            )
            
            # 产品匹配
            recommended_products = LoanProductMatcher.match_personal_loan_products(
                risk_grade=result["risk_grade"],
                income=income,
                max_emi=result["max_emi"],
                digital_bank_band=result["digital_bank_band"]["risk_band"]
            )
            
            result["recommended_products"] = recommended_products
            result["customer_id"] = customer_id
            result["mode"] = "modern"
            result["data_mode"] = data_mode
            result["engine"] = "Malaysian Banking Standard (DTI/FOIR/CCRIS)"
            
            # 添加数据增强摘要
            if enrichment_summary:
                result["data_enrichment"] = enrichment_summary
            
            return result
        
        # DSR模式：使用现有引擎（向后兼容）
        else:
            result = calculate_loan_eligibility(
                db=db,
                customer_id=customer_id,
                monthly_commitment=monthly_commitment,
                company_id=company_id
            )
            result["mode"] = "dsr"
            result["engine"] = "Traditional DSR"
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
