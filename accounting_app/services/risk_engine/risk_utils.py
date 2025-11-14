"""
Risk Utilities - 马来西亚银行风控标准化层
Normalization and risk factor calculation utilities

负责：
- Income normalization (Bank Statement / Salary / Business)
- Commitment normalization (CTOS)
- Age risk factor
- Employment stability factor
- Company risk factor (SME)
- Industry sector risk mapping (BNM standard)
- Digital bank risk band scaling
"""
from typing import Dict, Optional, Tuple
from datetime import datetime
from dateutil.relativedelta import relativedelta


class RiskUtils:
    """统一风险工具类"""
    
    # =================================================================
    # INCOME NORMALIZATION
    # =================================================================
    
    @staticmethod
    def normalize_income(
        income_data: Dict,
        income_type: str = "salary"
    ) -> Dict:
        """
        收入标准化
        
        Args:
            income_data: 原始收入数据
            income_type: salary | business | bank_statement
            
        Returns:
            {
                "monthly_income": float,
                "confidence": float,
                "source": str,
                "variance": float  # 0~1, 0 = 稳定
            }
        """
        if income_type == "salary":
            return RiskUtils._normalize_salary_income(income_data)
        elif income_type == "business":
            return RiskUtils._normalize_business_income(income_data)
        elif income_type == "bank_statement":
            return RiskUtils._normalize_bank_statement_income(income_data)
        else:
            raise ValueError(f"Unknown income_type: {income_type}")
    
    @staticmethod
    def _normalize_salary_income(data: Dict) -> Dict:
        """工资收入标准化 - 最高置信度"""
        monthly_income = data.get("dsr_income", 0.0)
        return {
            "monthly_income": monthly_income,
            "confidence": 0.95,
            "source": "salary_slip",
            "variance": 0.05  # 工资最稳定
        }
    
    @staticmethod
    def _normalize_business_income(data: Dict) -> Dict:
        """企业收入标准化 - 中等置信度"""
        annual_income = data.get("operating_income", 0.0)
        monthly_income = annual_income / 12
        return {
            "monthly_income": monthly_income,
            "confidence": 0.75,
            "source": "business_financials",
            "variance": 0.25  # 企业收入波动较大
        }
    
    @staticmethod
    def _normalize_bank_statement_income(data: Dict) -> Dict:
        """银行流水收入标准化 - Fintech方法"""
        monthly_income = data.get("avg_monthly_inflow", 0.0)
        variance = data.get("income_variance", 0.3)
        
        # Fintech: variance > 0.4 = High Risk
        confidence = max(0.5, 1.0 - variance)
        
        return {
            "monthly_income": monthly_income,
            "confidence": round(confidence, 2),
            "source": "bank_statement",
            "variance": variance
        }
    
    # =================================================================
    # COMMITMENT NORMALIZATION (CTOS)
    # =================================================================
    
    @staticmethod
    def normalize_commitment(
        monthly_commitment: Optional[float],
        annual_commitment: Optional[float] = None
    ) -> float:
        """
        债务承诺标准化（统一转为月度）
        
        Args:
            monthly_commitment: 月度承诺还款
            annual_commitment: 年度承诺还款（SME）
            
        Returns:
            标准化后的月度承诺还款
        """
        if monthly_commitment is not None and monthly_commitment > 0:
            return float(monthly_commitment)
        elif annual_commitment is not None and annual_commitment > 0:
            return float(annual_commitment) / 12
        else:
            return 0.0
    
    # =================================================================
    # AGE RISK FACTOR
    # =================================================================
    
    @staticmethod
    def calculate_age_risk_factor(age: int) -> Dict:
        """
        年龄风险因子（马来西亚银行标准）
        
        规则：
        - 21~25: High Risk (1.3x)
        - 26~35: Low Risk (1.0x)
        - 36~50: Medium Risk (1.1x)
        - 51~60: High Risk (1.4x)
        - >60: Very High Risk (1.8x)
        
        Returns:
            {
                "age_band": str,
                "risk_multiplier": float,
                "max_tenure": int  # 月份
            }
        """
        if age < 21:
            return {"age_band": "Underage", "risk_multiplier": 2.0, "max_tenure": 0}
        elif 21 <= age <= 25:
            return {"age_band": "21-25", "risk_multiplier": 1.3, "max_tenure": 60}
        elif 26 <= age <= 35:
            return {"age_band": "26-35", "risk_multiplier": 1.0, "max_tenure": 84}
        elif 36 <= age <= 50:
            return {"age_band": "36-50", "risk_multiplier": 1.1, "max_tenure": 72}
        elif 51 <= age <= 60:
            return {"age_band": "51-60", "risk_multiplier": 1.4, "max_tenure": 60}
        else:
            return {"age_band": ">60", "risk_multiplier": 1.8, "max_tenure": 36}
    
    # =================================================================
    # EMPLOYMENT STABILITY FACTOR
    # =================================================================
    
    @staticmethod
    def calculate_employment_stability(
        employment_years: float,
        job_type: str = "permanent"
    ) -> Dict:
        """
        就业稳定性因子
        
        Args:
            employment_years: 工作年限
            job_type: permanent | contract | self_employed
            
        Returns:
            {
                "stability_grade": str,
                "risk_adjustment": float  # -0.1 ~ +0.2
            }
        """
        # 基础风险调整
        if job_type == "permanent":
            base_adjustment = 0.0
        elif job_type == "contract":
            base_adjustment = 0.1
        else:  # self_employed
            base_adjustment = 0.15
        
        # 工作年限调整
        if employment_years >= 5:
            grade = "Excellent"
            years_adjustment = -0.05
        elif employment_years >= 2:
            grade = "Good"
            years_adjustment = 0.0
        elif employment_years >= 1:
            grade = "Fair"
            years_adjustment = 0.05
        else:
            grade = "Poor"
            years_adjustment = 0.1
        
        total_adjustment = base_adjustment + years_adjustment
        
        return {
            "stability_grade": grade,
            "risk_adjustment": round(total_adjustment, 2),
            "job_type": job_type
        }
    
    # =================================================================
    # COMPANY RISK FACTOR (SME)
    # =================================================================
    
    @staticmethod
    def calculate_company_risk_factor(
        company_age_years: int,
        employee_count: int
    ) -> Dict:
        """
        公司风险因子（SME）
        
        Returns:
            {
                "company_risk_grade": str,
                "risk_multiplier": float
            }
        """
        # 公司年龄风险
        if company_age_years >= 10:
            age_risk = "Low"
            age_multiplier = 1.0
        elif company_age_years >= 5:
            age_risk = "Medium"
            age_multiplier = 1.2
        elif company_age_years >= 2:
            age_risk = "High"
            age_multiplier = 1.4
        else:
            age_risk = "Very High"
            age_multiplier = 1.8
        
        # 员工规模风险
        if employee_count >= 50:
            size_risk = "Low"
            size_multiplier = 1.0
        elif employee_count >= 20:
            size_risk = "Medium"
            size_multiplier = 1.1
        elif employee_count >= 5:
            size_risk = "High"
            size_multiplier = 1.3
        else:
            size_risk = "Very High"
            size_multiplier = 1.5
        
        combined_multiplier = (age_multiplier + size_multiplier) / 2
        
        return {
            "company_risk_grade": f"{age_risk}/{size_risk}",
            "risk_multiplier": round(combined_multiplier, 2)
        }
    
    # =================================================================
    # INDUSTRY SECTOR RISK MAPPING (BNM STANDARD)
    # =================================================================
    
    @staticmethod
    def get_industry_risk(industry_sector: str) -> Dict:
        """
        行业风险映射（BNM标准）
        
        Returns:
            {
                "industry": str,
                "risk_level": str,  # Low | Medium | High
                "risk_score": int   # 1~10
            }
        """
        industry_map = {
            # Low Risk (1-3)
            "professional_services": {"risk_level": "Low", "risk_score": 2},
            "healthcare": {"risk_level": "Low", "risk_score": 2},
            "education": {"risk_level": "Low", "risk_score": 2},
            "government": {"risk_level": "Low", "risk_score": 1},
            
            # Medium Risk (4-6)
            "trading": {"risk_level": "Medium", "risk_score": 5},
            "retail": {"risk_level": "Medium", "risk_score": 5},
            "fnb": {"risk_level": "Medium", "risk_score": 6},
            "manufacturing": {"risk_level": "Medium", "risk_score": 5},
            "logistics": {"risk_level": "Medium", "risk_score": 5},
            
            # High Risk (7-10)
            "construction": {"risk_level": "High", "risk_score": 8},
            "property_development": {"risk_level": "High", "risk_score": 7},
            "agriculture": {"risk_level": "High", "risk_score": 7},
            "oil_gas": {"risk_level": "High", "risk_score": 6},
            "tourism_hospitality": {"risk_level": "High", "risk_score": 8}
        }
        
        sector_lower = industry_sector.lower().replace(" ", "_")
        result = industry_map.get(sector_lower, {"risk_level": "Medium", "risk_score": 5})
        
        return {
            "industry": industry_sector,
            **result
        }
    
    # =================================================================
    # DIGITAL BANK RISK BAND SCALING
    # =================================================================
    
    @staticmethod
    def calculate_digital_bank_risk_band(
        credit_score: int,
        income: float,
        commitment: float
    ) -> Dict:
        """
        数字银行风险分级（GXBank/Boost/Grab标准）
        
        Args:
            credit_score: CTOS/CCRIS分数
            income: 月收入
            commitment: 月度承诺还款
            
        Returns:
            {
                "risk_band": str,  # A | B | C | D
                "dti_limit": float,
                "max_emi_multiplier": float
            }
        """
        dti = commitment / income if income > 0 else 0.0
        
        # Band A: 低风险
        if credit_score >= 750 and dti <= 0.3:
            return {
                "risk_band": "A",
                "dti_limit": 0.65,
                "max_emi_multiplier": 1.2
            }
        
        # Band B: 中低风险
        elif credit_score >= 650 and dti <= 0.5:
            return {
                "risk_band": "B",
                "dti_limit": 0.60,
                "max_emi_multiplier": 1.0
            }
        
        # Band C: 中高风险
        elif credit_score >= 550 and dti <= 0.6:
            return {
                "risk_band": "C",
                "dti_limit": 0.50,
                "max_emi_multiplier": 0.8
            }
        
        # Band D: 高风险
        else:
            return {
                "risk_band": "D",
                "dti_limit": 0.40,
                "max_emi_multiplier": 0.6
            }
