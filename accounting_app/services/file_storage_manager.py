"""
Accounting App - Enterprise File Storage Manager
会计系统 - 企业级文件存储管理器

提供多租户隔离、标准化路径生成、类型化存储功能
Provides multi-tenant isolation, standardized path generation, typed storage
"""
import os
import re
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, List
from decimal import Decimal


class AccountingFileStorageManager:
    """
    会计系统文件存储管理器
    
    核心特性：
    1. 多租户隔离（按company_id）
    2. 标准化路径生成
    3. 类型化文件存储
    4. 自动目录创建
    5. 安全路径验证
    """
    
    BASE_DIR = "/home/runner/workspace/accounting_data/companies"
    
    FILE_TYPES = {
        'bank_statement': 'bank_statements',
        'pos_report': 'pos_reports',
        'supplier_invoice': 'invoices/supplier',
        'purchase_invoice': 'invoices/purchase',
        'sales_invoice': 'invoices/sales',
        'management_report': 'reports/management',
        'balance_sheet': 'reports/balance_sheet',
        'profit_loss': 'reports/profit_loss',
        'bank_package': 'reports/bank_package',
        'aging_report': 'reports/aging',
        'trial_balance': 'reports/trial_balance',
        'audit_report': 'audit_reports',
        'tax_document': 'tax_documents'
    }
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除特殊字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        filename = re.sub(r'[^\w\s.-]', '', filename)
        filename = filename.replace(' ', '_')
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('_')
        return filename
    
    @staticmethod
    def ensure_directory(file_path: str) -> str:
        """
        确保文件路径的目录存在
        
        Args:
            file_path: 完整文件路径
            
        Returns:
            目录路径
        """
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        return directory
    
    @staticmethod
    def generate_bank_statement_path(
        company_id: int,
        bank_name: str,
        account_number: str,
        statement_month: str,
        file_extension: str = 'csv'
    ) -> str:
        """
        生成银行月结单存储路径
        
        Args:
            company_id: 公司ID
            bank_name: 银行名称
            account_number: 账户号码
            statement_month: 账单月份（YYYY-MM格式）
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
            
        Example:
            >>> generate_bank_statement_path(1, 'Maybank', '123456789', '2025-01', 'csv')
            '/accounting_data/companies/1/bank_statements/2025/01/company1_bank_Maybank_123456789_2025-01.csv'
        """
        clean_bank = AccountingFileStorageManager.sanitize_filename(bank_name)
        clean_account = account_number.replace('-', '').replace(' ', '')[-6:]
        
        year, month = statement_month.split('-')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"company{company_id}_bank_{clean_bank}_{clean_account}_{statement_month}_{timestamp}.{file_extension}"
        
        path = os.path.join(
            AccountingFileStorageManager.BASE_DIR,
            str(company_id),
            AccountingFileStorageManager.FILE_TYPES['bank_statement'],
            year,
            month,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_pos_report_path(
        company_id: int,
        report_date: date,
        file_extension: str = 'csv'
    ) -> str:
        """
        生成POS报表存储路径
        
        Args:
            company_id: 公司ID
            report_date: 报表日期
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
        """
        year = report_date.strftime('%Y')
        month = report_date.strftime('%m')
        date_str = report_date.strftime('%Y-%m-%d')
        
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"company{company_id}_pos_{date_str}_{timestamp}.{file_extension}"
        
        path = os.path.join(
            AccountingFileStorageManager.BASE_DIR,
            str(company_id),
            AccountingFileStorageManager.FILE_TYPES['pos_report'],
            year,
            month,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_invoice_path(
        company_id: int,
        invoice_type: str,
        invoice_number: str,
        invoice_date: date,
        supplier_customer_name: str,
        file_extension: str = 'pdf'
    ) -> str:
        """
        生成发票存储路径
        
        Args:
            company_id: 公司ID
            invoice_type: 发票类型（'supplier', 'purchase', 'sales'）
            invoice_number: 发票编号
            invoice_date: 发票日期
            supplier_customer_name: 供应商/客户名称
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
        """
        clean_party = AccountingFileStorageManager.sanitize_filename(supplier_customer_name)[:30]
        clean_invoice_num = AccountingFileStorageManager.sanitize_filename(invoice_number)
        
        year = invoice_date.strftime('%Y')
        month = invoice_date.strftime('%m')
        date_str = invoice_date.strftime('%Y-%m-%d')
        
        filename = f"company{company_id}_{invoice_type}_invoice_{clean_invoice_num}_{clean_party}_{date_str}.{file_extension}"
        
        invoice_dir = AccountingFileStorageManager.FILE_TYPES.get(
            f'{invoice_type}_invoice',
            'invoices/misc'
        )
        
        path = os.path.join(
            AccountingFileStorageManager.BASE_DIR,
            str(company_id),
            invoice_dir,
            year,
            month,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_management_report_path(
        company_id: int,
        report_month: str,
        file_extension: str = 'json'
    ) -> str:
        """
        生成Management Report存储路径
        
        Args:
            company_id: 公司ID
            report_month: 报告月份（YYYY-MM格式）
            file_extension: 文件扩展名（json或pdf）
            
        Returns:
            标准化文件路径
        """
        year, month = report_month.split('-')
        
        filename = f"company{company_id}_management_report_{report_month}.{file_extension}"
        
        path = os.path.join(
            AccountingFileStorageManager.BASE_DIR,
            str(company_id),
            AccountingFileStorageManager.FILE_TYPES['management_report'],
            year,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_balance_sheet_path(
        company_id: int,
        as_of_date: date,
        file_extension: str = 'pdf'
    ) -> str:
        """
        生成Balance Sheet PDF存储路径
        
        Args:
            company_id: 公司ID
            as_of_date: 截止日期
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
        """
        year = as_of_date.strftime('%Y')
        date_str = as_of_date.strftime('%Y-%m-%d')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"company{company_id}_balance_sheet_{date_str}_{timestamp}.{file_extension}"
        
        path = os.path.join(
            AccountingFileStorageManager.BASE_DIR,
            str(company_id),
            AccountingFileStorageManager.FILE_TYPES['balance_sheet'],
            year,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_profit_loss_path(
        company_id: int,
        period_start: date,
        period_end: date,
        file_extension: str = 'pdf'
    ) -> str:
        """
        生成Profit & Loss Report PDF存储路径
        
        Args:
            company_id: 公司ID
            period_start: 期间开始日期
            period_end: 期间结束日期
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
        """
        year = period_end.strftime('%Y')
        month = period_end.strftime('%m')
        
        start_str = period_start.strftime('%Y-%m-%d')
        end_str = period_end.strftime('%Y-%m-%d')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"company{company_id}_profit_loss_{start_str}_to_{end_str}_{timestamp}.{file_extension}"
        
        path = os.path.join(
            AccountingFileStorageManager.BASE_DIR,
            str(company_id),
            AccountingFileStorageManager.FILE_TYPES['profit_loss'],
            year,
            month,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_bank_package_path(
        company_id: int,
        package_date: date,
        file_extension: str = 'pdf'
    ) -> str:
        """
        生成Bank Package PDF存储路径
        
        Args:
            company_id: 公司ID
            package_date: 包裹生成日期
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
        """
        year = package_date.strftime('%Y')
        date_str = package_date.strftime('%Y-%m-%d')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"company{company_id}_bank_package_{date_str}_{timestamp}.{file_extension}"
        
        path = os.path.join(
            AccountingFileStorageManager.BASE_DIR,
            str(company_id),
            AccountingFileStorageManager.FILE_TYPES['bank_package'],
            year,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def save_file_content(
        file_path: str,
        content: bytes,
        create_dirs: bool = True
    ) -> bool:
        """
        保存文件内容（从bytes）
        
        Args:
            file_path: 目标路径
            content: 文件内容（bytes）
            create_dirs: 是否自动创建目录
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if create_dirs:
                AccountingFileStorageManager.ensure_directory(file_path)
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error saving file content: {str(e)}")
            return False
    
    @staticmethod
    def save_text_content(
        file_path: str,
        content: str,
        create_dirs: bool = True
    ) -> bool:
        """
        保存文本文件内容
        
        Args:
            file_path: 目标路径
            content: 文件内容（str）
            create_dirs: 是否自动创建目录
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if create_dirs:
                AccountingFileStorageManager.ensure_directory(file_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error saving text content: {str(e)}")
            return False
    
    @staticmethod
    def copy_file(
        source_path: str,
        destination_path: str,
        create_dirs: bool = True
    ) -> bool:
        """
        复制文件到指定位置
        
        Args:
            source_path: 源文件路径
            destination_path: 目标路径
            create_dirs: 是否自动创建目录
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if create_dirs:
                AccountingFileStorageManager.ensure_directory(destination_path)
            
            shutil.copy2(source_path, destination_path)
            
            return True
        except Exception as e:
            print(f"Error copying file: {str(e)}")
            return False
    
    @staticmethod
    def delete_file(file_path: str, backup: bool = False) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            backup: 是否先备份（accounting系统默认不备份，因为有数据库记录）
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if not os.path.exists(file_path):
                return True
            
            if backup:
                backup_dir = os.path.join(
                    AccountingFileStorageManager.BASE_DIR,
                    '_backups',
                    datetime.now().strftime('%Y-%m-%d')
                )
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%H%M%S')
                backup_filename = f"{timestamp}_{os.path.basename(file_path)}"
                backup_path = os.path.join(backup_dir, backup_filename)
                shutil.copy2(file_path, backup_path)
            
            os.remove(file_path)
            
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    @staticmethod
    def list_company_files(
        company_id: int,
        file_type: Optional[str] = None
    ) -> List[Dict]:
        """
        列出公司的所有文件
        
        Args:
            company_id: 公司ID
            file_type: 可选，文件类型过滤
            
        Returns:
            文件信息列表
        """
        company_dir = os.path.join(AccountingFileStorageManager.BASE_DIR, str(company_id))
        
        if not os.path.exists(company_dir):
            return []
        
        if file_type and file_type in AccountingFileStorageManager.FILE_TYPES:
            search_dir = os.path.join(company_dir, AccountingFileStorageManager.FILE_TYPES[file_type])
        else:
            search_dir = company_dir
        
        files = []
        for root, dirs, filenames in os.walk(search_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                try:
                    stat = os.stat(file_path)
                    files.append({
                        'path': file_path.replace('\\', '/'),
                        'filename': filename,
                        'size': stat.st_size,
                        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except:
                    continue
        
        files.sort(key=lambda x: x['modified_at'], reverse=True)
        return files
    
    @staticmethod
    def get_storage_stats(company_id: int) -> Dict:
        """
        获取公司的存储统计信息
        
        Args:
            company_id: 公司ID
            
        Returns:
            统计信息字典
        """
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'by_type': {}
        }
        
        company_dir = os.path.join(AccountingFileStorageManager.BASE_DIR, str(company_id))
        
        if not os.path.exists(company_dir):
            return stats
        
        for file_type, type_dir in AccountingFileStorageManager.FILE_TYPES.items():
            full_path = os.path.join(company_dir, type_dir)
            if os.path.exists(full_path):
                files = list(Path(full_path).rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                file_size = sum(f.stat().st_size for f in files if f.is_file())
                
                stats['by_type'][file_type] = {
                    'count': file_count,
                    'size_mb': round(file_size / 1024 / 1024, 2)
                }
                
                stats['total_files'] += file_count
                stats['total_size_mb'] += file_size / 1024 / 1024
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats
    
    @staticmethod
    def validate_path_security(file_path: str, company_id: int) -> bool:
        """
        验证路径安全性（防止路径遍历攻击和跨租户访问）
        
        使用os.path.commonpath确保文件严格在公司目录内，
        避免prefix-matching导致的company_id=1访问company_id=10文件的问题
        
        Args:
            file_path: 待验证的文件路径
            company_id: 公司ID
            
        Returns:
            安全返回True，否则返回False
        """
        try:
            abs_path = os.path.abspath(file_path)
            expected_base = os.path.abspath(
                os.path.join(AccountingFileStorageManager.BASE_DIR, str(company_id))
            )
            
            # 使用commonpath确保两个路径的公共父路径就是expected_base
            common = os.path.commonpath([abs_path, expected_base])
            
            # 公共路径必须严格等于expected_base（公司目录）
            if common != expected_base:
                return False
            
            # abs_path必须在expected_base内部或等于expected_base
            # 添加os.sep确保"/companies/1"不匹配"/companies/10/file"
            return (abs_path == expected_base or 
                    abs_path.startswith(expected_base + os.sep))
        except (ValueError, TypeError):
            # commonpath在路径不兼容时会抛出ValueError（如不同驱动器）
            return False


def create_file_storage_manager():
    """工厂函数：创建FileStorageManager实例"""
    return AccountingFileStorageManager()
