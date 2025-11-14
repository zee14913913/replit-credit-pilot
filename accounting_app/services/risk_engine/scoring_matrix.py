"""
Scoring Matrix - 风险评分矩阵
综合评分系统用于个人贷款和SME贷款审批
"""
from typing import Dict, Optional


class ScoringMatrix:
    """风险评分矩阵引擎"""
    
    # =================================================================
    # PERSONAL LOAN RISK GRADING
    # =================================================================
    
    @staticmethod
    def calculate_personal_loan_grade(
        dti: float,
        ccris_bucket: int,
        income: float,
        employment_stability_score: float,
        age_risk_multiplier: float
    ) -> Dict:
        """
        个人贷款风险等级计算
        
        Args:
            dti: Debt-to-Income Ratio
            ccris_bucket: CCRIS bucket (0~3+)
            income: 月收入
            employment_stability_score: 就业稳定性分数 (0~100)
            age_risk_multiplier: 年龄风险倍数 (1.0~2.0)
            
        Returns:
            {
                "risk_grade": str,  # A+ | A | B+ | B | C | D
                "risk_score": int,  # 1~100
                "approval_probability": float  # 0~1
            }
        """
        # 基础分数 (100分制)
        base_score = 100
        
        # DTI扣分 (最多-40分)
        if dti <= 0.30:
            dti_penalty = 0
        elif dti <= 0.40:
            dti_penalty = 10
        elif dti <= 0.50:
            dti_penalty = 20
        elif dti <= 0.60:
            dti_penalty = 30
        else:
            dti_penalty = 40
        
        # CCRIS扣分 (最多-30分)
        ccris_penalty_map = {0: 0, 1: 10, 2: 20, 3: 30}
        ccris_penalty = ccris_penalty_map.get(ccris_bucket, 30)
        
        # 收入扣分 (最多-15分)
        if income >= 5000:
            income_penalty = 0
        elif income >= 3000:
            income_penalty = 5
        elif income >= 2000:
            income_penalty = 10
        else:
            income_penalty = 15
        
        # 就业稳定性扣分 (最多-10分)
        employment_penalty = max(0, 10 - (employment_stability_score / 10))
        
        # 年龄扣分 (最多-5分)
        age_penalty = (age_risk_multiplier - 1.0) * 5
        
        # 计算最终分数
        final_score = base_score - dti_penalty - ccris_penalty - income_penalty - employment_penalty - age_penalty
        final_score = max(0, min(100, final_score))
        
        # 分级
        if final_score >= 90:
            risk_grade = "A+"
            approval_probability = 0.95
        elif final_score >= 80:
            risk_grade = "A"
            approval_probability = 0.90
        elif final_score >= 70:
            risk_grade = "B+"
            approval_probability = 0.80
        elif final_score >= 60:
            risk_grade = "B"
            approval_probability = 0.70
        elif final_score >= 50:
            risk_grade = "C"
            approval_probability = 0.50
        else:
            risk_grade = "D"
            approval_probability = 0.30
        
        return {
            "risk_grade": risk_grade,
            "risk_score": int(final_score),
            "approval_probability": approval_probability,
            "scoring_breakdown": {
                "base_score": 100,
                "dti_penalty": -dti_penalty,
                "ccris_penalty": -ccris_penalty,
                "income_penalty": -income_penalty,
                "employment_penalty": -employment_penalty,
                "age_penalty": -age_penalty
            }
        }
    
    # =================================================================
    # SME LOAN BRR (Borrower Risk Rating) CALCULATION
    # =================================================================
    
    @staticmethod
    def calculate_brr_grade(
        dscr: float,
        dsr: float,
        ctos_sme_score: int,
        cashflow_variance: float,
        industry_risk_score: int,
        company_age_years: int
    ) -> Dict:
        """
        SME借款人风险评级 (BRR)
        
        Args:
            dscr: Debt Service Coverage Ratio
            dsr: Debt Service Ratio (cashflow-based)
            ctos_sme_score: CTOS SME分数 (0~999)
            cashflow_variance: 现金流波动率 (0~1)
            industry_risk_score: 行业风险分数 (1~10)
            company_age_years: 公司年龄
            
        Returns:
            {
                "brr_grade": int,  # 1~10 (1=最佳, 10=最差)
                "risk_category": str,  # Excellent | Good | Fair | Poor | High Risk
                "approval_probability": float
            }
        """
        # 基础分数 (100分制，然后映射到1~10)
        base_score = 100
        
        # DSCR扣分 (最多-25分)
        if dscr >= 2.0:
            dscr_penalty = 0
        elif dscr >= 1.50:
            dscr_penalty = 5
        elif dscr >= 1.25:
            dscr_penalty = 10
        elif dscr >= 1.00:
            dscr_penalty = 20
        else:
            dscr_penalty = 25
        
        # DSR扣分 (最多-20分)
        if dsr >= 1.50:
            dsr_penalty = 0
        elif dsr >= 1.20:
            dsr_penalty = 5
        elif dsr >= 1.00:
            dsr_penalty = 15
        else:
            dsr_penalty = 20
        
        # CTOS SME Score扣分 (最多-25分)
        if ctos_sme_score >= 750:
            ctos_penalty = 0
        elif ctos_sme_score >= 650:
            ctos_penalty = 5
        elif ctos_sme_score >= 550:
            ctos_penalty = 15
        elif ctos_sme_score >= 450:
            ctos_penalty = 20
        else:
            ctos_penalty = 25
        
        # Cashflow Variance扣分 (最多-15分)
        if cashflow_variance <= 0.20:
            variance_penalty = 0
        elif cashflow_variance <= 0.35:
            variance_penalty = 5
        elif cashflow_variance <= 0.50:
            variance_penalty = 10
        else:
            variance_penalty = 15
        
        # 行业风险扣分 (最多-10分)
        industry_penalty = industry_risk_score  # 1~10分直接映射
        
        # 公司年龄扣分 (最多-5分)
        if company_age_years >= 10:
            age_penalty = 0
        elif company_age_years >= 5:
            age_penalty = 2
        elif company_age_years >= 2:
            age_penalty = 4
        else:
            age_penalty = 5
        
        # 计算最终分数
        final_score = (
            base_score
            - dscr_penalty
            - dsr_penalty
            - ctos_penalty
            - variance_penalty
            - industry_penalty
            - age_penalty
        )
        final_score = max(0, min(100, final_score))
        
        # 映射到BRR等级 (1~10, 1=最佳)
        brr_grade = max(1, min(10, int((100 - final_score) / 10) + 1))
        
        # 风险分类
        if brr_grade <= 2:
            risk_category = "Excellent"
            approval_probability = 0.95
        elif brr_grade <= 4:
            risk_category = "Good"
            approval_probability = 0.85
        elif brr_grade <= 6:
            risk_category = "Fair"
            approval_probability = 0.65
        elif brr_grade <= 8:
            risk_category = "Poor"
            approval_probability = 0.40
        else:
            risk_category = "High Risk"
            approval_probability = 0.20
        
        return {
            "brr_grade": brr_grade,
            "risk_category": risk_category,
            "risk_score": int(final_score),
            "approval_probability": approval_probability,
            "scoring_breakdown": {
                "base_score": 100,
                "dscr_penalty": -dscr_penalty,
                "dsr_penalty": -dsr_penalty,
                "ctos_penalty": -ctos_penalty,
                "variance_penalty": -variance_penalty,
                "industry_penalty": -industry_penalty,
                "age_penalty": -age_penalty
            }
        }
    
    # =================================================================
    # APPROVAL PROBABILITY CALCULATION
    # =================================================================
    
    @staticmethod
    def calculate_approval_odds(
        risk_score: int,
        income: float,
        min_income_required: float,
        max_dti: float,
        actual_dti: float
    ) -> float:
        """
        综合审批概率计算
        
        Returns:
            审批概率 (0~100)
        """
        # 基础概率（基于风险分数）
        base_probability = risk_score / 100
        
        # 收入达标调整
        income_ratio = income / min_income_required if min_income_required > 0 else 1.0
        if income_ratio >= 2.0:
            income_boost = 0.10
        elif income_ratio >= 1.5:
            income_boost = 0.05
        elif income_ratio >= 1.0:
            income_boost = 0.0
        else:
            income_boost = -0.20
        
        # DTI达标调整
        dti_ratio = actual_dti / max_dti if max_dti > 0 else 0.0
        if dti_ratio <= 0.7:
            dti_boost = 0.10
        elif dti_ratio <= 0.9:
            dti_boost = 0.05
        elif dti_ratio <= 1.0:
            dti_boost = 0.0
        else:
            dti_boost = -0.30
        
        # 最终概率
        final_probability = base_probability + income_boost + dti_boost
        final_probability = max(0.0, min(1.0, final_probability))
        
        return round(final_probability * 100, 1)
