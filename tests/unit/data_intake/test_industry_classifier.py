"""
Test Industry Classifier
"""
import pytest
from accounting_app.services.data_intake.industry_classifier import IndustryClassifier


def test_classify_trading_company():
    """测试Trading公司分类"""
    result = IndustryClassifier.classify_industry(
        company_name="ABC Trading Sdn Bhd",
        description="Import and export of electronics"
    )
    
    assert result["industry"] == "trading"
    assert result["risk_level"] == "Medium"
    assert result["confidence"] >= 0.60


def test_classify_fnb_company():
    """测试F&B公司分类"""
    result = IndustryClassifier.classify_industry(
        company_name="Good Food Restaurant",
        description="Catering and food services"
    )
    
    assert result["industry"] == "fnb"
    assert result["risk_level"] == "Medium"


def test_classify_construction_company():
    """测试Construction公司分类（高风险）"""
    result = IndustryClassifier.classify_industry(
        company_name="Build Master Construction",
        description="Civil engineering and building"
    )
    
    assert result["industry"] == "construction"
    assert result["risk_level"] == "High"
    assert result["risk_score"] >= 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
