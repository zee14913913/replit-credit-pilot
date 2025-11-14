"""
Loan Reports API Routes - 贷款报告生成API
PHASE 5: 提供HTML/PDF贷款报告下载端点
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from typing import Literal, Optional
from fastapi import Depends

from ..db import get_db
from ..services.reporting import LoanReportBuilder
from ..services.reporting.pdf_renderer import (
    generate_personal_pdf,
    generate_sme_pdf
)
from ..services.risk_engine.personal_rules import PersonalLoanRules
from ..services.risk_engine.sme_rules import SMELoanRules
from ..services.data_intake.auto_enrichment import AutoEnrichment
from ..services.loan_products import LoanProductMatcher

router = APIRouter(prefix="/api/loan-reports", tags=["Loan Reports"])


@router.get("/personal/{customer_id}")
async def generate_personal_loan_report(
    customer_id: int,
    mode: str = Query("modern", description="评估模式: dsr或modern"),
    data_mode: str = Query("manual", description="数据模式: manual或auto"),
    format: Literal["html", "pdf"] = Query("html", description="输出格式"),
    monthly_commitment: float = Query(..., description="月度债务承诺"),
    income: Optional[float] = Query(None, description="月收入"),
    ccris_bucket: Optional[int] = Query(None, description="CCRIS bucket"),
    credit_score: Optional[int] = Query(None, description="信用分数"),
    age: Optional[int] = Query(None, description="年龄"),
    employment_years: Optional[float] = Query(None, description="就业年限"),
    target_bank: Optional[str] = Query(None, description="目标银行"),
    db: Session = Depends(get_db)
):
    """
    生成个人贷款评估报告
    
    支持HTML和PDF两种格式
    """
    try:
        # 只支持Modern模式
        if mode != "modern":
            raise HTTPException(
                status_code=400,
                detail="报告生成仅支持modern模式"
            )
        
        # 获取客户数据（简化版，实际应从数据库查询）
        customer_data = {
            "customer_id": customer_id,
            "name": f"Customer #{customer_id}",
            "ic_number": "N/A",
            "income": income or 5000,
            "age": age or 30,
            "employment_status": "Permanent",
            "employment_years": employment_years or 3.0
        }
        
        # 数据增强（如果启用）
        enriched_data = None
        if data_mode == "auto":
            enriched_data = AutoEnrichment.enrich_personal_loan_data(
                income=income or customer_data["income"],
                monthly_commitment=monthly_commitment,
                ccris_bucket=ccris_bucket,
                age=age,
                employment_years=employment_years,
                credit_score=credit_score
            )
            
            # 使用增强后的数据
            ccris_bucket = enriched_data.get("ccris_bucket", 0)
            age = enriched_data.get("age", 30)
            employment_years = enriched_data.get("employment_years", 3.0)
            credit_score = enriched_data.get("credit_score", 700)
        else:
            ccris_bucket = ccris_bucket if ccris_bucket is not None else 0
            age = age if age is not None else 30
            employment_years = employment_years if employment_years is not None else 3.0
            credit_score = credit_score if credit_score is not None else 700
        
        # 调用Modern风控评估
        evaluation_result = PersonalLoanRules.evaluate_loan_eligibility(
            income=income or customer_data["income"],
            monthly_commitment=monthly_commitment,
            ccris_bucket=ccris_bucket,
            age=age,
            employment_years=employment_years,
            job_type="permanent",
            credit_score=credit_score,
            target_bank=target_bank
        )
        
        # 产品匹配（传递target_bank参数）
        recommended_products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade=evaluation_result["risk_grade"],
            income=income or customer_data["income"],
            monthly_commitment=monthly_commitment,
            ccris_bucket=ccris_bucket,
            credit_score=credit_score,
            max_emi=evaluation_result["max_emi"],
            top_n=10,
            target_bank=target_bank
        )
        
        evaluation_result["recommended_products"] = recommended_products
        evaluation_result["monthly_commitment"] = monthly_commitment
        
        # 生成报告
        if format == "html":
            html_content = LoanReportBuilder.build_personal_report(
                evaluation_result=evaluation_result,
                customer_data=customer_data,
                enriched_data=enriched_data if data_mode == "auto" else None
            )
            
            return HTMLResponse(content=html_content)
        
        else:  # PDF
            pdf_bytes = generate_personal_pdf(
                evaluation_result=evaluation_result,
                customer_data=customer_data,
                enriched_data=enriched_data if data_mode == "auto" else None
            )
            
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=personal_loan_report_{customer_id}.pdf"
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成报告失败: {str(e)}"
        )


@router.get("/sme/{customer_id}")
async def generate_sme_loan_report(
    customer_id: int,
    mode: str = Query("modern", description="评估模式: dscr或modern"),
    data_mode: str = Query("manual", description="数据模式: manual或auto"),
    format: Literal["html", "pdf"] = Query("html", description="输出格式"),
    annual_commitment: float = Query(..., description="年度债务承诺"),
    operating_income: Optional[float] = Query(None, description="年度营业收入"),
    industry_sector: Optional[str] = Query(None, description="行业分类"),
    ctos_sme_score: Optional[int] = Query(None, description="CTOS SME分数"),
    company_age_years: Optional[int] = Query(None, description="公司年龄"),
    employee_count: Optional[int] = Query(None, description="员工人数"),
    target_bank: Optional[str] = Query(None, description="目标银行"),
    db: Session = Depends(get_db)
):
    """
    生成SME贷款评估报告
    
    支持HTML和PDF两种格式
    """
    try:
        # 只支持Modern模式
        if mode != "modern":
            raise HTTPException(
                status_code=400,
                detail="报告生成仅支持modern模式"
            )
        
        # 获取企业数据（简化版）
        customer_data = {
            "customer_id": customer_id,
            "company_name": f"Company #{customer_id}",
            "registration_number": "N/A",
            "operating_income": operating_income or 1000000,
            "industry_sector": industry_sector or "services",
            "company_age_years": company_age_years or 5,
            "employee_count": employee_count or 10
        }
        
        # 数据增强（如果启用）
        enriched_data = None
        if data_mode == "auto":
            enriched_data = AutoEnrichment.enrich_sme_loan_data(
                operating_income=operating_income or customer_data["operating_income"],
                annual_commitment=annual_commitment,
                ctos_sme_score=ctos_sme_score,
                cashflow_variance=None,
                industry_sector=industry_sector,
                company_age_years=company_age_years
            )
            
            # 使用增强后的数据
            ctos_sme_score = enriched_data.get("ctos_sme_score", 650)
            cashflow_variance = enriched_data.get("cashflow_variance", 0.30)
            industry_sector = enriched_data.get("industry_sector", "services")
            company_age_years = enriched_data.get("company_age_years", 5)
        else:
            ctos_sme_score = ctos_sme_score if ctos_sme_score is not None else 650
            cashflow_variance = 0.30
            industry_sector = industry_sector or "services"
            company_age_years = company_age_years if company_age_years is not None else 5
        
        # 调用Modern风控评估
        evaluation_result = SMELoanRules.evaluate_sme_loan_eligibility(
            operating_income=operating_income or customer_data["operating_income"],
            annual_commitment=annual_commitment,
            ctos_sme_score=ctos_sme_score,
            cashflow_variance=cashflow_variance,
            industry_sector=industry_sector,
            company_age_years=company_age_years,
            employee_count=employee_count or 10,
            target_bank=target_bank
        )
        
        # 产品匹配（传递target_bank参数）
        recommended_products = LoanProductMatcher.match_sme_loan_v2(
            brr_grade=evaluation_result["brr_grade"],
            dscr=evaluation_result["dscr"],
            operating_income=operating_income or customer_data["operating_income"],
            industry_sector=industry_sector,
            ctos_sme_score=ctos_sme_score,
            company_age_years=company_age_years,
            max_loan_amount=evaluation_result["max_loan_amount"],
            cgc_eligible=evaluation_result["cgc_eligibility"],
            top_n=10,
            target_bank=target_bank
        )
        
        evaluation_result["recommended_products"] = recommended_products
        evaluation_result["annual_commitment"] = annual_commitment
        
        # 生成报告
        if format == "html":
            html_content = LoanReportBuilder.build_sme_report(
                evaluation_result=evaluation_result,
                customer_data=customer_data,
                enriched_data=enriched_data if data_mode == "auto" else None
            )
            
            return HTMLResponse(content=html_content)
        
        else:  # PDF
            pdf_bytes = generate_sme_pdf(
                evaluation_result=evaluation_result,
                customer_data=customer_data,
                enriched_data=enriched_data if data_mode == "auto" else None
            )
            
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=sme_loan_report_{customer_id}.pdf"
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成报告失败: {str(e)}"
        )
