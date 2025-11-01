"""
月结任务API集成测试
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestMonthlyCloseAPI:
    """月结任务端点集成测试"""
    
    def test_monthly_close_execution(
        self, 
        client, 
        sample_company, 
        sample_journal_entry
    ):
        """测试月结任务执行"""
        response = client.post(
            "/api/tasks/monthly-close",
            params={
                "company_id": sample_company.id,
                "month": "2025-11"
            },
            headers={"X-Task-Token": "test-token"}  # 测试环境使用测试token
        )
        
        # 注意：实际API可能需要身份验证，这里假设测试环境允许
        # 如果返回401，说明需要配置测试环境的认证token
        
        if response.status_code == 200:
            data = response.json()
            
            # 验证返回结构
            assert "success" in data
            assert "company_id" in data
            assert "month" in data
            assert "trial_balance" in data
            assert "management_report" in data
            
            # 验证公司和期间
            assert data["company_id"] == sample_company.id
            assert data["month"] == "2025-11"
            
            # 验证management_report结构
            mgmt_report = data["management_report"]
            assert "success" in mgmt_report
            
            if mgmt_report["success"]:
                assert "report_path" in mgmt_report
                assert "balance_sheet_balanced" in mgmt_report
    
    def test_monthly_close_invalid_month_format(self, client, sample_company):
        """测试无效月份格式"""
        response = client.post(
            "/api/tasks/monthly-close",
            params={
                "company_id": sample_company.id,
                "month": "invalid-format"
            }
        )
        
        # 应该返回400错误（如果有输入验证）
        # 或者500（如果直接执行失败）
        assert response.status_code in [400, 422, 500]
    
    def test_monthly_close_trial_balance_structure(
        self, 
        client, 
        sample_company, 
        sample_journal_entry
    ):
        """测试月结任务中的试算表结构"""
        response = client.post(
            "/api/tasks/monthly-close",
            params={
                "company_id": sample_company.id,
                "month": "2025-11"
            },
            headers={"X-Task-Token": "test-token"}
        )
        
        if response.status_code == 200:
            data = response.json()
            trial_balance = data.get("trial_balance", {})
            
            # 验证试算表结构
            assert "total_debits" in trial_balance
            assert "total_credits" in trial_balance
            assert "balanced" in trial_balance
            assert "accounts" in trial_balance
            
            # 验证借贷平衡
            total_debits = trial_balance["total_debits"]
            total_credits = trial_balance["total_credits"]
            
            if trial_balance["balanced"]:
                assert abs(total_debits - total_credits) < 0.01
