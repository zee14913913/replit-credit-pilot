"""
Statement Organizer Service
按Statement Date智能分月归档系统

核心逻辑：
- 以Statement Date为分月标准（不是Due Date）
- 自动创建客户文件夹结构：客户名/年月/信用卡账单
- 每月30号自动统计生成优化方案
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import re


class StatementOrganizer:
    """智能账单归档管理器"""
    
    def __init__(self, base_upload_folder='static/uploads'):
        self.base_folder = base_upload_folder
        
    def parse_statement_date(self, statement_date_str):
        """
        解析statement date字符串
        支持格式：28/10/2025, 2025-10-28, 28 Oct 2025
        
        Returns:
            datetime object
        """
        formats = [
            '%d/%m/%Y',      # 28/10/2025
            '%Y-%m-%d',      # 2025-10-28
            '%d %b %Y',      # 28 Oct 2025
            '%d-%m-%Y',      # 28-10-2025
            '%m/%d/%Y'       # 10/28/2025 (备用)
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(statement_date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"无法解析日期格式: {statement_date_str}")
    
    def get_statement_month_year(self, statement_date):
        """
        根据statement date确定归档月份
        
        Args:
            statement_date: datetime object or string
            
        Returns:
            tuple: (year, month) - 例如 (2025, 10)
        """
        if isinstance(statement_date, str):
            statement_date = self.parse_statement_date(statement_date)
        
        return statement_date.year, statement_date.month
    
    def create_customer_folder_structure(self, customer_name, year, month):
        """
        创建客户文件夹结构
        
        结构：
        uploads/
        └── {customer_name}/
            └── {year}-{month:02d}/
                ├── statements/     (原始账单文件)
                ├── transactions/   (提取的交易数据)
                └── reports/        (生成的报告)
        
        Args:
            customer_name: 客户名称
            year: 年份
            month: 月份
            
        Returns:
            dict: 包含所有文件夹路径的字典
        """
        # 清理客户名称（移除特殊字符）
        safe_customer_name = re.sub(r'[^\w\s-]', '', customer_name).strip().replace(' ', '_')
        
        # 主文件夹路径
        month_folder = f"{year}-{month:02d}"
        base_path = Path(self.base_folder) / safe_customer_name / month_folder
        
        # 创建子文件夹
        folders = {
            'base': str(base_path),
            'statements': str(base_path / 'statements'),
            'transactions': str(base_path / 'transactions'),
            'reports': str(base_path / 'reports')
        }
        
        for folder in folders.values():
            os.makedirs(folder, exist_ok=True)
        
        return folders
    
    def organize_statement(self, file_path, customer_name, statement_date, card_info):
        """
        归档账单文件到正确的月份文件夹
        
        Args:
            file_path: 上传的文件路径
            customer_name: 客户名称
            statement_date: 账单日期（string or datetime）
            card_info: 信用卡信息 (dict with bank_name, last_4_digits)
            
        Returns:
            dict: 归档后的文件路径信息
        """
        # 解析statement date
        if isinstance(statement_date, str):
            stmt_date = self.parse_statement_date(statement_date)
        else:
            stmt_date = statement_date
        
        year, month = self.get_statement_month_year(stmt_date)
        
        # 创建文件夹结构
        folders = self.create_customer_folder_structure(customer_name, year, month)
        
        # 生成新文件名：BankName_Last4Digits_YYYY-MM-DD.pdf
        file_extension = os.path.splitext(file_path)[1]
        safe_bank_name = re.sub(r'[^\w\s-]', '', card_info.get('bank_name', 'BANK')).replace(' ', '_')
        new_filename = f"{safe_bank_name}_{card_info.get('last_4_digits', '0000')}_{stmt_date.strftime('%Y-%m-%d')}{file_extension}"
        
        # 目标路径
        destination = os.path.join(folders['statements'], new_filename)
        
        # 复制文件到归档位置
        shutil.copy2(file_path, destination)
        
        return {
            'original_path': file_path,
            'archived_path': destination,
            'year': year,
            'month': month,
            'month_folder': folders['base'],
            'folders': folders
        }
    
    def get_monthly_statements(self, customer_name, year, month):
        """
        获取指定客户指定月份的所有账单
        
        Args:
            customer_name: 客户名称
            year: 年份
            month: 月份
            
        Returns:
            list: 账单文件路径列表
        """
        safe_customer_name = re.sub(r'[^\w\s-]', '', customer_name).strip().replace(' ', '_')
        month_folder = f"{year}-{month:02d}"
        statements_folder = Path(self.base_folder) / safe_customer_name / month_folder / 'statements'
        
        if not statements_folder.exists():
            return []
        
        statements = []
        for file in statements_folder.iterdir():
            if file.is_file():
                statements.append({
                    'path': str(file),
                    'filename': file.name,
                    'size': file.stat().st_size,
                    'modified': datetime.fromtimestamp(file.stat().st_mtime)
                })
        
        return statements
    
    def should_generate_monthly_report(self, customer_name, year, month):
        """
        检查是否应该生成月度报告
        
        规则：每月30号自动生成
        
        Args:
            customer_name: 客户名称
            year: 年份
            month: 月份
            
        Returns:
            bool: True if should generate report
        """
        today = datetime.now()
        
        # 检查是否是30号或月末
        if today.day >= 30:
            # 检查指定月份的报告是否已存在
            safe_customer_name = re.sub(r'[^\w\s-]', '', customer_name).strip().replace(' ', '_')
            month_folder = f"{year}-{month:02d}"
            reports_folder = Path(self.base_folder) / safe_customer_name / month_folder / 'reports'
            
            if reports_folder.exists():
                # 检查是否已有月度报告
                report_files = list(reports_folder.glob('monthly_report_*.pdf'))
                if not report_files:
                    return True
        
        return False
    
    def get_customer_monthly_summary(self, customer_name, year, month):
        """
        获取客户指定月份的汇总数据
        用于生成优化方案对比
        
        Args:
            customer_name: 客户名称
            year: 年份
            month: 月份
            
        Returns:
            dict: 月度汇总数据
        """
        statements = self.get_monthly_statements(customer_name, year, month)
        
        return {
            'customer_name': customer_name,
            'year': year,
            'month': month,
            'total_statements': len(statements),
            'statements': statements,
            'period': f"{year}-{month:02d}",
            'ready_for_report': len(statements) > 0
        }
    
    def calculate_due_date(self, statement_date, days_offset=21):
        """
        根据statement date计算due date
        默认21天后（标准信用卡还款周期）
        
        Args:
            statement_date: 账单日期
            days_offset: 天数偏移（默认21天）
            
        Returns:
            datetime: due date
        """
        if isinstance(statement_date, str):
            statement_date = self.parse_statement_date(statement_date)
        
        return statement_date + timedelta(days=days_offset)


# 示例用法
if __name__ == "__main__":
    organizer = StatementOrganizer()
    
    # 示例：归档一个账单
    # statement_date = "28/10/2025"
    # card_info = {'bank_name': 'Maybank', 'last_4_digits': '1234'}
    # result = organizer.organize_statement(
    #     'uploads/temp_file.pdf',
    #     'cheok jun yoon',
    #     statement_date,
    #     card_info
    # )
    # print(f"归档完成：{result}")
