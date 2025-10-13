"""
客户文件夹管理器 - Customer Folder Manager
为每个客户创建12个月份文件夹，并组织原始账单和分类报告
"""

import os
import shutil
from datetime import datetime
from typing import List, Dict
from db.database import get_db


class CustomerFolderManager:
    """客户文件夹管理器"""
    
    def __init__(self, base_dir: str = "static/customer_files"):
        """
        初始化文件夹管理器
        
        Args:
            base_dir: 客户文件的基础目录
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def create_customer_folder_structure(self, customer_id: int, customer_name: str) -> str:
        """
        为客户创建完整的文件夹结构（12个月份）
        
        Args:
            customer_id: 客户ID
            customer_name: 客户全名
            
        Returns:
            客户根文件夹路径
        """
        # 创建客户根文件夹（使用全名）
        safe_name = customer_name.replace(' ', '_').replace('/', '_')
        customer_folder = os.path.join(self.base_dir, f"{customer_id}_{safe_name}")
        os.makedirs(customer_folder, exist_ok=True)
        
        # 创建12个月份文件夹
        current_year = datetime.now().year
        months = [
            '01_January', '02_February', '03_March', '04_April',
            '05_May', '06_June', '07_July', '08_August',
            '09_September', '10_October', '11_November', '12_December'
        ]
        
        for month in months:
            month_folder = os.path.join(customer_folder, f"{current_year}_{month}")
            os.makedirs(month_folder, exist_ok=True)
            
            # 在每个月份文件夹内创建子文件夹
            os.makedirs(os.path.join(month_folder, 'original_statements'), exist_ok=True)
            os.makedirs(os.path.join(month_folder, 'classified_reports'), exist_ok=True)
            os.makedirs(os.path.join(month_folder, 'supplier_invoices'), exist_ok=True)
        
        return customer_folder
    
    def get_month_folder(self, customer_id: int, statement_date: str) -> str:
        """
        获取指定账单日期对应的月份文件夹
        
        Args:
            customer_id: 客户ID
            statement_date: 账单日期 (YYYY-MM-DD)
            
        Returns:
            月份文件夹路径
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
            customer_name = cursor.fetchone()[0]
        
        safe_name = customer_name.replace(' ', '_').replace('/', '_')
        customer_folder = os.path.join(self.base_dir, f"{customer_id}_{safe_name}")
        
        # 解析日期
        date_obj = datetime.strptime(statement_date, '%Y-%m-%d')
        year = date_obj.year
        month_num = date_obj.strftime('%m')
        
        month_names = {
            '01': 'January', '02': 'February', '03': 'March', '04': 'April',
            '05': 'May', '06': 'June', '07': 'July', '08': 'August',
            '09': 'September', '10': 'October', '11': 'November', '12': 'December'
        }
        
        month_folder = os.path.join(
            customer_folder, 
            f"{year}_{month_num}_{month_names[month_num]}"
        )
        
        return month_folder
    
    def organize_statement_files(self, customer_id: int, statement_id: int, 
                                original_pdf_path: str, 
                                classified_report_path: str = None,
                                invoice_paths: List[str] = None) -> Dict[str, str]:
        """
        组织账单文件：将原始PDF和分类报告放在对应的月份文件夹
        
        Args:
            customer_id: 客户ID
            statement_id: 账单ID
            original_pdf_path: 原始PDF路径
            classified_report_path: 分类报告路径（可选）
            invoice_paths: 发票路径列表（可选）
            
        Returns:
            文件组织结果字典
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取账单日期
            cursor.execute('SELECT statement_date FROM statements WHERE id = ?', (statement_id,))
            result = cursor.fetchone()
            if not result or not result[0]:
                return {'error': 'Statement date not found'}
            
            statement_date = result[0]
        
        # 获取月份文件夹
        month_folder = self.get_month_folder(customer_id, statement_date)
        
        # 确保文件夹存在
        os.makedirs(os.path.join(month_folder, 'original_statements'), exist_ok=True)
        os.makedirs(os.path.join(month_folder, 'classified_reports'), exist_ok=True)
        os.makedirs(os.path.join(month_folder, 'supplier_invoices'), exist_ok=True)
        
        result = {}
        
        # 复制原始PDF
        if os.path.exists(original_pdf_path):
            filename = os.path.basename(original_pdf_path)
            dest_path = os.path.join(month_folder, 'original_statements', filename)
            shutil.copy2(original_pdf_path, dest_path)
            result['original_pdf'] = dest_path
        
        # 复制分类报告
        if classified_report_path and os.path.exists(classified_report_path):
            filename = os.path.basename(classified_report_path)
            dest_path = os.path.join(month_folder, 'classified_reports', filename)
            shutil.copy2(classified_report_path, dest_path)
            result['classified_report'] = dest_path
        
        # 复制供应商发票
        if invoice_paths:
            result['invoices'] = []
            for invoice_path in invoice_paths:
                if os.path.exists(invoice_path):
                    filename = os.path.basename(invoice_path)
                    dest_path = os.path.join(month_folder, 'supplier_invoices', filename)
                    shutil.copy2(invoice_path, dest_path)
                    result['invoices'].append(dest_path)
        
        return result


def setup_customer_folders(customer_id: int) -> str:
    """
    为新客户设置文件夹结构（便捷函数）
    
    Args:
        customer_id: 客户ID
        
    Returns:
        客户根文件夹路径
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM customers WHERE id = ?', (customer_id,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Customer {customer_id} not found")
        customer_name = result[0]
    
    manager = CustomerFolderManager()
    return manager.create_customer_folder_structure(customer_id, customer_name)
