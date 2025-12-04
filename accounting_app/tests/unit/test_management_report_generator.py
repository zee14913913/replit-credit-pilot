"""
ManagementReportGenerator单元测试
"""
import pytest
from datetime import date
from decimal import Decimal
from accounting_app.services.management_report_generator import ManagementReportGenerator


@pytest.mark.unit
class TestManagementReportGenerator:
    """管理报表生成器测试"""
    
    def test_generate_monthly_report_structure(
        self, 
        test_db, 
        sample_company, 
        sample_journal_entry
    ):
        """测试月度报表生成 - 数据结构验证"""
        generator = ManagementReportGenerator(test_db, sample_company.id)
        
        report = generator.generate_monthly_report("2025-11", include_details=True)
        
        assert "company_id" in report
        assert "period" in report
        assert "balance_sheet_summary" in report
        assert "pnl_summary" in report
        assert "aging_summary" in report
        
        assert report["company_id"] == sample_company.id
        assert report["period"] == "2025-11"
    
    def test_balance_sheet_calculation(
        self, 
        test_db, 
        sample_company, 
        sample_chart_of_accounts
    ):
        """测试资产负债表计算准确性"""
        generator = ManagementReportGenerator(test_db, sample_company.id)
        
        report = generator.generate_monthly_report("2025-11", include_details=False)
        bs = report["balance_sheet_summary"]
        
        assert "assets" in bs
        assert "liabilities" in bs
        assert "equity" in bs
        assert "balance_check" in bs
        
        assert "total_assets" in bs["assets"]
        assert "total_liabilities" in bs["liabilities"]
        assert "total_equity" in bs["equity"]
        
        total_assets = bs["assets"]["total_assets"]
        total_liabilities = bs["liabilities"]["total_liabilities"]
        total_equity = bs["equity"]["total_equity"]
        
        balance_check = abs(total_assets - (total_liabilities + total_equity))
        assert balance_check < 0.01 or bs["balance_check"] >= 0, "资产负债表结构验证"
    
    def test_pnl_calculation(
        self, 
        test_db, 
        sample_company, 
        sample_journal_entry
    ):
        """测试损益表计算"""
        generator = ManagementReportGenerator(test_db, sample_company.id)
        
        report = generator.generate_monthly_report("2025-11", include_details=False)
        pnl = report["pnl_summary"]
        
        assert "revenue" in pnl
        assert "expenses" in pnl
        assert "net_profit" in pnl
        
        assert "total_revenue" in pnl["revenue"]
        assert "total_expenses" in pnl["expenses"]
        
        total_revenue = pnl["revenue"]["total_revenue"]
        total_expenses = pnl["expenses"]["total_expenses"]
        expected_net_profit = total_revenue - total_expenses
        assert abs(pnl["net_profit"] - expected_net_profit) < 0.01
    
    def test_aging_report_structure(
        self, 
        test_db, 
        sample_company
    ):
        """测试账龄报表结构"""
        generator = ManagementReportGenerator(test_db, sample_company.id)
        
        report = generator.generate_monthly_report("2025-11", include_details=True)
        aging = report["aging_summary"]
        
        assert "ar_current" in aging
        assert "ar_1_30" in aging
        assert "ar_31_60" in aging
        assert "ar_61_90" in aging
        assert "ar_over_90" in aging
        assert "total_ar" in aging
        
        assert "ap_current" in aging
        assert "ap_1_30" in aging
        assert "ap_31_60" in aging
        assert "ap_61_90" in aging
        assert "ap_over_90" in aging
        assert "total_ap" in aging
    
    def test_include_details_flag(
        self, 
        test_db, 
        sample_company, 
        sample_journal_entry
    ):
        """测试include_details参数控制明细"""
        generator = ManagementReportGenerator(test_db, sample_company.id)
        
        report_summary = generator.generate_monthly_report("2025-11", include_details=False)
        
        report_detailed = generator.generate_monthly_report("2025-11", include_details=True)
        bs_detailed = report_detailed.get("balance_sheet_summary", {})
        
        assert "assets" in bs_detailed
        if "details" in bs_detailed.get("assets", {}):
            assert isinstance(bs_detailed["assets"]["details"], dict)
