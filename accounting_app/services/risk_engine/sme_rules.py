"""
SME Loan Rules - 企业贷款审批规则引擎
基于DSCR/DSR/BRR/Cashflow Variance的马来西亚SME标准
"""
from typing import Dict, Optional
from .risk_tables import SME_BANK_STANDARDS, CTOS_SME_SCORE_BANDS, BNM_INDUSTRY_RISK, CGC_ELIGIBILITY_CRITERIA
from .scoring_matrix import ScoringMatrix
from .risk_utils import RiskUtils


class SMELoanRules:
    """SME贷款审批规则引擎"""
    
    @classmethod
    def evaluate_sme_loan_eligibility(
        cls,
        operating_income: float,
        annual_commitment: float,
        ctos_sme_score: int = 650,
        cashflow_variance: float = 0.30,
        industry_sector: str = "trading",
        company_age_years: int = 5,
        employee_count: int = 10,
        target_bank: str = "maybank_sme"
    ) -> Dict:
        """
        评估SME贷款资格（马来西亚银行标准）
        
        Args:
            operating_income: 年度营业收入
            annual_commitment: 年度承诺还款（CTOS）
            ctos_sme_score: CTOS SME分数 (0~999)
            cashflow_variance: 现金流波动率 (0~1)
            industry_sector: 行业分类
            company_age_years: 公司年龄
            employee_count: 员工数量
            target_bank: 目标银行
            
        Returns:
            {
                "brr_grade": int,
                "dscr": float,
                "dsr": float,
                "industry_risk": str,
                "cashflow_variance": float,
                "max_loan_amount": float,
                "approval_probability": float,
                "cgc_eligibility": bool
            }
        """
        # 1. 计算DSCR (Debt Service Coverage Ratio)
        dscr = operating_income / annual_commitment if annual_commitment > 0 else float('inf')
        
        # 2. 计算DSR (现金流式)
        # DSR = (operating_income - annual_commitment) / annual_commitment
        dsr = ((operating_income - annual_commitment) / annual_commitment) if annual_commitment > 0 else float('inf')
        dsr = max(0, dsr)  # 不能为负
        
        # 3. 获取银行标准
        bank_standards = SME_BANK_STANDARDS.get(target_bank, SME_BANK_STANDARDS["maybank_sme"])
        min_dscr = bank_standards["min_dscr"]
        min_dsr = bank_standards.get("min_dsr", 1.20)
        max_variance = bank_standards["max_cashflow_variance"]
        min_ctos = bank_standards["min_ctos_sme_score"]
        
        # 4. 行业风险
        industry_risk = RiskUtils.get_industry_risk(industry_sector)
        
        # 5. 公司风险因子
        company_risk = RiskUtils.calculate_company_risk_factor(
            company_age_years, employee_count
        )
        
        # 6. CTOS SME Score分级
        ctos_band = cls._get_ctos_sme_band(ctos_sme_score)
        
        # 7. 计算BRR等级
        brr_result = ScoringMatrix.calculate_brr_grade(
            dscr=dscr if dscr != float('inf') else 5.0,
            dsr=dsr if dsr != float('inf') else 5.0,
            ctos_sme_score=ctos_sme_score,
            cashflow_variance=cashflow_variance,
            industry_risk_score=industry_risk["risk_score"],
            company_age_years=company_age_years
        )
        
        # 8. 计算最大贷款额
        # 基于80%营业收入的债务承受能力
        max_annual_debt_service = operating_income * 0.80
        available_capacity = max(0, max_annual_debt_service - annual_commitment)
        
        # 应用行业风险multiplier
        max_loan_amount = available_capacity * industry_risk.get("max_exposure_multiplier", 1.0)
        
        # 应用银行限制
        max_loan_amount = min(max_loan_amount, bank_standards["max_loan_amount"])
        
        # 应用公司风险调整
        max_loan_amount = max_loan_amount / company_risk["risk_multiplier"]
        
        # 9. CGC资格评估
        cgc_eligible = cls._check_cgc_eligibility(
            max_loan_amount=max_loan_amount,
            industry_sector=industry_sector,
            company_age_years=company_age_years
        )
        
        # 10. 审批概率（基于BRR）
        approval_probability = brr_result["approval_probability"]
        
        # 应用CTOS分数调整
        approval_probability = (approval_probability + ctos_band["approval_probability"]) / 2
        
        # 11. 资格判定
        if dscr < min_dscr:
            eligibility_status = "Rejected - DSCR Below Minimum"
            approval_probability = min(30.0, approval_probability * 100)
        elif dsr < min_dsr:
            eligibility_status = "Rejected - DSR Below Minimum"
            approval_probability = min(40.0, approval_probability * 100)
        elif cashflow_variance > max_variance:
            eligibility_status = "High Risk - Unstable Cashflow"
            approval_probability = min(50.0, approval_probability * 100)
        elif ctos_sme_score < min_ctos:
            eligibility_status = "Rejected - Low CTOS Score"
            approval_probability = min(35.0, approval_probability * 100)
        elif brr_result["brr_grade"] <= 4:
            eligibility_status = "Approved"
            approval_probability = approval_probability * 100
        elif brr_result["brr_grade"] <= 6:
            eligibility_status = "Borderline - Additional Collateral Required"
            approval_probability = approval_probability * 100
        else:
            eligibility_status = "Rejected - High BRR Grade"
            approval_probability = min(40.0, approval_probability * 100)
        
        return {
            "eligibility_status": eligibility_status,
            "brr_grade": brr_result["brr_grade"],
            "risk_category": brr_result["risk_category"],
            "risk_score": brr_result["risk_score"],
            
            # 财务指标
            "dscr": round(dscr, 4) if dscr != float('inf') else 999.9999,
            "dsr": round(dsr, 4) if dsr != float('inf') else 999.9999,
            "operating_income": round(operating_income, 2),
            "annual_commitment": round(annual_commitment, 2),
            "cashflow_variance": round(cashflow_variance, 4),
            
            # 贷款能力
            "max_loan_amount": round(max_loan_amount, 2),
            "max_tenure_months": bank_standards["max_tenure"],
            "available_capacity": round(available_capacity, 2),
            
            # 审批信息
            "approval_probability": round(approval_probability / 100, 4),
            "approval_odds": round(approval_probability, 1),
            
            # 详细信息
            "bank_specific": {
                "bank_name": bank_standards["name"],
                "min_dscr": min_dscr,
                "min_dsr": min_dsr,
                "max_variance": max_variance,
                "min_ctos_score": min_ctos,
                "interest_rate_range": bank_standards["interest_rate_range"]
            },
            "industry_info": {
                "sector": industry_risk["industry"],
                "risk_level": industry_risk["risk_level"],
                "risk_score": industry_risk["risk_score"]
            },
            "company_info": {
                "age_years": company_age_years,
                "employee_count": employee_count,
                "risk_grade": company_risk["company_risk_grade"],
                "risk_multiplier": company_risk["risk_multiplier"]
            },
            "ctos_info": {
                "score": ctos_sme_score,
                "band": ctos_band["score_range"],
                "risk_level": ctos_band["risk_level"]
            },
            "cgc_eligibility": cgc_eligible,
            "scoring_breakdown": brr_result["scoring_breakdown"]
        }
    
    @staticmethod
    def _get_ctos_sme_band(score: int) -> Dict:
        """获取CTOS SME分数段"""
        for band_name, band_data in CTOS_SME_SCORE_BANDS.items():
            min_score, max_score = band_data["score_range"]
            if min_score <= score <= max_score:
                return band_data
        return CTOS_SME_SCORE_BANDS["poor"]
    
    @staticmethod
    def _check_cgc_eligibility(
        max_loan_amount: float,
        industry_sector: str,
        company_age_years: int
    ) -> bool:
        """检查CGC（信贷担保公司）资格"""
        # Micro enterprises
        if max_loan_amount <= CGC_ELIGIBILITY_CRITERIA["micro_enterprises"]["max_loan_amount"]:
            if company_age_years >= CGC_ELIGIBILITY_CRITERIA["micro_enterprises"]["min_business_age_years"]:
                return True
        
        # SME financing
        if max_loan_amount <= CGC_ELIGIBILITY_CRITERIA["sme_financing"]["max_loan_amount"]:
            if company_age_years >= CGC_ELIGIBILITY_CRITERIA["sme_financing"]["min_business_age_years"]:
                eligible_sectors = CGC_ELIGIBILITY_CRITERIA["sme_financing"]["eligible_sectors"]
                sector_normalized = industry_sector.lower().replace(" ", "_").replace("&", "").replace("_", "")
                for sector in eligible_sectors:
                    if sector in sector_normalized:
                        return True
        
        return False
