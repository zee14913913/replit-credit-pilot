"""
Loan Product Matcher - 贷款产品匹配引擎
根据风险等级自动推荐适合的银行/Fintech产品
"""
from typing import Dict, List
from .risk_engine.risk_tables import BANK_DTI_LIMITS, SME_BANK_STANDARDS


class LoanProductMatcher:
    """贷款产品匹配引擎"""
    
    @staticmethod
    def match_personal_loan_products(
        risk_grade: str,
        income: float,
        max_emi: float,
        digital_bank_band: str = "B"
    ) -> List[Dict]:
        """
        匹配个人贷款产品
        
        Args:
            risk_grade: 风险等级 (A+, A, B+, B, C, D)
            income: 月收入
            max_emi: 最大月供能力
            digital_bank_band: 数字银行风险分级 (A, B, C, D)
            
        Returns:
            推荐产品列表（按匹配度排序）
        """
        recommended_products = []
        
        for bank_code, bank_data in BANK_DTI_LIMITS.items():
            # 收入筛选
            if income < bank_data.get("min_income", 0):
                continue
            
            # 风险等级匹配
            if risk_grade in ["A+", "A"]:
                # 所有银行都适合
                match_score = 100
            elif risk_grade in ["B+", "B"]:
                # 传统银行和优质数字银行
                if bank_data.get("risk_band_based"):
                    match_score = 90 if digital_bank_band in ["A", "B"] else 60
                else:
                    match_score = 85
            elif risk_grade == "C":
                # 数字银行和Fintech
                if bank_data.get("risk_band_based") or bank_data.get("risk_score_based"):
                    match_score = 75
                else:
                    match_score = 50
            else:  # D
                # 仅Fintech
                if bank_data.get("risk_score_based"):
                    match_score = 60
                else:
                    continue
            
            # 计算产品详情
            min_rate, max_rate = bank_data["interest_rate_range"]
            avg_rate = (min_rate + max_rate) / 2
            
            # 根据风险等级调整利率
            if risk_grade in ["A+", "A"]:
                offered_rate = min_rate
            elif risk_grade in ["B+", "B"]:
                offered_rate = min_rate + (avg_rate - min_rate) * 0.5
            elif risk_grade == "C":
                offered_rate = avg_rate
            else:
                offered_rate = max_rate
            
            # 计算可贷金额（60个月）
            max_loan = LoanProductMatcher._calculate_loan_from_emi(
                max_emi, offered_rate, 60
            )
            
            recommended_products.append({
                "bank": bank_data["name"],
                "bank_code": bank_code,
                "product_type": "Personal Loan",
                "match_score": match_score,
                "interest_rate": round(offered_rate, 4),
                "rate_range": bank_data["interest_rate_range"],
                "max_loan_amount": round(max_loan, 2),
                "max_tenure": bank_data["max_tenure"],
                "min_income": bank_data["min_income"],
                "features": LoanProductMatcher._get_product_features(bank_code, risk_grade)
            })
        
        # 按匹配分数排序
        recommended_products.sort(key=lambda x: x["match_score"], reverse=True)
        
        return recommended_products[:10]  # 返回前10个
    
    @staticmethod
    def match_sme_loan_products(
        brr_grade: int,
        dscr: float,
        industry_sector: str,
        max_loan_amount: float,
        cgc_eligible: bool = False
    ) -> List[Dict]:
        """
        匹配SME贷款产品
        
        Args:
            brr_grade: BRR等级 (1~10)
            dscr: DSCR比率
            industry_sector: 行业分类
            max_loan_amount: 最大贷款额
            cgc_eligible: CGC资格
            
        Returns:
            推荐产品列表
        """
        recommended_products = []
        
        for bank_code, bank_data in SME_BANK_STANDARDS.items():
            # BRR筛选
            if brr_grade <= 4:
                # 所有银行
                match_score = 100
            elif brr_grade <= 6:
                # 传统银行和部分Fintech
                if bank_data.get("alternative_data"):
                    match_score = 85
                else:
                    match_score = 75
            elif brr_grade <= 8:
                # 主要Fintech
                if bank_data.get("alternative_data"):
                    match_score = 70
                else:
                    continue
            else:
                # 仅高风险Fintech
                if bank_code in ["funding_societies", "boost_credit"]:
                    match_score = 50
                else:
                    continue
            
            # DSCR筛选
            if dscr < bank_data["min_dscr"]:
                continue
            
            # 贷款额度筛选
            if max_loan_amount > bank_data["max_loan_amount"]:
                match_score -= 20
            
            # 计算利率
            min_rate, max_rate = bank_data["interest_rate_range"]
            if brr_grade <= 2:
                offered_rate = min_rate
            elif brr_grade <= 4:
                offered_rate = min_rate + (max_rate - min_rate) * 0.3
            elif brr_grade <= 6:
                offered_rate = min_rate + (max_rate - min_rate) * 0.6
            else:
                offered_rate = max_rate
            
            recommended_products.append({
                "bank": bank_data["name"],
                "bank_code": bank_code,
                "product_type": "SME Loan",
                "match_score": max(0, match_score),
                "interest_rate": round(offered_rate, 4),
                "rate_range": bank_data["interest_rate_range"],
                "max_loan_amount": min(max_loan_amount, bank_data["max_loan_amount"]),
                "max_tenure": bank_data["max_tenure"],
                "min_dscr": bank_data["min_dscr"],
                "min_ctos_score": bank_data.get("min_ctos_sme_score", 0),
                "cgc_support": cgc_eligible,
                "features": LoanProductMatcher._get_sme_product_features(bank_code, brr_grade)
            })
        
        # 按匹配分数排序
        recommended_products.sort(key=lambda x: x["match_score"], reverse=True)
        
        return recommended_products[:10]
    
    @staticmethod
    def _calculate_loan_from_emi(emi: float, annual_rate: float, tenure_months: int) -> float:
        """从EMI计算贷款金额"""
        if emi <= 0 or annual_rate <= 0 or tenure_months <= 0:
            return 0.0
        
        monthly_rate = annual_rate / 12
        if monthly_rate == 0:
            return emi * tenure_months
        
        pv = emi * ((1 - (1 + monthly_rate) ** -tenure_months) / monthly_rate)
        return pv
    
    @staticmethod
    def _get_product_features(bank_code: str, risk_grade: str) -> List[str]:
        """获取产品特性"""
        features = []
        
        if bank_code in ["maybank", "public_bank", "cimb"]:
            features.append("Traditional Bank - Stable & Trusted")
        
        if bank_code in ["gxbank", "boost_bank"]:
            features.append("Digital Bank - Fast Approval")
            features.append("Instant Disbursement")
        
        if bank_code in ["aeon_credit", "grab_paylater"]:
            features.append("Flexible Repayment")
            features.append("No Collateral Required")
        
        if risk_grade in ["A+", "A"]:
            features.append("Premium Rate Offered")
        
        return features
    
    @staticmethod
    def _get_sme_product_features(bank_code: str, brr_grade: int) -> List[str]:
        """获取SME产品特性"""
        features = []
        
        if bank_code in ["maybank_sme", "public_bank_sme", "cimb_sme"]:
            features.append("Government-Backed Scheme Available")
        
        if bank_code in ["funding_societies", "boost_credit"]:
            features.append("Fast Approval (24-72 hours)")
            features.append("Minimal Documentation")
        
        if brr_grade <= 4:
            features.append("Low Interest Rate")
            features.append("Long Tenure Available")
        
        return features
