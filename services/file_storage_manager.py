"""
统一文件存储管理服务
Unified File Storage Manager Service

提供标准化的文件路径生成、目录管理、文件操作功能
"""
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

class FileStorageManager:
    """
    文件存储管理器
    
    核心功能:
    1. 标准化路径生成
    2. 目录自动创建
    3. 文件操作封装
    4. 路径验证
    """
    
    # 基础路径配置
    BASE_DIR = "static/uploads/customers"
    
    # 文件类型目录映射
    FILE_TYPES = {
        'credit_card': 'credit_cards',
        'savings': 'savings',
        'payment_receipt': 'receipts/payment_receipts',
        'merchant_receipt': 'receipts/merchant_receipts',
        'supplier_invoice': 'invoices/supplier',
        'customer_invoice': 'invoices/customer',
        'monthly_report': 'reports/monthly',
        'annual_report': 'reports/annual',
        'loan_application': 'loans/applications',
        'ctos_report': 'loans/ctos_reports',
        'contract': 'documents/contracts',
        'identification': 'documents/identification'
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
        # 移除或替换特殊字符
        filename = re.sub(r'[^\w\s.-]', '', filename)
        # 将空格替换为下划线
        filename = filename.replace(' ', '_')
        # 移除连续的下划线
        filename = re.sub(r'_+', '_', filename)
        # 移除开头和结尾的下划线
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
    def generate_credit_card_path(
        customer_code: str,
        bank_name: str,
        card_last4: str,
        statement_date: datetime,
        file_extension: str = 'pdf'
    ) -> str:
        """
        生成信用卡账单存储路径
        
        Args:
            customer_code: 客户代码 (例如: Be_rich_CCC)
            bank_name: 银行名称 (例如: Maybank)
            card_last4: 卡号后4位
            statement_date: 账单日期
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
            
        Example:
            >>> generate_credit_card_path('Be_rich_CCC', 'Maybank', '5678', datetime(2025, 10, 15))
            'static/uploads/customers/Be_rich_CCC/credit_cards/Maybank/2025-10/Maybank_5678_2025-10-15.pdf'
        """
        # 清理银行名称
        clean_bank = FileStorageManager.sanitize_filename(bank_name)
        
        # 生成年月目录
        year_month = statement_date.strftime('%Y-%m')
        
        # 生成文件名：银行名_日期.pdf（不包含卡号）
        date_str = statement_date.strftime('%Y-%m-%d')
        filename = f"{clean_bank}_{date_str}.{file_extension}"
        
        # 拼接完整路径
        path = os.path.join(
            FileStorageManager.BASE_DIR,
            customer_code,
            FileStorageManager.FILE_TYPES['credit_card'],
            clean_bank,
            year_month,
            filename
        )
        
        # 转换为正斜杠（跨平台兼容）
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_savings_path(
        customer_code: str,
        bank_name: str,
        account_num: str,
        statement_date: datetime,
        file_extension: str = 'pdf'
    ) -> str:
        """
        生成储蓄账户月结单存储路径
        
        Args:
            customer_code: 客户代码
            bank_name: 银行名称
            account_num: 账户号码或标识
            statement_date: 月结单日期
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
        """
        clean_bank = FileStorageManager.sanitize_filename(bank_name)
        year_month = statement_date.strftime('%Y-%m')
        date_str = statement_date.strftime('%Y-%m-%d')
        filename = f"{clean_bank}_{account_num}_{date_str}.{file_extension}"
        
        path = os.path.join(
            FileStorageManager.BASE_DIR,
            customer_code,
            FileStorageManager.FILE_TYPES['savings'],
            clean_bank,
            year_month,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_receipt_path(
        customer_code: str,
        receipt_date: datetime,
        merchant: str,
        amount: float,
        card_last4: str,
        file_extension: str = 'jpg'
    ) -> str:
        """
        生成收据存储路径
        
        Args:
            customer_code: 客户代码
            receipt_date: 收据日期
            merchant: 商户名称
            amount: 金额
            card_last4: 卡号后4位
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
        """
        clean_merchant = FileStorageManager.sanitize_filename(merchant)[:30]  # 限制长度
        year_month = receipt_date.strftime('%Y-%m')
        date_str = receipt_date.strftime('%Y-%m-%d')
        filename = f"{date_str}_{clean_merchant}_{amount:.2f}_{card_last4}.{file_extension}"
        
        path = os.path.join(
            FileStorageManager.BASE_DIR,
            customer_code,
            FileStorageManager.FILE_TYPES['payment_receipt'],
            year_month,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_invoice_path(
        customer_code: str,
        invoice_type: str,  # 'supplier' or 'customer'
        party_name: str,
        invoice_number: str,
        invoice_date: datetime,
        file_extension: str = 'pdf'
    ) -> str:
        """
        生成发票存储路径
        
        Args:
            customer_code: 客户代码
            invoice_type: 发票类型 ('supplier' 或 'customer')
            party_name: 供应商/客户名称
            invoice_number: 发票编号
            invoice_date: 发票日期
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
        """
        clean_party = FileStorageManager.sanitize_filename(party_name)
        year_month = invoice_date.strftime('%Y-%m')
        date_str = invoice_date.strftime('%Y-%m-%d')
        filename = f"Invoice_{clean_party}_{invoice_number}_{date_str}.{file_extension}"
        
        invoice_dir = FileStorageManager.FILE_TYPES.get(
            f'{invoice_type}_invoice',
            'invoices/misc'
        )
        
        path = os.path.join(
            FileStorageManager.BASE_DIR,
            customer_code,
            invoice_dir,
            year_month,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_report_path(
        customer_code: str,
        report_type: str,  # 'monthly' or 'annual'
        report_date: datetime,
        file_extension: str = 'pdf'
    ) -> str:
        """
        生成报告存储路径
        
        Args:
            customer_code: 客户代码
            report_type: 报告类型
            report_date: 报告日期
            file_extension: 文件扩展名
            
        Returns:
            标准化文件路径
        """
        report_dir = FileStorageManager.FILE_TYPES.get(f'{report_type}_report', 'reports/custom')
        
        if report_type == 'monthly':
            year_month = report_date.strftime('%Y-%m')
            filename = f"Monthly_Report_{year_month}.{file_extension}"
            subdir = year_month
        elif report_type == 'annual':
            year = report_date.strftime('%Y')
            filename = f"Annual_Report_{year}.{file_extension}"
            subdir = year
        else:
            timestamp = report_date.strftime('%Y%m%d_%H%M%S')
            filename = f"{report_type}_{timestamp}.{file_extension}"
            subdir = report_date.strftime('%Y-%m')
        
        path = os.path.join(
            FileStorageManager.BASE_DIR,
            customer_code,
            report_dir,
            subdir,
            filename
        )
        
        return path.replace('\\', '/')
    
    @staticmethod
    def save_file(source_path: str, destination_path: str, create_dirs: bool = True) -> bool:
        """
        保存文件到指定位置
        
        Args:
            source_path: 源文件路径（临时上传路径）
            destination_path: 目标路径（标准化路径）
            create_dirs: 是否自动创建目录
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            # 确保目标目录存在
            if create_dirs:
                FileStorageManager.ensure_directory(destination_path)
            
            # 复制文件
            shutil.copy2(source_path, destination_path)
            
            return True
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return False
    
    @staticmethod
    def move_file(old_path: str, new_path: str, create_dirs: bool = True) -> bool:
        """
        移动文件到新位置
        
        Args:
            old_path: 原路径
            new_path: 新路径
            create_dirs: 是否自动创建目录
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if not os.path.exists(old_path):
                print(f"Source file not found: {old_path}")
                return False
            
            # 确保目标目录存在
            if create_dirs:
                FileStorageManager.ensure_directory(new_path)
            
            # 移动文件
            shutil.move(old_path, new_path)
            
            return True
        except Exception as e:
            print(f"Error moving file: {str(e)}")
            return False
    
    @staticmethod
    def delete_file(file_path: str, backup: bool = True) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            backup: 是否先备份
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if not os.path.exists(file_path):
                return True  # 文件不存在，视为成功
            
            # 备份到backup目录
            if backup:
                backup_dir = 'static/backup_deleted_files'
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f"{timestamp}_{os.path.basename(file_path)}"
                backup_path = os.path.join(backup_dir, backup_filename)
                shutil.copy2(file_path, backup_path)
            
            # 删除文件
            os.remove(file_path)
            
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            存在返回True，否则返回False
        """
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        获取文件大小（字节）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节），文件不存在返回0
        """
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    @staticmethod
    def list_customer_files(customer_code: str, file_type: Optional[str] = None) -> list:
        """
        列出客户的所有文件
        
        Args:
            customer_code: 客户代码
            file_type: 可选，文件类型过滤
            
        Returns:
            文件路径列表
        """
        customer_dir = os.path.join(FileStorageManager.BASE_DIR, customer_code)
        
        if not os.path.exists(customer_dir):
            return []
        
        if file_type and file_type in FileStorageManager.FILE_TYPES:
            search_dir = os.path.join(customer_dir, FileStorageManager.FILE_TYPES[file_type])
        else:
            search_dir = customer_dir
        
        files = []
        for root, dirs, filenames in os.walk(search_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(file_path.replace('\\', '/'))
        
        return files
    
    @staticmethod
    def get_storage_stats(customer_code: str) -> dict:
        """
        获取客户的存储统计信息
        
        Args:
            customer_code: 客户代码
            
        Returns:
            统计信息字典
        """
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'by_type': {}
        }
        
        customer_dir = os.path.join(FileStorageManager.BASE_DIR, customer_code)
        
        if not os.path.exists(customer_dir):
            return stats
        
        for file_type, type_dir in FileStorageManager.FILE_TYPES.items():
            full_path = os.path.join(customer_dir, type_dir)
            if os.path.exists(full_path):
                files = list(Path(full_path).rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                file_size = sum(f.stat().st_size for f in files if f.is_file())
                
                stats['by_type'][file_type] = {
                    'count': file_count,
                    'size_mb': file_size / 1024 / 1024
                }
                
                stats['total_files'] += file_count
                stats['total_size_mb'] += file_size / 1024 / 1024
        
        return stats


# 便捷函数（向后兼容）
def get_credit_card_statement_path(customer_code, bank_name, card_last4, statement_date):
    """便捷函数：生成信用卡账单路径"""
    return FileStorageManager.generate_credit_card_path(
        customer_code, bank_name, card_last4, statement_date
    )

def get_savings_statement_path(customer_code, bank_name, account_num, statement_date):
    """便捷函数：生成储蓄账户路径"""
    return FileStorageManager.generate_savings_path(
        customer_code, bank_name, account_num, statement_date
    )

def get_receipt_path(customer_code, receipt_date, merchant, amount, card_last4, file_ext='jpg'):
    """便捷函数：生成收据路径"""
    return FileStorageManager.generate_receipt_path(
        customer_code, receipt_date, merchant, amount, card_last4, file_ext
    )
