"""
FileStorageManager单元测试
"""
import pytest
import os
import tempfile
from datetime import date, datetime
from accounting_app.services.file_storage_manager import AccountingFileStorageManager


class TestFileStorageManager:
    """FileStorageManager核心功能测试"""
    
    def setup_method(self):
        """每个测试前设置"""
        self.test_company_id = 999
    
    def test_generate_bank_statement_path(self):
        """测试银行月结单路径生成"""
        path = AccountingFileStorageManager.generate_bank_statement_path(
            company_id=1,
            bank_name="Maybank",
            account_number="1234567890",
            statement_month="2025-11",
            file_extension="csv"
        )
        
        assert "/companies/1/bank_statements/2025/11/" in path
        assert "Maybank" in path
        # 账户号码后6位（实现中使用后缀）
        assert "567890" in path
        assert path.endswith(".csv")
    
    def test_generate_balance_sheet_path(self):
        """测试资产负债表路径生成"""
        path = AccountingFileStorageManager.generate_balance_sheet_path(
            company_id=1,
            as_of_date=date(2025, 11, 30),
            file_extension="pdf"
        )
        
        assert "/companies/1/reports/balance_sheet/2025/" in path
        assert "balance_sheet" in path
        assert "2025-11-30" in path
        assert path.endswith(".pdf")
    
    def test_generate_profit_loss_path(self):
        """测试损益表路径生成"""
        path = AccountingFileStorageManager.generate_profit_loss_path(
            company_id=1,
            period_start=date(2025, 11, 1),
            period_end=date(2025, 11, 30),
            file_extension="pdf"
        )
        
        assert "/companies/1/reports/profit_loss/2025/11/" in path
        assert "profit_loss" in path
        assert "2025-11-01_to_2025-11-30" in path
    
    def test_generate_management_report_path(self):
        """测试管理报表路径生成"""
        path = AccountingFileStorageManager.generate_management_report_path(
            company_id=1,
            report_month="2025-11",
            file_extension="json"
        )
        
        assert "/companies/1/reports/management/2025/" in path
        assert "management_report" in path
        assert "2025-11" in path
        assert path.endswith(".json")
    
    def test_validate_path_security_valid(self):
        """测试安全路径验证 - 合法路径"""
        # 使用绝对路径进行测试
        import os
        base_path = os.path.join(os.getcwd(), "accounting_data/companies/1/reports/test.pdf")
        
        result = AccountingFileStorageManager.validate_path_security(
            base_path, 
            company_id=1
        )
        
        assert result is True
    
    def test_validate_path_security_cross_tenant(self):
        """测试安全路径验证 - 跨租户攻击防护"""
        # Company 1 试图访问 Company 10 的文件
        malicious_path = "/accounting_data/companies/10/reports/secret.pdf"
        
        result = AccountingFileStorageManager.validate_path_security(
            malicious_path, 
            company_id=1
        )
        
        assert result is False
    
    def test_validate_path_security_traversal(self):
        """测试安全路径验证 - 路径遍历攻击防护"""
        # 尝试使用 ../ 访问父目录
        malicious_path = "/accounting_data/companies/1/../../etc/passwd"
        
        result = AccountingFileStorageManager.validate_path_security(
            malicious_path, 
            company_id=1
        )
        
        assert result is False
    
    def test_validate_path_security_prefix_matching_exploit(self):
        """测试安全路径验证 - 前缀匹配漏洞防护（修复后）"""
        # Company 1 不能访问 Company 10 （即使 "1" 是 "10" 的前缀）
        malicious_path = "/accounting_data/companies/10/bank_statements/file.csv"
        
        result = AccountingFileStorageManager.validate_path_security(
            malicious_path, 
            company_id=1
        )
        
        assert result is False
    
    def test_save_and_read_text_content(self, tmp_path):
        """测试文本内容保存和读取"""
        test_content = "Test CSV Content\nLine 2\nLine 3"
        test_file = tmp_path / "test_file.csv"
        
        # 保存文件
        success = AccountingFileStorageManager.save_text_content(
            str(test_file), 
            test_content
        )
        assert success is True
        assert test_file.exists()
        
        # 读取文件
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == test_content
    
    def test_save_file_content_binary(self, tmp_path):
        """测试二进制内容保存"""
        test_bytes = b"PDF binary content"
        test_file = tmp_path / "test_file.pdf"
        
        # 保存二进制文件
        success = AccountingFileStorageManager.save_file_content(
            str(test_file), 
            test_bytes
        )
        assert success is True
        assert test_file.exists()
        
        # 读取验证
        with open(test_file, 'rb') as f:
            content = f.read()
        
        assert content == test_bytes
    
    def test_delete_file(self, tmp_path):
        """测试文件删除"""
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("Delete me", encoding='utf-8')
        
        assert test_file.exists()
        
        # 删除文件
        success = AccountingFileStorageManager.delete_file(str(test_file))
        
        assert success is True
        assert not test_file.exists()
    
    def test_path_generation_consistency(self):
        """测试路径生成一致性 - 同一输入应产生可预测路径"""
        path1 = AccountingFileStorageManager.generate_bank_statement_path(
            company_id=1,
            bank_name="Maybank",
            account_number="123456",
            statement_month="2025-11",
            file_extension="csv"
        )
        
        path2 = AccountingFileStorageManager.generate_bank_statement_path(
            company_id=1,
            bank_name="Maybank",
            account_number="123456",
            statement_month="2025-11",
            file_extension="csv"
        )
        
        # 路径应该包含相同的公司ID、银行名称、期间
        assert "/companies/1/" in path1
        assert "/companies/1/" in path2
        assert "Maybank" in path1
        assert "Maybank" in path2
