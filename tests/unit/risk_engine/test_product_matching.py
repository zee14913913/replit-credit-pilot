"""
Unit Tests for PHASE 4 - Product Matching Engine
测试智能产品匹配、动态利率计算、批准概率预测
"""
import pytest
from accounting_app.services.loan_products import LoanProductMatcher


class TestPersonalLoanProductMatching:
    """测试个人贷款产品匹配"""
    
    def test_high_risk_grade_matches_premium_banks(self):
        """高风险等级(A+/A)应匹配优质银行"""
        products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="A+",
            income=8000,
            monthly_commitment=1000,
            ccris_bucket=0,
            credit_score=780,
            top_n=5
        )
        
        assert len(products) > 0
        
        # 验证Top 1产品
        top_product = products[0]
        assert top_product["match_score"] >= 85
        assert top_product["approval_odds"] >= 85
        
        # 验证利率在合理范围
        assert 0.045 <= top_product["interest_rate"] <= 0.080
        
        # 验证银行类型（A+应匹配传统银行）
        top_banks = [p["bank"] for p in products[:3]]
        assert any(bank in top_banks for bank in ["Public Bank", "Standard Chartered", "Maybank"])
    
    def test_medium_risk_grade_matches_diverse_products(self):
        """中等风险等级(B+/B)应匹配多样化产品"""
        products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="B",
            income=4000,
            monthly_commitment=800,
            ccris_bucket=1,
            credit_score=650,
            top_n=10
        )
        
        assert len(products) >= 3
        
        # 验证包含传统银行和数字银行
        product_types = [p["type"] for p in products]
        assert "traditional_bank" in product_types
        
        # 验证利率范围（Fintech可能稍高）
        for product in products:
            assert 0.055 <= product["interest_rate"] <= 0.180
    
    def test_high_risk_grade_matches_fintech(self):
        """高风险等级(C/D)应主要推荐Fintech/数字银行"""
        products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="D",
            income=2500,
            monthly_commitment=500,
            ccris_bucket=3,
            credit_score=520,
            top_n=5
        )
        
        assert len(products) > 0
        
        # 验证主要是数字银行或Fintech
        top_types = [p["type"] for p in products[:3]]
        assert all(t in ["digital_bank", "fintech"] for t in top_types)
        
        # 验证批准概率合理（高风险应较低）
        for product in products:
            assert product["approval_odds"] <= 75
    
    def test_ccris_bucket_affects_approval_odds(self):
        """CCRIS bucket应影响批准概率"""
        # CCRIS Bucket = 0
        products_bucket_0 = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="B+",
            income=5000,
            monthly_commitment=1000,
            ccris_bucket=0,
            credit_score=700,
            top_n=3
        )
        
        # CCRIS Bucket = 2
        products_bucket_2 = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="B+",
            income=5000,
            monthly_commitment=1000,
            ccris_bucket=2,
            credit_score=700,
            top_n=3
        )
        
        # Bucket 0应该有更高的批准概率
        avg_odds_0 = sum(p["approval_odds"] for p in products_bucket_0) / len(products_bucket_0)
        avg_odds_2 = sum(p["approval_odds"] for p in products_bucket_2) / len(products_bucket_2)
        
        assert avg_odds_0 > avg_odds_2
    
    def test_income_filtering(self):
        """低收入应过滤掉高门槛产品"""
        products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="A",
            income=1500,  # 低收入
            monthly_commitment=300,
            ccris_bucket=0,
            credit_score=720,
            top_n=None
        )
        
        # 验证所有产品的min_income <= 1500
        for product in products:
            assert product.get("bank") not in ["Standard Chartered", "Public Bank"]
    
    def test_dynamic_interest_rate_calculation(self):
        """验证动态利率计算逻辑"""
        # A+ 风险应得到最低利率
        products_a_plus = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="A+",
            income=10000,
            monthly_commitment=1000,
            ccris_bucket=0,
            credit_score=800,
            top_n=1
        )
        
        # D 风险应得到较高利率
        products_d = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="D",
            income=2000,
            monthly_commitment=500,
            ccris_bucket=3,
            credit_score=500,
            top_n=1
        )
        
        # A+的利率应显著低于D
        if products_a_plus and products_d:
            assert products_a_plus[0]["interest_rate"] < products_d[0]["interest_rate"]
    
    def test_max_loan_amount_calculation(self):
        """验证最大可贷金额计算"""
        products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="B+",
            income=6000,
            monthly_commitment=1500,
            ccris_bucket=0,
            credit_score=700,
            top_n=1
        )
        
        assert len(products) > 0
        
        # 最大可贷金额应为正数且合理
        assert products[0]["max_loan_amount"] > 0
        assert products[0]["max_loan_amount"] <= 200000  # 不超过产品上限


class TestSMELoanProductMatching:
    """测试SME贷款产品匹配"""
    
    def test_low_brr_matches_traditional_banks(self):
        """低BRR等级(1-3)应匹配传统银行"""
        products = LoanProductMatcher.match_sme_loan_v2(
            brr_grade=2,
            dscr=2.5,
            operating_income=2000000,
            industry_sector="trading",
            ctos_sme_score=750,
            company_age_years=8,
            max_loan_amount=1000000,
            cgc_eligible=True,
            top_n=5
        )
        
        assert len(products) > 0
        
        # 验证高匹配分数
        assert products[0]["match_score"] >= 85
        
        # 验证传统银行
        top_banks = [p["bank"] for p in products[:3]]
        assert any(bank in top_banks for bank in ["Maybank", "Public Bank", "CIMB"])
        
        # 验证低利率
        assert products[0]["interest_rate"] <= 0.070
    
    def test_high_brr_matches_fintech(self):
        """高BRR等级(6-8)应主要推荐Fintech"""
        products = LoanProductMatcher.match_sme_loan_v2(
            brr_grade=7,
            dscr=1.30,
            operating_income=300000,
            industry_sector="fnb",
            ctos_sme_score=600,
            company_age_years=2,
            max_loan_amount=200000,
            cgc_eligible=False,
            top_n=5
        )
        
        assert len(products) > 0
        
        # 验证主要是Fintech
        top_types = [p["type"] for p in products[:3]]
        assert "fintech" in top_types
        
        # 验证利率较高
        assert products[0]["interest_rate"] >= 0.080
    
    def test_industry_restrictions(self):
        """验证行业限制生效"""
        # 测试受限行业（construction）
        products = LoanProductMatcher.match_sme_loan_v2(
            brr_grade=3,
            dscr=1.80,
            operating_income=1000000,
            industry_sector="construction",
            ctos_sme_score=700,
            company_age_years=5,
            max_loan_amount=500000,
            cgc_eligible=True,
            top_n=None
        )
        
        # 验证排除了限制construction的银行
        excluded_banks = ["CIMB", "CapitalBay"]
        for product in products:
            assert product["bank"] not in excluded_banks
    
    def test_dscr_affects_matching(self):
        """DSCR应影响匹配结果"""
        # 高DSCR
        products_high_dscr = LoanProductMatcher.match_sme_loan_v2(
            brr_grade=4,
            dscr=2.5,
            operating_income=800000,
            industry_sector="services",
            ctos_sme_score=680,
            company_age_years=4,
            top_n=3
        )
        
        # 低DSCR
        products_low_dscr = LoanProductMatcher.match_sme_loan_v2(
            brr_grade=4,
            dscr=1.30,
            operating_income=800000,
            industry_sector="services",
            ctos_sme_score=680,
            company_age_years=4,
            top_n=3
        )
        
        # 高DSCR应有更高的匹配分数
        avg_score_high = sum(p["match_score"] for p in products_high_dscr) / len(products_high_dscr)
        avg_score_low = sum(p["match_score"] for p in products_low_dscr) / len(products_low_dscr)
        
        assert avg_score_high > avg_score_low
    
    def test_ctos_sme_score_filtering(self):
        """低CTOS SME分数应过滤掉高要求产品"""
        products = LoanProductMatcher.match_sme_loan_v2(
            brr_grade=5,
            dscr=1.50,
            operating_income=500000,
            industry_sector="retail",
            ctos_sme_score=580,  # 低分数
            company_age_years=3,
            top_n=None
        )
        
        # 验证没有高要求银行
        excluded_banks = ["Public Bank", "Maybank"]
        for product in products:
            assert product["bank"] not in excluded_banks
    
    def test_cgc_eligible_products(self):
        """验证CGC资格标记"""
        products = LoanProductMatcher.match_sme_loan_v2(
            brr_grade=3,
            dscr=1.80,
            operating_income=1500000,
            industry_sector="trading",
            ctos_sme_score=720,
            company_age_years=6,
            cgc_eligible=True,
            top_n=5
        )
        
        # 验证有CGC产品
        cgc_products = [p for p in products if p.get("cgc_eligible")]
        assert len(cgc_products) > 0


class TestProductMatchingEdgeCases:
    """测试边缘情况"""
    
    def test_zero_income_returns_empty(self):
        """零收入应返回空列表"""
        products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="A",
            income=0,
            monthly_commitment=0,
            ccris_bucket=0,
            credit_score=700
        )
        
        assert len(products) == 0
    
    def test_very_high_commitment_limits_products(self):
        """极高债务承诺应限制产品数量"""
        products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="B",
            income=5000,
            monthly_commitment=4500,  # 90% DTI
            ccris_bucket=1,
            credit_score=680
        )
        
        # 应该返回产品，但max_loan_amount会很低
        for product in products:
            assert product["max_loan_amount"] < 50000  # 极低可贷额
    
    def test_top_n_parameter_works(self):
        """验证top_n参数生效"""
        products_top_3 = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="A",
            income=6000,
            monthly_commitment=1000,
            ccris_bucket=0,
            credit_score=720,
            top_n=3
        )
        
        assert len(products_top_3) <= 3
        
        products_all = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="A",
            income=6000,
            monthly_commitment=1000,
            ccris_bucket=0,
            credit_score=720,
            top_n=None
        )
        
        assert len(products_all) >= len(products_top_3)
    
    def test_sorting_by_match_score(self):
        """验证产品按匹配分数排序"""
        products = LoanProductMatcher.match_personal_loan_v2(
            risk_grade="B+",
            income=5000,
            monthly_commitment=1200,
            ccris_bucket=0,
            credit_score=700,
            top_n=None
        )
        
        # 验证降序排列
        for i in range(len(products) - 1):
            assert products[i]["match_score"] >= products[i + 1]["match_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
