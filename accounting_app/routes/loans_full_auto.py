"""
Phase 8.3: Full Automated Loan Evaluation
文件上传 → 数据自动解析 → 风控分析 → 推荐产品 → AI解释
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import io

from accounting_app.services.data_intake.auto_enrichment import AutoEnrichment
from accounting_app.services.risk_engine.personal_rules import (
    PersonalLoanRules,
    personal_risk_grade_explainer
)
from accounting_app.services.loan_products import LoanProductMatcher

router = APIRouter()


@router.post("/api/loans/full-auto")
async def full_auto_evaluation(
    payslip_pdf: Optional[UploadFile] = File(None),
    epf_pdf: Optional[UploadFile] = File(None),
    bank_statement_pdf: Optional[UploadFile] = File(None),
    ctos_pdf: Optional[UploadFile] = File(None),
    ccris_pdf: Optional[UploadFile] = File(None)
):
    """
    Full Automated Mode - 自动解析上传文件并生成贷款评估
    
    流程：
    1. 文件验证和读取
    2. AutoEnrichment自动数据提取
    3. 风险引擎评估
    4. 产品匹配
    5. AI顾问生成
    """
    
    # 验证至少上传一个文件
    uploaded_files = [payslip_pdf, epf_pdf, bank_statement_pdf, ctos_pdf, ccris_pdf]
    if not any(f for f in uploaded_files):
        raise HTTPException(
            status_code=400,
            detail="Please upload at least one document (Payslip / EPF / Bank Statement / CTOS / CCRIS)"
        )
    
    try:
        # ============================================================
        # STEP 1: 读取上传的文件内容
        # ============================================================
        file_contents = {}
        
        if payslip_pdf:
            file_contents['payslip'] = await payslip_pdf.read()
        
        if epf_pdf:
            file_contents['epf'] = await epf_pdf.read()
        
        if bank_statement_pdf:
            file_contents['bank_statement'] = await bank_statement_pdf.read()
        
        if ctos_pdf:
            file_contents['ctos'] = await ctos_pdf.read()
        
        if ccris_pdf:
            file_contents['ccris'] = await ccris_pdf.read()
        
        # ============================================================
        # STEP 2: AutoEnrichment - 自动数据提取
        # ============================================================
        enriched_data = AutoEnrichment.extract_from_documents(file_contents)
        
        # 提取关键财务指标
        monthly_income = enriched_data.get('monthly_income', 0)
        monthly_commitments = enriched_data.get('monthly_commitments', 0)
        employment_status = enriched_data.get('employment_status', 'Unknown')
        employment_tenure_months = enriched_data.get('employment_tenure_months', 0)
        credit_score = enriched_data.get('credit_score', 700)  # 默认中等信用
        ccris_bucket = enriched_data.get('ccris_bucket', 0)
        
        # ============================================================
        # STEP 3: 风险引擎评估 - PersonalLoanRules
        # ============================================================
        eligibility_result = PersonalLoanRules.evaluate_loan_eligibility(
            monthly_income=monthly_income,
            monthly_commitment=monthly_commitments,
            credit_score=credit_score,
            ccris_bucket=ccris_bucket,
            employment_status=employment_status,
            employment_tenure_months=employment_tenure_months,
            requested_loan_amount=monthly_income * 30,  # 默认请求30倍月薪
            loan_tenure_months=84,  # 7年期
            mode="modern"  # 使用Modern引擎（DTI/FOIR/CCRIS标准）
        )
        
        # 提取评估结果关键字段
        risk_grade = eligibility_result.get('risk_grade', 'B')
        final_dti = eligibility_result.get('final_dti', 0)
        foir = eligibility_result.get('foir', 0)
        max_emi = eligibility_result.get('max_emi_calculated', 0)
        max_loan = eligibility_result.get('max_loan_amount_calculated', 0)
        approval_odds = eligibility_result.get('approval_odds', 60)
        
        # ============================================================
        # STEP 4: 产品匹配 - LoanProductMatcher
        # ============================================================
        recommended_products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade=risk_grade,
            income=monthly_income,
            monthly_commitment=monthly_commitments,
            ccris_bucket=ccris_bucket,
            credit_score=credit_score,
            max_loan_amount=max_loan,
            top_n=10
        )
        
        # ============================================================
        # STEP 5: AI Advisor - personal_risk_grade_explainer
        # ============================================================
        ai_explanation = personal_risk_grade_explainer(
            risk_grade=risk_grade,
            dti=final_dti,
            income=monthly_income,
            commitments=monthly_commitments
        )
        
        # ============================================================
        # STEP 6: 组装最终响应（与Phase 8.2字段命名一致）
        # ============================================================
        return {
            "mode": "full_auto",
            "eligibility": {
                "risk_grade": risk_grade,
                "dti": final_dti,
                "foir": foir,
                "max_emi": max_emi,
                "max_loan_amount": max_loan,
                "approval_odds": approval_odds,
                "credit_score": credit_score,
                "ccris_bucket": ccris_bucket,
                "employment_status": employment_status,
                "monthly_income": monthly_income,
                "monthly_commitments": monthly_commitments
            },
            "products": recommended_products,
            "advisor": ai_explanation,
            "enriched_data": enriched_data  # 调试用，可选返回
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Full Auto evaluation failed: {str(e)}"
        )
