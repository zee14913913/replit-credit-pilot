"""
Test CCRIS Parser
"""
import pytest
from accounting_app.services.data_intake.ccris_parser import CCRISParser


def test_parse_ccris_bucket_from_facilities():
    """测试从设施列表提取bucket"""
    raw_data = {
        "facilities": [
            {"special_account_code": "0"},
            {"special_account_code": "1"},
        ],
        "payment_history": [],
        "text": ""
    }
    
    result = CCRISParser.parse_ccris_bucket(raw_data)
    
    assert result["bucket"] == 1
    assert result["confidence"] >= 0.90


def test_calculate_behavior_score():
    """测试行为分数计算"""
    raw_data = {
        "payment_history": [
            {"status": "on_time"},
            {"status": "on_time"},
            {"status": "late"},
        ],
        "facilities": []
    }
    
    score = CCRISParser.calculate_behavior_score(raw_data)
    
    assert 0 <= score <= 100
    assert score < 100  # 有逾期记录，分数应该被扣


def test_detect_special_flags():
    """测试特殊标记检测"""
    raw_data = {
        "facilities": [
            {"status": "rescheduled"}
        ],
        "text": "bankruptcy proceedings"
    }
    
    flags = CCRISParser.detect_special_flags(raw_data)
    
    assert "rescheduled" in flags
    assert "bankruptcy" in flags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
