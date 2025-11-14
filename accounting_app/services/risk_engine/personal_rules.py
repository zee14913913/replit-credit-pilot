"""
Personal Loan Rules - 个人贷款审批规则引擎
基于DTI/FOIR/CCRIS的马来西亚银行标准
"""
from typing import Dict, Optional
from .risk_tables import BANK_DTI_LIMITS, CCRIS_BUCKET_RISK, DIGITAL_BANK_RISK_BANDS
from .scoring_matrix import ScoringMatrix
from .risk_utils import RiskUtils


class PersonalLoanRules:
    """个人贷款审批规则引擎"""
    
    @classmethod
    def evaluate_loan_eligibility(
        cls,
        income: float,
        monthly_commitment: float,
        ccris_bucket: int = 0,
        age: int = 30,
        employment_years: float = 3.0,
        job_type: str = "permanent",
        credit_score: int = 700,
        target_bank: str = "maybank"
    ) -> Dict:
        """
        评估个人贷款资格（马来西亚银行标准）
        
        Args:
            income: 月收入
            monthly_commitment: 月度承诺还款（CTOS）
            ccris_bucket: CCRIS bucket (0~3+)
            age: 年龄
            employment_years: 工作年限
            job_type: permanent | contract | self_employed
            credit_score: 信用分数 (CTOS/CCRIS)
            target_bank: 目标银行代码
            
        Returns:
            {
                "risk_grade": str,
                "final_dti": float,
                "max_emi": float,
                "max_loan_amount": float,
                "approval_odds": float,
                "bank_specific": Dict,
                "digital_bank_band": Dict
            }
        """
        # 1. 计算DTI
        dti = monthly_commitment / income if income > 0 else 0.0
        
        # 2. 获取银行限制
        bank_limits = BANK_DTI_LIMITS.get(target_bank, BANK_DTI_LIMITS["maybank"])
        max_dti_limit = bank_limits.get("max_dti") or bank_limits.get("max_foir", 0.60)
        min_income_required = bank_limits.get("min_income", 2000)
        
        # 3. CCRIS风险调整
        ccris_risk = CCRIS_BUCKET_RISK.get(f"{ccris_bucket}_bucket", CCRIS_BUCKET_RISK["1_bucket"])
        dti_adjustment = ccris_risk["dti_adjustment"]
        adjusted_max_dti = max_dti_limit + dti_adjustment
        
        # 4. 年龄风险因子
        age_risk = RiskUtils.calculate_age_risk_factor(age)
        
        # 5. 就业稳定性
        employment_stability = RiskUtils.calculate_employment_stability(
            employment_years, job_type
        )
        employment_stability_score = max(0, 100 - (employment_stability["risk_adjustment"] * 100))
        
        # 6. 数字银行风险分级
        digital_band = RiskUtils.calculate_digital_bank_risk_band(
            credit_score, income, monthly_commitment
        )
        
        # 7. 计算风险等级
        risk_grading = ScoringMatrix.calculate_personal_loan_grade(
            dti=dti,
            ccris_bucket=ccris_bucket,
            income=income,
            employment_stability_score=employment_stability_score,
            age_risk_multiplier=age_risk["risk_multiplier"]
        )
        
        # 8. 计算最大EMI能力
        max_emi = (income * adjusted_max_dti) - monthly_commitment
        max_emi = max(0, max_emi)
        
        # 应用数字银行multiplier
        if bank_limits.get("risk_band_based"):
            max_emi = max_emi * digital_band["max_emi_multiplier"]
        
        # 9. 反推最大贷款额（假设5年期，6.5%利率）
        annual_rate = (bank_limits["interest_rate_range"][0] + bank_limits["interest_rate_range"][1]) / 2
        tenure_months = min(60, age_risk["max_tenure"])
        max_loan_amount = cls._calculate_max_loan_from_emi(
            max_emi, annual_rate, tenure_months
        )
        
        # 10. 审批概率
        approval_odds = ScoringMatrix.calculate_approval_odds(
            risk_score=risk_grading["risk_score"],
            income=income,
            min_income_required=min_income_required,
            max_dti=adjusted_max_dti,
            actual_dti=dti
        )
        
        # 11. 资格判定
        if income < min_income_required:
            eligibility_status = "Rejected - Insufficient Income"
            approval_odds = 0.0
        elif dti > adjusted_max_dti:
            eligibility_status = "Rejected - DTI Exceeded"
            approval_odds = min(30.0, approval_odds)
        elif ccris_bucket >= 3:
            eligibility_status = "High Risk - Manual Review Required"
            approval_odds = min(40.0, approval_odds)
        elif approval_odds >= 70:
            eligibility_status = "Approved"
        elif approval_odds >= 50:
            eligibility_status = "Borderline - Additional Documents Required"
        else:
            eligibility_status = "Rejected - High Risk"
        
        return {
            "eligibility_status": eligibility_status,
            "risk_grade": risk_grading["risk_grade"],
            "risk_score": risk_grading["risk_score"],
            "final_dti": round(dti, 4),
            "adjusted_max_dti": round(adjusted_max_dti, 4),
            "max_emi": round(max_emi, 2),
            "max_loan_amount": round(max_loan_amount, 2),
            "max_tenure_months": tenure_months,
            "approval_odds": approval_odds,
            "approval_probability": approval_odds / 100,
            
            # 详细信息
            "bank_specific": {
                "bank_name": bank_limits["name"],
                "base_dti_limit": max_dti_limit,
                "min_income": min_income_required,
                "interest_rate_range": bank_limits["interest_rate_range"]
            },
            "ccris_info": {
                "bucket": ccris_bucket,
                "risk_level": ccris_risk["risk_level"],
                "dti_adjustment": dti_adjustment
            },
            "age_info": {
                "age": age,
                "age_band": age_risk["age_band"],
                "risk_multiplier": age_risk["risk_multiplier"]
            },
            "employment_info": {
                "years": employment_years,
                "job_type": job_type,
                "stability_grade": employment_stability["stability_grade"]
            },
            "digital_bank_band": digital_band,
            "scoring_breakdown": risk_grading["scoring_breakdown"]
        }
    
    @staticmethod
    def _calculate_max_loan_from_emi(
        monthly_emi: float,
        annual_rate: float,
        tenure_months: int
    ) -> float:
        """
        从EMI反推最大贷款金额
        
        公式：PV = EMI * [(1 - (1 + r)^-n) / r]
        """
        if monthly_emi <= 0 or annual_rate <= 0 or tenure_months <= 0:
            return 0.0
        
        monthly_rate = annual_rate / 12
        
        if monthly_rate == 0:
            return monthly_emi * tenure_months
        
        pv = monthly_emi * ((1 - (1 + monthly_rate) ** -tenure_months) / monthly_rate)
        return pv


# ============================================================================
# PHASE 8.1: QUICK ESTIMATE FUNCTIONS (Client-Side快速评估)
# ============================================================================

def estimate_risk_income_only(income: float) -> dict:
    """
    Quick Estimate - Income Only
    基于月收入快速估算贷款资格（无需CTOS数据）
    """
    if not income or income <= 0:
        return {"error": "Invalid income"}

    # 简易默认参数
    commitments = 0
    dti = commitments / income
    foir = dti

    # 风险等级估算（基于收入区间）
    if income >= 8000:
        grade = "A"
        odds = 92
    elif income >= 5000:
        grade = "B+"
        odds = 82
    elif income >= 3000:
        grade = "B"
        odds = 68
    else:
        grade = "C"
        odds = 45

    # EMI计算：保守使用35%收入作为EMI capacity
    max_emi = income * 0.35
    # 假设7年期限（84个月）
    max_loan = max_emi * 50  # 简化计算

    return {
        "mode": "quick_income_only",
        "income": income,
        "dti": round(dti, 3),
        "foir": round(foir, 3),
        "risk_grade": grade,
        "approval_odds": odds,
        "max_emi": round(max_emi, 2),
        "max_loan_amount": round(max_loan, 2),
        "recommended_products": []
    }


def estimate_risk_income_commitments(income: float, commitments: float) -> dict:
    """
    Quick Estimate - Income + Commitments
    基于月收入和现有债务快速估算贷款资格
    """
    if not income or income <= 0:
        return {"error": "Invalid income"}

    if commitments < 0:
        return {"error": "Invalid commitments"}

    # 计算DTI
    dti = commitments / income
    foir = dti  # 简化：FOIR = DTI

    # 风险等级估计（基于DTI区间）
    if dti <= 0.25:
        grade = "A"
        odds = 90
    elif dti <= 0.40:
        grade = "B+"
        odds = 75
    elif dti <= 0.55:
        grade = "B"
        odds = 60
    else:
        grade = "C"
        odds = 35

    # 计算剩余EMI capacity
    # 保守策略：允许最高DTI 60%
    max_emi = income * (0.6 - dti)
    if max_emi < 0:
        max_emi = 0

    # 假设7年期限
    max_loan = max_emi * 50  # 简化计算

    return {
        "mode": "quick_income_commitment",
        "income": income,
        "commitments": commitments,
        "dti": round(dti, 3),
        "foir": round(foir, 3),
        "risk_grade": grade,
        "approval_odds": odds,
        "max_emi": round(max_emi, 2),
        "max_loan_amount": round(max_loan, 2),
        "recommended_products": []
    }

