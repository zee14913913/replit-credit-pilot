"""
PDF报表API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date
from decimal import Decimal


@pytest.mark.integration
class TestPDFReportsAPI:
    """PDF报表端点集成测试"""
    
    def test_balance_sheet_pdf_generation(
        self, 
        client, 
        sample_company, 
        sample_chart_of_accounts
    ):
        """测试Balance Sheet PDF生成"""
        response = client.get(
            "/api/reports/pdf/balance-sheet",
            params={
                "company_id": sample_company.id,
                "period": "2025-11-30"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
        
        # 验证文件名
        content_disposition = response.headers.get("content-disposition", "")
        assert "Balance_Sheet" in content_disposition
        assert sample_company.company_code in content_disposition
    
    def test_profit_loss_pdf_generation(
        self, 
        client, 
        sample_company, 
        sample_journal_entry
    ):
        """测试Profit & Loss PDF生成"""
        response = client.get(
            "/api/reports/pdf/profit-loss",
            params={
                "company_id": sample_company.id,
                "period": "2025-11"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
        
        # 验证文件名
        content_disposition = response.headers.get("content-disposition", "")
        assert "Profit_Loss" in content_disposition
    
    def test_bank_package_pdf_generation(
        self, 
        client, 
        sample_company, 
        sample_journal_entry
    ):
        """测试Bank Package PDF生成"""
        response = client.get(
            "/api/reports/pdf/bank-package",
            params={
                "company_id": sample_company.id,
                "period": "2025-11"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
        
        # 验证文件名包含所有必要信息
        content_disposition = response.headers.get("content-disposition", "")
        assert "Bank_Package" in content_disposition
        assert sample_company.company_code in content_disposition
        assert "2025-11" in content_disposition
    
    def test_invalid_company_returns_404(self, client):
        """测试无效公司ID返回404"""
        response = client.get(
            "/api/reports/pdf/balance-sheet",
            params={
                "company_id": 99999,
                "period": "2025-11-30"
            }
        )
        
        assert response.status_code == 404
        assert "公司不存在" in response.json().get("detail", "")
    
    def test_pdf_preview_structure(
        self, 
        client, 
        sample_company, 
        sample_journal_entry
    ):
        """测试PDF预览数据结构"""
        response = client.get(
            "/api/reports/pdf/preview/balance_sheet",
            params={
                "company_id": sample_company.id,
                "period": "2025-11-30"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "company_info" in data
        assert "balance_sheet_summary" in data
        assert data["company_info"]["company_code"] == sample_company.company_code
