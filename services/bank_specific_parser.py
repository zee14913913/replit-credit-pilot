"""
银行特定解析器 - Bank-Specific Parser
为12家马来西亚银行提供专用解析逻辑
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class BankSpecificParser:
    """12家马来西亚银行的专用解析器"""
    
    def __init__(self):
        """加载银行模板配置"""
        config_path = Path(__file__).parent.parent / 'config' / 'bank_templates.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.banks = self.config['banks']
        self.global_settings = self.config['global_settings']
    
    def detect_bank(self, text: str) -> Optional[str]:
        """
        从PDF文本中检测银行名称
        
        Args:
            text: PDF文本内容
            
        Returns:
            银行名称或None
        """
        text_upper = text.upper()
        
        # 银行检测规则
        bank_patterns = {
            'Maybank': ['MAYBANK', 'MALAYAN BANKING'],
            'CIMB': ['CIMB BANK', 'CIMB'],
            'Hong Leong Bank': ['HONG LEONG', 'HLB', 'HONG LEONG BANK'],
            'Public Bank': ['PUBLIC BANK', 'PBB'],
            'RHB': ['RHB BANK', 'RHB'],
            'AmBank': ['AMBANK', 'AM BANK'],
            'UOB': ['UOB', 'UNITED OVERSEAS BANK'],
            'OCBC': ['OCBC BANK', 'OCBC'],
            'Alliance Bank': ['ALLIANCE BANK', 'ALLIANCE'],
            'GXBank': ['GXBANK', 'GX BANK', 'GRAB'],
            'Bank Islam': ['BANK ISLAM', 'BIMB'],
            'HSBC': ['HSBC', 'HONGKONG SHANGHAI']
        }
        
        for bank_name, patterns in bank_patterns.items():
            for pattern in patterns:
                if pattern in text_upper:
                    return bank_name
        
        return None
    
    def get_bank_config(self, bank_name: str) -> Optional[Dict]:
        """
        获取银行配置
        
        Args:
            bank_name: 银行名称
            
        Returns:
            银行配置字典或None
        """
        return self.banks.get(bank_name)
    
    def parse_date(self, date_str: str, bank_name: str) -> Optional[str]:
        """
        根据银行的日期格式解析日期
        
        Args:
            date_str: 日期字符串
            bank_name: 银行名称
            
        Returns:
            标准格式日期 (YYYY-MM-DD) 或None
        """
        bank_config = self.get_bank_config(bank_name)
        if not bank_config:
            return None
        
        date_format = bank_config.get('date_format', 'dd/MM/yyyy')
        
        # 转换为Python日期格式
        python_format = date_format.replace('dd', '%d').replace('MM', '%m').replace('MMM', '%b').replace('yyyy', '%Y')
        
        try:
            parsed_date = datetime.strptime(date_str.strip(), python_format)
            return parsed_date.strftime('%Y-%m-%d')
        except Exception:
            # 尝试多种常见格式
            formats = [
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%d %b %Y',
                '%d %B %Y',
                '%Y-%m-%d'
            ]
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
        
        return None
    
    def extract_field(self, text: str, field_name: str, bank_name: str) -> Optional[str]:
        """
        根据银行配置提取特定字段
        
        Args:
            text: PDF文本内容
            field_name: 字段名称
            bank_name: 银行名称
            
        Returns:
            提取的字段值或None
        """
        bank_config = self.get_bank_config(bank_name)
        if not bank_config:
            return None
        
        field_mapping = bank_config.get('field_mapping', {})
        field_aliases = field_mapping.get(field_name, [])
        
        if not field_aliases:
            return None
        
        # 尝试每个字段别名
        for alias in field_aliases:
            # 创建正则表达式模式
            pattern = rf'{re.escape(alias)}\s*:?\s*([^\n]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def is_supplier_transaction(self, description: str, bank_name: str) -> bool:
        """
        判断交易是否为供应商交易
        
        Args:
            description: 交易描述
            bank_name: 银行名称
            
        Returns:
            True/False
        """
        bank_config = self.get_bank_config(bank_name)
        if not bank_config:
            # 使用全局供应商列表
            suppliers = self.global_settings['suppliers']
        else:
            suppliers = bank_config.get('supplier_keywords', self.global_settings['suppliers'])
        
        description_upper = description.upper()
        for supplier in suppliers:
            if supplier.upper() in description_upper:
                return True
        
        return False
    
    def classify_transaction(self, description: str, amount: float, cardholder: str) -> str:
        """
        分类交易
        
        Args:
            description: 交易描述
            amount: 金额
            cardholder: 持卡人姓名
            
        Returns:
            分类名称
        """
        description_upper = description.upper()
        
        # 供应商交易
        if self.is_supplier_transaction(description, ''):
            # 判断是Owners还是GZ
            if 'INFINITE' in cardholder.upper() or 'GZ' in cardholder.upper():
                return 'GZs Expenses'
            else:
                return 'Owners Expenses'
        
        # 付款交易
        if amount < 0 or 'PAYMENT' in description_upper or 'BAYARAN' in description_upper:
            if 'INFINITE' in cardholder.upper() or 'GZ' in cardholder.upper():
                return 'GZs Payment'
            else:
                return 'Owners Payment'
        
        # 费用和利息
        if any(keyword in description_upper for keyword in ['FEE', 'INTEREST', 'CHARGE', 'YURAN', 'FAEDAH']):
            if 'INFINITE' in cardholder.upper() or 'GZ' in cardholder.upper():
                return 'GZs Expenses'
            else:
                return 'Owners Expenses'
        
        # 默认分类
        if 'INFINITE' in cardholder.upper() or 'GZ' in cardholder.upper():
            return 'Infinite GZ'
        else:
            return 'Owners'
    
    def validate_parsing_accuracy(self, extracted_data: Dict, bank_name: str) -> Tuple[bool, float, List[str]]:
        """
        验证解析准确率
        
        Args:
            extracted_data: 提取的数据
            bank_name: 银行名称
            
        Returns:
            (是否通过, 准确率, 错误列表)
        """
        errors = []
        required_fields = ['statement_date', 'card_number', 'total_amount']
        
        # 检查必填字段
        for field in required_fields:
            if not extracted_data.get(field):
                errors.append(f"缺少必填字段: {field}")
        
        # 检查日期格式
        if extracted_data.get('statement_date'):
            date_str = extracted_data['statement_date']
            if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                errors.append(f"日期格式错误: {date_str}")
        
        # 检查金额格式
        if extracted_data.get('total_amount'):
            try:
                float(str(extracted_data['total_amount']).replace(',', '').replace('RM', '').strip())
            except:
                errors.append(f"金额格式错误: {extracted_data['total_amount']}")
        
        # 计算准确率
        total_checks = len(required_fields) + 2  # 必填字段 + 2个格式检查
        passed_checks = total_checks - len(errors)
        accuracy = (passed_checks / total_checks) * 100
        
        is_valid = len(errors) == 0
        
        return is_valid, accuracy, errors
    
    def get_supported_banks(self) -> List[Dict]:
        """
        获取支持的银行列表
        
        Returns:
            银行列表
        """
        result = []
        for bank_name, config in self.banks.items():
            result.append({
                'name': bank_name,
                'display_name': config['display_name'],
                'code': config['code'],
                'enabled': config.get('enabled', True)
            })
        return result
    
    def get_parsing_stats(self) -> Dict:
        """
        获取解析统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_banks': len(self.banks),
            'enabled_banks': sum(1 for config in self.banks.values() if config.get('enabled', True)),
            'total_suppliers': len(self.global_settings['suppliers']),
            'owners_categories': len(self.global_settings['owners_categories']),
            'gz_categories': len(self.global_settings['gz_categories'])
        }


# 全局实例
_parser_instance = None

def get_bank_parser() -> BankSpecificParser:
    """获取银行解析器单例"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = BankSpecificParser()
    return _parser_instance
