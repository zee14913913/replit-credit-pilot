"""
Business Loans API Routes

提供企业贷款（SME Loan）评估功能，基于 DSCR 计算

⚠️ 收入来源：仅从 JournalEntry 会计账目获取
⚠️ 债务来源：仅从 CTOS 报告获取（通过API参数传入）
⚠️ 不再从 monthly_statements 的信用卡字段推导

Author: AI Loan Evaluation System
Date: 2025-01-14
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from accounting_app.db import get_db
from accounting_app.models import Customer
from accounting_app.services.business_loan_engine import BusinessLoanEngine


router = APIRouter(prefix="/api/business-loans", tags=["Business Loans"])


@router.get("/evaluate/{customer_id}")
def get_business_loan_eligibility(
    customer_id: int,
    annual_commitment: Optional[float] = Query(None, description="年度承诺还款（从CTOS报告获取）"),
    company_id: int = Query(1, description="公司ID"),
    mode: str = Query("dscr", description="引擎模式 (dscr=传统DSCR | modern=马来西亚SME标准)"),
    data_mode: str = Query("manual", description="数据模式 (manual=手动输入 | auto=自动采集)"),
    ctos_sme_score: Optional[int] = Query(None, description="CTOS SME分数 - manual模式需要"),
    cashflow_variance: Optional[float] = Query(None, description="现金流波动率 - manual模式需要"),
    industry_sector: Optional[str] = Query(None, description="行业分类 - manual模式需要"),
    company_age_years: Optional[int] = Query(None, description="公司年龄 - manual模式需要"),
    employee_count: Optional[int] = Query(None, description="员工数量 - manual模式需要"),
    target_bank: str = Query("maybank_sme", description="目标银行 - 仅modern模式"),
    db: Session = Depends(get_db)
):
    """
    获取企业贷款资格评估（基于DSCR + CTOS commitment）
    
    DSCR (Debt Service Coverage Ratio) = Operating Income / Annual Debt Service
    
    ⚠️ 收入：从 JournalEntry 会计账目获取
    ⚠️ 债务：从 CTOS 报告获取（API参数）
    
    功能：
    1. 从会计账目提取企业营业收入（operating_income）
    2. 使用CTOS报告的年度债务服务（annual_debt_service）
    3. 计算 DSCR 比率
    4. 判定资格状态（Eligible/Borderline/Not Eligible）
    5. 计算可承受债务额度和可借款能力
    
    分类规则：
    - DSCR ≥ 1.25 → Eligible
    - 1.00 ≤ DSCR < 1.25 → Borderline
    - DSCR < 1.00 → Not Eligible
    
    Args:
        customer_id: 客户ID
        annual_commitment: 年度承诺还款（从CTOS报告获取，必填）
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
        # Modern模式：使用新的马来西亚SME标准
        if mode == "modern":
            from accounting_app.services.risk_engine import SMELoanRules
            from accounting_app.services.loan_products import LoanProductMatcher
            from accounting_app.services.data_intake import AutoEnrichment
            
            # 获取营业收入
            operating_income = BusinessLoanEngine._get_operating_income(db, customer_id, company_id)
            
            if annual_commitment is None:
                raise HTTPException(status_code=400, detail="Debt commitment is required based on CTOS.")
            
            # Auto模式：自动填充缺失数据
            if data_mode == "auto":
                provided_data = {
                    "operating_income": operating_income,
                    "ctos_sme_score": ctos_sme_score,
                    "cashflow_variance": cashflow_variance,
                    "industry_sector": industry_sector,
                    "company_age_years": company_age_years,
                    "employee_count": employee_count
                }
                
                enriched_data = AutoEnrichment.enrich_sme_loan_data(
                    customer_id=customer_id,
                    db=db,
                    provided_data=provided_data
                )
                
                # 使用增强后的数据
                ctos_sme_score = enriched_data.get("ctos_sme_score", 650)
                cashflow_variance = enriched_data.get("cashflow_variance", 0.30)
                industry_sector = enriched_data.get("industry_sector", "trading")
                company_age_years = enriched_data.get("company_age_years", 5)
                employee_count = enriched_data.get("employee_count", 10)
                
                # 获取增强摘要
                enrichment_summary = AutoEnrichment.get_enrichment_summary(enriched_data)
            else:
                # Manual模式：使用默认值
                ctos_sme_score = ctos_sme_score if ctos_sme_score is not None else 650
                cashflow_variance = cashflow_variance if cashflow_variance is not None else 0.30
                industry_sector = industry_sector if industry_sector is not None else "trading"
                company_age_years = company_age_years if company_age_years is not None else 5
                employee_count = employee_count if employee_count is not None else 10
                enrichment_summary = None
            
            # 调用新风控引擎
            result = SMELoanRules.evaluate_sme_loan_eligibility(
                operating_income=operating_income,
                annual_commitment=annual_commitment,
                ctos_sme_score=ctos_sme_score,
                cashflow_variance=cashflow_variance,
                industry_sector=industry_sector,
                company_age_years=company_age_years,
                employee_count=employee_count,
                target_bank=target_bank
            )
            
            # 产品匹配
            recommended_products = LoanProductMatcher.match_sme_loan_products(
                brr_grade=result["brr_grade"],
                dscr=result["dscr"],
                industry_sector=industry_sector,
                max_loan_amount=result["max_loan_amount"],
                cgc_eligible=result["cgc_eligibility"]
            )
            
            result["recommended_products"] = recommended_products
            result["customer_id"] = customer_id
            result["mode"] = "modern"
            result["data_mode"] = data_mode
            result["engine"] = "Malaysian SME Standard (BRR/DSCR/DSR/Industry)"
            
            # 添加数据增强摘要
            if enrichment_summary:
                result["data_enrichment"] = enrichment_summary
            
            return result
        
        # DSCR模式：使用现有引擎（向后兼容）
        else:
            result = BusinessLoanEngine.calculate_dscr(
                db=db,
                customer_id=customer_id,
                company_id=company_id,
                annual_commitment=annual_commitment
            )
            
            if "error" in result:
                if result["error"] == "missing_commitment_data":
                    raise HTTPException(
                        status_code=400,
                        detail=result.get("message", "年度债务数据缺失，请上传CTOS报告")
                    )
                raise HTTPException(
                    status_code=404,
                    detail=result["error"]
                )
            
            result["mode"] = "dscr"
            result["engine"] = "Traditional DSCR"
            return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"计算企业贷款资格失败: {str(e)}"
        )
