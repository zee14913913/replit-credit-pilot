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
        
        # 验证报表结构
        assert "company_info" in report
        assert "period" in report
        assert "balance_sheet_summary" in report
        assert "pnl_summary" in report
        assert "aging_summary" in report
        
        # 验证公司信息
        assert report["company_info"]["company_name"] == sample_company.company_name
        assert report["company_info"]["company_code"] == sample_company.company_code
        
        # 验证期间
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
        
        # 验证资产负债表基本结构
        assert "total_assets" in bs
        assert "total_liabilities" in bs
        assert "total_equity" in bs
        assert "balance_check" in bs
        
        # 验证会计等式：Assets = Liabilities + Equity
        total_assets = bs["total_assets"]
        total_liabilities = bs["total_liabilities"]
        total_equity = bs["total_equity"]
        
        balance_check = abs(total_assets - (total_liabilities + total_equity))
        assert balance_check < 0.01, "资产负债表不平衡"
    
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
        
        # 验证损益表结构
        assert "total_revenue" in pnl
        assert "total_expenses" in pnl
        assert "net_profit" in pnl
        assert "gross_margin" in pnl
        
        # 验证净利润计算
        expected_net_profit = pnl["total_revenue"] - pnl["total_expenses"]
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
        
        # 验证账龄报表包含AR和AP
        assert "accounts_receivable" in aging
        assert "accounts_payable" in aging
        
        ar = aging["accounts_receivable"]
        ap = aging["accounts_payable"]
        
        # 验证账龄分段
        for aging_data in [ar, ap]:
            assert "current" in aging_data
            assert "30_days" in aging_data
            assert "60_days" in aging_data
            assert "90_days" in aging_data
            assert "over_90_days" in aging_data
            assert "total" in aging_data
    
    def test_include_details_flag(
        self, 
        test_db, 
        sample_company, 
        sample_journal_entry
    ):
        """测试include_details参数控制明细"""
        generator = ManagementReportGenerator(test_db, sample_company.id)
        
        # 不包含明细
        report_summary = generator.generate_monthly_report("2025-11", include_details=False)
        assert "details" not in report_summary.get("balance_sheet_summary", {})
        
        # 包含明细
        report_detailed = generator.generate_monthly_report("2025-11", include_details=True)
        bs_detailed = report_detailed.get("balance_sheet_summary", {})
        
        # 如果有明细，验证结构
        if "details" in bs_detailed:
            assert "assets" in bs_detailed["details"]
            assert "liabilities" in bs_detailed["details"]
