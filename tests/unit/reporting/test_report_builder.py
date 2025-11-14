"""
Unit Tests for Loan Report Builder
PHASE 5: 测试报告生成功能
"""
import pytest
from accounting_app.services.reporting import LoanReportBuilder


class TestPersonalLoanReportBuilder:
    """测试个人贷款报告生成"""
    
    def test_build_personal_report_basic(self):
        """测试基本个人贷款报告生成"""
        evaluation_result = {
            "risk_grade": "B+",
            "dti": 0.45,
            "foir": 0.50,
            "ccris_bucket": 0,
            "credit_score": 720,
            "max_loan_amount": 80000,
            "max_emi": 1500,
            "income": 5000,
            "monthly_commitment": 1500,
            "recommended_products": [
                {
                    "bank": "Maybank",
                    "product_name": "Maybank Personal Loan",
                    "match_score": 88.5,
                    "interest_rate": 0.065,
                    "max_loan_amount": 80000,
                    "approval_odds": 85.2
                }
            ]
        }
        
        customer_data = {
            "name": "John Doe",
            "ic_number": "123456-78-9012",
            "age": 35,
            "income": 5000,
            "employment_status": "Permanent",
            "employment_years": 5.0
        }
        
        html = LoanReportBuilder.build_personal_report(
            evaluation_result=evaluation_result,
            customer_data=customer_data
        )
        
        # 验证HTML包含关键元素
        assert "个人贷款评估报告" in html
        assert "John Doe" in html
        assert "B+" in html
        assert "RM 80,000" in html or "80000" in html
        assert "Maybank" in html
        assert len(html) > 5000  # HTML应该较大
    
    def test_report_includes_ai_advisor(self):
        """测试报告包含AI顾问解释"""
        evaluation_result = {
            "risk_grade": "A",
            "dti": 0.30,
            "foir": 0.35,
            "ccris_bucket": 0,
            "credit_score": 780,
            "max_loan_amount": 120000,
            "max_emi": 2000,
            "recommended_products": []
        }
        
        customer_data = {
            "name": "Jane Smith",
            "ic_number": "987654-32-1098",
            "age": 30,
            "income": 7000
        }
        
        html = LoanReportBuilder.build_personal_report(
            evaluation_result=evaluation_result,
            customer_data=customer_data
        )
        
        assert "AI风控顾问分析" in html or "AI Risk Advisor" in html


class TestSMELoanReportBuilder:
    """测试SME贷款报告生成"""
    
    def test_build_sme_report_basic(self):
        """测试基本SME贷款报告生成"""
        evaluation_result = {
            "brr_grade": 3,
            "dscr": 2.2,
            "cashflow_variance": 0.18,
            "ctos_sme_score": 740,
            "industry_sector": "trading",
            "max_loan_amount": 1500000,
            "annual_commitment": 200000,
            "operating_income": 2000000,
            "cgc_eligibility": True,
            "recommended_products": [
                {
                    "bank": "Public Bank",
                    "product_name": "Public Bank SME Term Financing",
                    "match_score": 92.0,
                    "interest_rate": 0.048,
                    "max_loan_amount": 1500000,
                    "approval_odds": 94.5
                }
            ]
        }
        
        customer_data = {
            "company_name": "ABC Trading Sdn Bhd",
            "registration_number": "SSM123456",
            "company_age_years": 8,
            "industry_sector": "trading",
            "employee_count": 25,
            "operating_income": 2000000
        }
        
        html = LoanReportBuilder.build_sme_report(
            evaluation_result=evaluation_result,
            customer_data=customer_data
        )
        
        # 验证HTML包含关键元素
        assert "SME贷款评估报告" in html
        assert "ABC Trading" in html
        assert "BRR" in html or "brr" in html.lower()
        assert "DSCR" in html
        assert "Public Bank" in html
        assert len(html) > 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
