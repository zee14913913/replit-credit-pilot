"""
Loan Product Matcher - 贷款产品匹配引擎
根据风险等级自动推荐适合的银行/Fintech产品

PHASE 4 增强：
- 集成12+家真实银行/Fintech产品目录
- 动态利率计算（基于风险等级）
- 智能批准概率预测
- 产品匹配评分系统
"""
from typing import Dict, List, Optional
import math
from .risk_engine.risk_tables import BANK_DTI_LIMITS, SME_BANK_STANDARDS
from .risk_engine.product_catalog import (
    PERSONAL_LOAN_CATALOG,
    SME_LOAN_CATALOG,
    get_all_personal_products,
    get_all_sme_products
)


class LoanProductMatcher:
    """贷款产品匹配引擎 - PHASE 4 增强版"""
    
    # ============================================================
    # PHASE 4: 智能产品匹配引擎
    # ============================================================
    
    @staticmethod
    def match_personal_loan_v2(
        risk_grade: str,
        income: float,
        monthly_commitment: float,
        ccris_bucket: int = 0,
        credit_score: int = 700,
        max_emi: float = None,
        top_n: int = None
    ) -> List[Dict]:
        """
        PHASE 4 增强版个人贷款匹配
        
        Args:
            risk_grade: 风险等级 (A+, A, B+, B, C, D)
            income: 月收入
            monthly_commitment: 现有月度承诺
            ccris_bucket: CCRIS bucket (0~3)
            credit_score: 信用分数
            max_emi: 最大月供能力（可选）
            top_n: 返回前N个产品（None=全部）
            
        Returns:
            推荐产品列表（智能评分+动态利率+批准概率）
        """
        recommended_products = []
        
        # 计算最大EMI（如未提供）
        if max_emi is None:
            dti = monthly_commitment / income if income > 0 else 0
            available_capacity = income * 0.70 - monthly_commitment
            max_emi = max(0, available_capacity)
        
        for product_id, product_data in PERSONAL_LOAN_CATALOG.items():
            # 1. 基本筛选
            if income < product_data["min_income"]:
                continue
            
            if ccris_bucket > product_data["ccris_bucket_max"]:
                continue
            
            if credit_score < product_data["min_credit_score"]:
                continue
            
            # 2. 风险等级匹配
            if risk_grade not in product_data["required_risk_bands"]:
                continue
            
            # 3. 计算匹配分数
            match_score = LoanProductMatcher._calculate_match_score(
                risk_grade=risk_grade,
                credit_score=credit_score,
                ccris_bucket=ccris_bucket,
                product_type=product_data["type"],
                required_bands=product_data["required_risk_bands"]
            )
            
            # 4. 计算动态利率
            dynamic_rate = LoanProductMatcher._calculate_dynamic_interest_rate(
                base_rate=product_data["base_rate"],
                rate_range=product_data["rate_range"],
                risk_grade=risk_grade,
                credit_score=credit_score,
                ccris_bucket=ccris_bucket
            )
            
            # 5. 计算最大可贷金额
            max_loan_amount = min(
                product_data["max_amount"],
                LoanProductMatcher._calculate_loan_from_emi(
                    max_emi, dynamic_rate, product_data["max_tenure"]
                )
            )
            
            # 6. 计算批准概率
            approval_odds = LoanProductMatcher._calculate_approval_probability(
                match_score=match_score,
                credit_score=credit_score,
                ccris_bucket=ccris_bucket,
                risk_grade=risk_grade
            )
            
            recommended_products.append({
                "product_id": product_id,
                "bank": product_data["bank"],
                "product_name": product_data["product_name"],
                "type": product_data["type"],
                "match_score": round(match_score, 1),
                "interest_rate": round(dynamic_rate, 4),
                "rate_range": product_data["rate_range"],
                "max_loan_amount": round(max_loan_amount, 2),
                "max_tenure": product_data["max_tenure"],
                "approval_odds": round(approval_odds, 1),
                "approval_time_hours": product_data.get("approval_time_hours", 48),
                "features": product_data["features"],
                "digital_application": product_data["digital_application"]
            })
        
        # 按匹配分数排序
        recommended_products.sort(key=lambda x: (-x["match_score"], -x["approval_odds"]))
        
        return recommended_products[:top_n] if top_n else recommended_products
    
    @staticmethod
    def match_sme_loan_v2(
        brr_grade: int,
        dscr: float,
        operating_income: float,
        industry_sector: str,
        ctos_sme_score: int = 650,
        company_age_years: int = 5,
        max_loan_amount: float = None,
        cgc_eligible: bool = False,
        top_n: int = None
    ) -> List[Dict]:
        """
        PHASE 4 增强版SME贷款匹配
        
        Args:
            brr_grade: BRR等级 (1~10)
            dscr: DSCR比率
            operating_income: 年度营业收入
            industry_sector: 行业分类
            ctos_sme_score: CTOS SME分数
            company_age_years: 公司年龄
            max_loan_amount: 风控引擎计算的最大可贷额
            cgc_eligible: CGC资格
            top_n: 返回前N个产品
            
        Returns:
            推荐产品列表
        """
        recommended_products = []
        
        for product_id, product_data in SME_LOAN_CATALOG.items():
            # 1. 基本筛选
            if operating_income < product_data["min_revenue"]:
                continue
            
            if brr_grade not in product_data["required_brr_grades"]:
                continue
            
            if dscr < product_data["min_dscr"]:
                continue
            
            if ctos_sme_score < product_data["min_ctos_sme_score"]:
                continue
            
            # 2. 行业筛选
            industry_allowed = product_data["industry_allowed"]
            industry_excluded = product_data["industry_excluded"]
            
            if industry_allowed != ["all"] and industry_sector not in industry_allowed:
                continue
            
            if industry_sector in industry_excluded:
                continue
            
            # 3. 计算匹配分数
            match_score = LoanProductMatcher._calculate_sme_match_score(
                brr_grade=brr_grade,
                dscr=dscr,
                ctos_sme_score=ctos_sme_score,
                industry_sector=industry_sector,
                product_type=product_data["type"],
                required_brr_grades=product_data["required_brr_grades"]
            )
            
            # 4. 计算动态利率
            dynamic_rate = LoanProductMatcher._calculate_sme_dynamic_rate(
                base_rate=product_data["base_rate"],
                rate_range=product_data["rate_range"],
                brr_grade=brr_grade,
                dscr=dscr,
                ctos_sme_score=ctos_sme_score
            )
            
            # 5. 计算最大可贷金额
            calculated_max = min(
                product_data["max_amount"],
                max_loan_amount if max_loan_amount else product_data["max_amount"]
            )
            
            # 6. 计算批准概率
            approval_odds = LoanProductMatcher._calculate_sme_approval_probability(
                match_score=match_score,
                brr_grade=brr_grade,
                dscr=dscr,
                ctos_sme_score=ctos_sme_score
            )
            
            recommended_products.append({
                "product_id": product_id,
                "bank": product_data["bank"],
                "product_name": product_data["product_name"],
                "type": product_data["type"],
                "match_score": round(match_score, 1),
                "interest_rate": round(dynamic_rate, 4),
                "rate_range": product_data["rate_range"],
                "max_loan_amount": round(calculated_max, 2),
                "max_tenure": product_data["max_tenure"],
                "approval_odds": round(approval_odds, 1),
                "cgc_eligible": product_data.get("cgc_eligible", False),
                "features": product_data["features"]
            })
        
        # 按匹配分数排序
        recommended_products.sort(key=lambda x: (-x["match_score"], -x["approval_odds"]))
        
        return recommended_products[:top_n] if top_n else recommended_products
    
    # ============================================================
    # PHASE 4: 核心计算方法
    # ============================================================
    
    @staticmethod
    def _calculate_match_score(
        risk_grade: str,
        credit_score: int,
        ccris_bucket: int,
        product_type: str,
        required_bands: List[str]
    ) -> float:
        """
        计算产品匹配分数 (0~100)
        
        权重：
        - Risk Grade匹配: 40%
        - Credit Score: 30%
        - CCRIS Bucket: 20%
        - Product Type适配: 10%
        """
        score = 0.0
        
        # 1. Risk Grade匹配度 (40分)
        if risk_grade == required_bands[0]:
            score += 40
        elif risk_grade in required_bands[:3]:
            score += 35
        elif risk_grade in required_bands:
            score += 25
        else:
            score += 10
        
        # 2. Credit Score (30分)
        if credit_score >= 750:
            score += 30
        elif credit_score >= 700:
            score += 25
        elif credit_score >= 650:
            score += 20
        elif credit_score >= 600:
            score += 15
        else:
            score += 10
        
        # 3. CCRIS Bucket (20分)
        if ccris_bucket == 0:
            score += 20
        elif ccris_bucket == 1:
            score += 15
        elif ccris_bucket == 2:
            score += 10
        else:
            score += 5
        
        # 4. Product Type适配 (10分)
        if product_type == "traditional_bank":
            if risk_grade in ["A+", "A", "B+"]:
                score += 10
            else:
                score += 5
        elif product_type == "digital_bank":
            if risk_grade in ["B", "C", "D"]:
                score += 10
            else:
                score += 7
        elif product_type == "fintech":
            if risk_grade in ["C", "D"]:
                score += 10
            else:
                score += 6
        
        return min(100.0, score)
    
    @staticmethod
    def _calculate_dynamic_interest_rate(
        base_rate: float,
        rate_range: tuple,
        risk_grade: str,
        credit_score: int,
        ccris_bucket: int
    ) -> float:
        """
        计算动态利率
        
        公式: rate = base_rate × (1 + risk_multiplier)
        """
        min_rate, max_rate = rate_range
        
        # 风险等级系数
        risk_multiplier_map = {
            "A+": 0.0,
            "A": 0.1,
            "B+": 0.2,
            "B": 0.35,
            "C": 0.55,
            "D": 0.80
        }
        risk_multiplier = risk_multiplier_map.get(risk_grade, 0.5)
        
        # Credit Score调整
        if credit_score >= 750:
            credit_adjustment = -0.05
        elif credit_score >= 700:
            credit_adjustment = 0.0
        elif credit_score >= 650:
            credit_adjustment = 0.05
        else:
            credit_adjustment = 0.10
        
        # CCRIS Bucket调整
        ccris_adjustment = ccris_bucket * 0.08
        
        # 最终利率
        dynamic_rate = base_rate * (1 + risk_multiplier) + credit_adjustment + ccris_adjustment
        
        # 限制在range内
        return max(min_rate, min(dynamic_rate, max_rate))
    
    @staticmethod
    def _calculate_approval_probability(
        match_score: float,
        credit_score: int,
        ccris_bucket: int,
        risk_grade: str
    ) -> float:
        """
        计算批准概率 (0~100%)
        
        使用Sigmoid函数平滑曲线
        """
        # 基础概率（基于match_score）
        base_prob = match_score * 0.85  # 85分match_score = 72%基础概率
        
        # Credit Score加成
        if credit_score >= 750:
            base_prob += 10
        elif credit_score >= 700:
            base_prob += 5
        elif credit_score < 600:
            base_prob -= 10
        
        # CCRIS Bucket惩罚
        if ccris_bucket == 0:
            base_prob += 5
        elif ccris_bucket >= 2:
            base_prob -= 15
        
        # Risk Grade调整
        if risk_grade in ["A+", "A"]:
            base_prob += 8
        elif risk_grade in ["C", "D"]:
            base_prob -= 12
        
        # Sigmoid平滑
        sigmoid_prob = 100 / (1 + math.exp(-(base_prob - 50) / 15))
        
        return max(5.0, min(99.0, sigmoid_prob))
    
    @staticmethod
    def _calculate_sme_match_score(
        brr_grade: int,
        dscr: float,
        ctos_sme_score: int,
        industry_sector: str,
        product_type: str,
        required_brr_grades: List[int]
    ) -> float:
        """
        计算SME产品匹配分数
        
        权重：
        - BRR Grade: 35%
        - DSCR: 30%
        - CTOS SME Score: 25%
        - Industry/Type适配: 10%
        """
        score = 0.0
        
        # 1. BRR Grade (35分)
        if brr_grade <= 3:
            score += 35
        elif brr_grade <= 5:
            score += 28
        elif brr_grade <= 7:
            score += 20
        else:
            score += 12
        
        # 2. DSCR (30分)
        if dscr >= 2.0:
            score += 30
        elif dscr >= 1.75:
            score += 25
        elif dscr >= 1.50:
            score += 20
        elif dscr >= 1.25:
            score += 15
        else:
            score += 10
        
        # 3. CTOS SME Score (25分)
        if ctos_sme_score >= 750:
            score += 25
        elif ctos_sme_score >= 700:
            score += 20
        elif ctos_sme_score >= 650:
            score += 16
        elif ctos_sme_score >= 600:
            score += 12
        else:
            score += 8
        
        # 4. Industry/Type适配 (10分)
        if product_type == "traditional_bank":
            if brr_grade <= 4:
                score += 10
            else:
                score += 6
        elif product_type == "fintech":
            if brr_grade >= 5:
                score += 10
            else:
                score += 7
        
        return min(100.0, score)
    
    @staticmethod
    def _calculate_sme_dynamic_rate(
        base_rate: float,
        rate_range: tuple,
        brr_grade: int,
        dscr: float,
        ctos_sme_score: int
    ) -> float:
        """计算SME动态利率"""
        min_rate, max_rate = rate_range
        
        # BRR Grade系数
        brr_multiplier = (brr_grade - 1) * 0.12
        
        # DSCR调整
        if dscr >= 2.0:
            dscr_adjustment = -0.08
        elif dscr >= 1.75:
            dscr_adjustment = -0.04
        elif dscr >= 1.50:
            dscr_adjustment = 0.0
        elif dscr >= 1.25:
            dscr_adjustment = 0.06
        else:
            dscr_adjustment = 0.12
        
        # CTOS SME Score调整
        if ctos_sme_score >= 750:
            ctos_adjustment = -0.06
        elif ctos_sme_score >= 700:
            ctos_adjustment = -0.02
        elif ctos_sme_score >= 650:
            ctos_adjustment = 0.0
        else:
            ctos_adjustment = 0.05
        
        # 最终利率
        dynamic_rate = base_rate * (1 + brr_multiplier) + dscr_adjustment + ctos_adjustment
        
        return max(min_rate, min(dynamic_rate, max_rate))
    
    @staticmethod
    def _calculate_sme_approval_probability(
        match_score: float,
        brr_grade: int,
        dscr: float,
        ctos_sme_score: int
    ) -> float:
        """计算SME批准概率"""
        base_prob = match_score * 0.80
        
        # BRR Grade调整
        if brr_grade <= 3:
            base_prob += 12
        elif brr_grade <= 5:
            base_prob += 5
        elif brr_grade >= 8:
            base_prob -= 15
        
        # DSCR调整
        if dscr >= 2.0:
            base_prob += 10
        elif dscr >= 1.50:
            base_prob += 5
        elif dscr < 1.25:
            base_prob -= 12
        
        # CTOS调整
        if ctos_sme_score >= 750:
            base_prob += 8
        elif ctos_sme_score < 600:
            base_prob -= 10
        
        # Sigmoid平滑
        sigmoid_prob = 100 / (1 + math.exp(-(base_prob - 50) / 18))
        
        return max(5.0, min(98.0, sigmoid_prob))
    
    # ============================================================
    # LEGACY METHODS (向后兼容)
    # ============================================================
    
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
