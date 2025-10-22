"""
Statement Organizer Service
智能文件分类归档系统

新层级结构：
客户名/
  ├── credit_cards/      (信用卡类别)
  │   ├── Maybank/      (银行1)
  │   │   ├── 2024-11/  (月份1)
  │   │   └── 2024-12/  (月份2)
  │   └── CIMB/         (银行2)
  │       └── 2025-01/
  └── savings/          (储蓄/来往账户类别)
      ├── GX_Bank/
      │   └── 2024-12/
      └── Maybank/
          └── 2025-01/
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import re


class StatementOrganizer:
    """智能账单归档管理器 - 按客户/类别/银行/月份四级分类"""
    
    # 账单类别常量
    CATEGORY_CREDIT_CARD = 'credit_cards'
    CATEGORY_SAVINGS = 'savings'
    
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
    
    def sanitize_name(self, name):
        """
        清理名称，移除特殊字符并标准化大小写
        银行名称统一使用首字母大写格式（Title Case）
        """
        # 清理特殊字符
        clean_name = re.sub(r'[^\w\s-]', '', name).strip()
        # 标准化大小写：每个单词首字母大写
        clean_name = clean_name.title()
        # 替换空格为下划线
        return clean_name.replace(' ', '_')
    
    def create_folder_structure(self, customer_name, category, bank_name, year, month):
        """
        创建四级文件夹结构
        
        结构：
        uploads/
        └── {customer_name}/
            ├── credit_cards/
            │   └── {bank_name}/
            │       └── {year}-{month:02d}/
            └── savings/
                └── {bank_name}/
                    └── {year}-{month:02d}/
        
        Args:
            customer_name: 客户名称
            category: 类别 ('credit_cards' 或 'savings')
            bank_name: 银行名称
            year: 年份
            month: 月份
            
        Returns:
            str: 完整的文件夹路径
        """
        # 清理名称
        safe_customer_name = self.sanitize_name(customer_name)
        safe_bank_name = self.sanitize_name(bank_name)
        
        # 构建路径：客户/类别/银行/月份
        month_folder = f"{year}-{month:02d}"
        folder_path = Path(self.base_folder) / safe_customer_name / category / safe_bank_name / month_folder
        
        # 创建文件夹
        os.makedirs(folder_path, exist_ok=True)
        
        return str(folder_path)
    
    def organize_statement(self, file_path, customer_name, statement_date, card_info, category=CATEGORY_CREDIT_CARD):
        """
        归档账单文件到正确的层级文件夹
        
        Args:
            file_path: 上传的文件路径
            customer_name: 客户名称
            statement_date: 账单日期（string or datetime）
            card_info: 信用卡/储蓄账户信息 (dict with bank_name, last_4_digits)
            category: 类别 ('credit_cards' 或 'savings')
            
        Returns:
            dict: 归档后的文件路径信息
        """
        # 解析statement date
        if isinstance(statement_date, str):
            stmt_date = self.parse_statement_date(statement_date)
        else:
            stmt_date = statement_date
        
        year, month = self.get_statement_month_year(stmt_date)
        
        # 获取银行名称
        bank_name = card_info.get('bank_name', 'UNKNOWN_BANK')
        
        # 创建文件夹结构
        folder_path = self.create_folder_structure(
            customer_name, category, bank_name, year, month
        )
        
        # 生成新文件名：BankName_Last4Digits_YYYY-MM-DD.pdf
        file_extension = os.path.splitext(file_path)[1]
        safe_bank_name = self.sanitize_name(bank_name)
        new_filename = f"{safe_bank_name}_{card_info.get('last_4_digits', '0000')}_{stmt_date.strftime('%Y-%m-%d')}{file_extension}"
        
        # 目标路径
        destination = os.path.join(folder_path, new_filename)
        
        # 复制文件到归档位置
        shutil.copy2(file_path, destination)
        
        return {
            'original_path': file_path,
            'archived_path': destination,
            'category': category,
            'bank_name': bank_name,
            'year': year,
            'month': month,
            'folder_path': folder_path
        }
    
    def get_monthly_statements(self, customer_name, category, bank_name, year, month):
        """
        获取指定客户/类别/银行/月份的所有账单
        
        Args:
            customer_name: 客户名称
            category: 类别 ('credit_cards' 或 'savings')
            bank_name: 银行名称
            year: 年份
            month: 月份
            
        Returns:
            list: 账单文件路径列表
        """
        safe_customer_name = self.sanitize_name(customer_name)
        safe_bank_name = self.sanitize_name(bank_name)
        month_folder = f"{year}-{month:02d}"
        
        statements_folder = Path(self.base_folder) / safe_customer_name / category / safe_bank_name / month_folder
        
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
    
    def get_customer_all_statements(self, customer_name):
        """
        获取客户所有账单（信用卡+储蓄）
        
        Args:
            customer_name: 客户名称
            
        Returns:
            dict: 包含信用卡和储蓄账户的所有账单
        """
        safe_customer_name = self.sanitize_name(customer_name)
        customer_folder = Path(self.base_folder) / safe_customer_name
        
        result = {
            'credit_cards': {},
            'savings': {}
        }
        
        if not customer_folder.exists():
            return result
        
        # 遍历两大类别
        for category in [self.CATEGORY_CREDIT_CARD, self.CATEGORY_SAVINGS]:
            category_folder = customer_folder / category
            if not category_folder.exists():
                continue
            
            # 遍历银行
            for bank_folder in category_folder.iterdir():
                if not bank_folder.is_dir():
                    continue
                
                bank_name = bank_folder.name
                result[category][bank_name] = {}
                
                # 遍历月份
                for month_folder in bank_folder.iterdir():
                    if not month_folder.is_dir():
                        continue
                    
                    month_key = month_folder.name  # 例如 "2024-11"
                    files = [f.name for f in month_folder.iterdir() if f.is_file()]
                    result[category][bank_name][month_key] = files
        
        return result
    
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
    
    # 示例：归档一个信用卡账单
    # card_info = {'bank_name': 'Maybank', 'last_4_digits': '1234'}
    # result = organizer.organize_statement(
    #     'uploads/temp_file.pdf',
    #     'Chang',
    #     '2025-01-28',
    #     card_info,
    #     category=StatementOrganizer.CATEGORY_CREDIT_CARD
    # )
    # print(f"✅ 信用卡账单归档完成：{result['archived_path']}")
    
    # 示例：归档一个储蓄账户账单
    # savings_info = {'bank_name': 'GX Bank', 'last_4_digits': '5678'}
    # result = organizer.organize_statement(
    #     'uploads/temp_file.pdf',
    #     'Chang',
    #     '2024-12-31',
    #     savings_info,
    #     category=StatementOrganizer.CATEGORY_SAVINGS
    # )
    # print(f"✅ 储蓄账单归档完成：{result['archived_path']}")
