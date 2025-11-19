"""
银行专用解析器
使用银行模版配置 + 正则表达式从Document AI文本中提取所有字段
"""

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from decimal import Decimal

logger = logging.getLogger(__name__)

# 7个Supplier列表（用于分类）
SUPPLIERS = [
    "7SL",
    "Dinas",
    "Raub Syc Hainan",
    "Ai Smart Tech",
    "HUAWEI",
    "PasarRaya",
    "Puchong Herbs"
]


class BankSpecificParser:
    """银行专用解析器"""
    
    def __init__(self):
        """初始化，加载银行模版配置"""
        config_path = Path(__file__).parent.parent / "config" / "bank_parser_templates.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.templates = json.load(f)
        
        logger.info(f"✅ 加载银行模版配置：{len(self.templates) - 1}间银行")  # -1 for classification_rules
    
    def detect_bank(self, text: str) -> str:
        """从文本中检测银行名称"""
        text_upper = text.upper()
        
        # 检测每间银行的别名
        for bank_name, config in self.templates.items():
            if bank_name == "classification_rules":
                continue
            
            aliases = config.get("aliases", [])
            for alias in aliases:
                if alias.upper() in text_upper:
                    logger.info(f"✅ 检测到银行: {bank_name}")
                    return bank_name
        
        logger.warning("⚠️ 未能检测银行，返回UNKNOWN")
        return "UNKNOWN"
    
    def parse_bank_statement(self, text: str, bank_name: str) -> Dict[str, Any]:
        """
        使用银行专用模版解析账单
        
        Args:
            text: Document AI提取的完整文本
            bank_name: 银行名称（自动检测或手动指定）
        
        Returns:
            Dict包含所有提取的字段和交易记录
        """
        if bank_name not in self.templates:
            logger.error(f"❌ 未找到银行 {bank_name} 的模版配置")
            return {}
        
        template = self.templates[bank_name]
        logger.info(f"🔍 使用 {bank_name} 模版解析账单")
        
        result = {
            'bank_name': bank_name,
            'fields': {},
            'transactions': []
        }
        
        # 1. 提取基本字段
        patterns = template.get('patterns', {})
        for field_name, pattern_config in patterns.items():
            # 跳过非dict类型的配置（如'description'字段）
            if not isinstance(pattern_config, dict):
                continue
            
            regex_list = pattern_config.get('regex', [])
            
            # 确保regex_list是列表
            if isinstance(regex_list, str):
                regex_list = [regex_list]
            elif not isinstance(regex_list, list):
                continue
            
            for regex_pattern in regex_list:
                # 跳过非字符串的regex
                if not isinstance(regex_pattern, str):
                    continue
                
                try:
                    match = re.search(regex_pattern, text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        value = match.group(1) if match.groups() else match.group(0)
                        
                        # 特殊处理：卡号提取后4位
                        if field_name == 'card_number' and pattern_config.get('extract') == 'last_4':
                            if match.groups() and len(match.groups()) >= 4:
                                value = match.group(4)  # 最后一组
                        
                        # 特殊处理：金额去除逗号
                        if any(keyword in field_name for keyword in ['balance', 'payment', 'amount', 'limit', 'credit']):
                            value = value.replace(',', '')
                        
                        result['fields'][field_name] = value
                        logger.debug(f"  ✅ {field_name}: {value}")
                        break
                except re.error as e:
                    logger.warning(f"⚠️ 正则表达式错误 {field_name}: {e}")
        
        # 2. 提取交易记录（传入客户名用于分类）
        customer_name = result['fields'].get('customer_name')
        transactions = self._extract_transactions(text, template, customer_name)
        result['transactions'] = transactions
        
        logger.info(f"✅ 提取完成：{len(result['fields'])}个字段，{len(transactions)}笔交易")
        
        return result
    
    def _extract_transactions(self, text: str, template: Dict, customer_name: Optional[str] = None) -> List[Dict]:
        """
        提取交易记录
        
        Returns:
            List of transactions with structure:
            {
                'date': str,
                'description': str,
                'dr_amount': float,  # DR列（借方）
                'cr_amount': float,  # CR列（贷方）
                'classification': str  # 'Owner' or 'GZ'
            }
        """
        transactions = []
        trans_patterns = template.get('transaction_patterns', {})
        
        if not trans_patterns:
            logger.warning("⚠️ 模版中未配置transaction_patterns")
            return transactions
        
        # 检查是否需要特殊解析器
        special_parser = trans_patterns.get('special_parser')
        if special_parser == 'ambank_columnar':
            return self._extract_ambank_columnar(text, trans_patterns, customer_name)
        
        # 获取交易记录正则
        trans_line = trans_patterns.get('transaction_line', {})
        regex_pattern = trans_line.get('regex')
        groups = trans_line.get('groups', {})
        
        if not regex_pattern:
            logger.warning("⚠️ 模版中未配置交易记录正则表达式")
            return transactions
        
        # 查找所有交易记录
        matches = re.finditer(regex_pattern, text, re.MULTILINE)
        
        for match in matches:
            try:
                # 提取字段
                date = match.group(groups.get('date', 1))
                description = match.group(groups.get('description', 2))
                amount_str = match.group(groups.get('amount', 3))
                
                # 解析金额
                amount = self._parse_amount(amount_str)
                
                # 检测DR/CR类型
                dr_cr_config = trans_patterns.get('dr_cr_detection', {})
                is_credit = self._is_credit_transaction(
                    description, 
                    amount_str, 
                    dr_cr_config
                )
                
                # 分离DR和CR列（使用Decimal）
                from decimal import Decimal
                dr_amount = Decimal('0') if is_credit else amount
                cr_amount = amount if is_credit else Decimal('0')
                
                # 分类（Owner or GZ）- 使用传入的客户名
                classification = self._classify_transaction(
                    description, 
                    is_credit,
                    customer_name=customer_name
                )
                
                transaction = {
                    'date': date.strip(),
                    'description': description.strip(),
                    'dr_amount': dr_amount,
                    'cr_amount': cr_amount,
                    'type': 'CR' if is_credit else 'DR',
                    'classification': classification
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"⚠️ 解析交易记录失败: {e}")
                continue
        
        logger.info(f"📊 提取了 {len(transactions)} 笔交易")
        
        return transactions
    
    def _extract_ambank_columnar(self, text: str, trans_patterns: Dict, customer_name: Optional[str] = None) -> List[Dict]:
        """
        AMBANK专用解析器 - 处理列式布局
        
        AMBANK格式：
        - Transaction Date列（多行日期）
        - Posting Date列（多行日期）
        - Amount列（多行金额）
        - Transaction Description列（多行描述）
        
        这些列在文本中是分开的，需要特殊逻辑来匹配
        """
        import re
        from decimal import Decimal
        
        transactions = []
        lines = text.split('\n')
        
        # 1. 找到交易记录区域
        trans_start = None
        for i, line in enumerate(lines):
            if 'YOUR TRANSACTION DETAILS' in line or 'TRANSAKSI TERPERINCI' in line:
                trans_start = i
                break
        
        if not trans_start:
            logger.warning("⚠️ 未找到AMBANK交易记录起始位置")
            return transactions
        
        # 2. 提取日期列（Transaction Date）
        dates = []
        date_pattern = r'^\d{2}\s+[A-Z]{3}\s+\d{2}$'
        
        for i in range(trans_start, min(trans_start + 50, len(lines))):
            line = lines[i].strip()
            if re.match(date_pattern, line) and line not in ['Transaction Date', 'Tarikh Transaksi']:
                dates.append(line)
        
        logger.info(f"  找到 {len(dates)} 个日期")
        
        # 3. 提取描述列（Transaction Description）
        descriptions = []
        desc_start = None
        
        for i in range(trans_start, min(trans_start + 50, len(lines))):
            if 'Transaction Description' in lines[i] or 'Butir-butir Transaksi' in lines[i]:
                desc_start = i + 1
                break
        
        if desc_start:
            # 读取描述，直到遇到"SUB TOTAL"或金额行
            for i in range(desc_start, min(desc_start + 30, len(lines))):
                line = lines[i].strip()
                
                # 停止条件
                if 'SUB TOTAL' in line or 'End of Transaction' in line:
                    break
                # 跳过纯金额行
                if re.match(r'^[\d,]+\.\d{2}(\s+CR)?$', line):
                    break
                # 跳过空行
                if not line:
                    continue
                # 跳过卡号相关行
                if re.match(r'^\d{4}\s+\d{4}\s+\d{4}\s+\d{4}', line):
                    continue
                if 'AmBank' in line and re.search(r'\d{4}.*?\d{4}.*?\d{4}.*?\d{4}', line):
                    continue
                if 'Visa Signature' in line or 'Islamic' in line:
                    continue
                # 跳过表头行
                if line in ['Transaction Description', 'Butir-butir Transaksi']:
                    continue
                
                descriptions.append(line)
        
        logger.info(f"  找到 {len(descriptions)} 行描述")
        
        # 4. 提取金额列
        amounts = []
        amount_start = None
        
        # 金额通常在描述之后
        for i in range(desc_start if desc_start else trans_start, len(lines)):
            line = lines[i].strip()
            # 纯金额格式：xxx.xx 或 xxx.xx CR
            if re.match(r'^[\d,]+\.\d{2}(\s+CR)?$', line):
                amounts.append(line)
            # 遇到"Total Current Balance"停止
            if 'Total Current Balance' in line or 'End of Transaction' in line:
                break
        
        logger.info(f"  找到 {len(amounts)} 个金额")
        
        # 5. 匹配交易（取最小长度）
        min_len = min(len(dates), len(descriptions), len(amounts))
        
        if min_len == 0:
            logger.warning(f"⚠️ AMBANK数据不完整：dates={len(dates)}, desc={len(descriptions)}, amounts={len(amounts)}")
            return transactions
        
        logger.info(f"  匹配 {min_len} 笔交易")
        
        # 6. 创建交易记录
        dr_cr_config = trans_patterns.get('dr_cr_detection', {})
        
        for i in range(min_len):
            try:
                date = dates[i]
                description = descriptions[i]
                amount_str = amounts[i]
                
                # 解析金额
                amount = self._parse_amount(amount_str.replace(' CR', '').strip())
                
                # 检测CR交易
                is_credit = self._is_credit_transaction(description, amount_str, dr_cr_config)
                
                # 分离DR和CR
                dr_amount = Decimal('0') if is_credit else amount
                cr_amount = amount if is_credit else Decimal('0')
                
                # 分类
                classification = self._classify_transaction(description, is_credit, customer_name)
                
                transaction = {
                    'date': date,
                    'description': description,
                    'dr_amount': dr_amount,
                    'cr_amount': cr_amount,
                    'type': 'CR' if is_credit else 'DR',
                    'classification': classification
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"⚠️ AMBANK交易{i+1}解析失败: {e}")
                continue
        
        logger.info(f"📊 AMBANK提取了 {len(transactions)} 笔交易")
        
        return transactions
    
    def _parse_amount(self, amount_str: str):
        """解析金额字符串（使用Decimal确保精度）"""
        from decimal import Decimal, InvalidOperation
        try:
            # 去除逗号和空格
            cleaned = amount_str.replace(',', '').replace(' ', '').strip()
            
            # 处理负号
            is_negative = cleaned.startswith('-')
            cleaned = cleaned.lstrip('-')
            
            amount = Decimal(cleaned)
            return -amount if is_negative else amount
        except (InvalidOperation, ValueError):
            return Decimal('0')
    
    def _is_credit_transaction(self, description: str, amount_str: str, dr_cr_config: Dict) -> bool:
        """
        判断是否为CR交易
        
        规则：
        1. 金额为负数 → CR
        2. 描述包含CR关键词（PAYMENT, BAYARAN等） → CR
        3. 其他 → DR
        """
        # 检查负数
        if dr_cr_config.get('negative_is_credit', False):
            if amount_str.strip().startswith('-'):
                return True
        
        # 检查CR关键词
        cr_keywords = dr_cr_config.get('cr_keywords', [])
        desc_upper = description.upper()
        
        for keyword in cr_keywords:
            if keyword.upper() in desc_upper:
                return True
        
        return False
    
    def _classify_transaction(self, description: str, is_credit: bool, customer_name: Optional[str] = None) -> str:
        """
        分类交易（Owner or GZ）
        
        规则：
        - DR交易：包含7个Supplier → GZ，否则 → Owner
        - CR交易：包含客户名或为空 → Owner，否则 → GZ
        """
        desc_upper = description.upper()
        
        if not is_credit:  # DR交易
            # 检查7个Supplier
            for supplier in SUPPLIERS:
                if supplier.upper() in desc_upper:
                    logger.debug(f"    ✅ {description[:30]}... 匹配Supplier: {supplier} → GZ")
                    return "GZ"
            logger.debug(f"    ❌ {description[:30]}... 未匹配Supplier → Owner")
            return "Owner"
        
        else:  # CR交易
            # 检查客户名
            if customer_name and customer_name.upper() in desc_upper:
                logger.debug(f"    ✅ {description[:30]}... 包含客户名 → Owner")
                return "Owner"
            
            # 检查Owner关键词（PAYMENT, BAYARAN, THANK YOU等）
            owner_cr_keywords = ['PAYMENT', 'BAYARAN', 'THANK YOU', 'TERIMA KASIH']
            for keyword in owner_cr_keywords:
                if keyword in desc_upper:
                    logger.debug(f"    ✅ {description[:30]}... 包含{keyword} → Owner")
                    return "Owner"
            
            # 检查是否为空
            if len(description.strip()) == 0:
                logger.debug(f"    ✅ 空描述 → Owner")
                return "Owner"
            
            logger.debug(f"    ❌ {description[:30]}... 未匹配Owner规则 → GZ")
            return "GZ"
    
    def convert_to_standard_format(self, parsed_data: Dict) -> tuple:
        """
        转换为标准格式（兼容现有系统）
        
        Returns:
            (info_dict, transactions_list)
        """
        fields = parsed_data.get('fields', {})
        
        # 构建info字典
        info = {
            'bank': parsed_data.get('bank_name', 'UNKNOWN'),
            'card_last4': fields.get('card_number'),
            'statement_date': fields.get('statement_date'),
            'payment_due_date': fields.get('payment_due_date'),
            'previous_balance': self._parse_amount(fields.get('previous_balance', '0')),
            'minimum_payment': self._parse_amount(fields.get('minimum_payment', '0')),
            'total_amount_due': self._parse_amount(fields.get('total_amount_due', '0')),
            'credit_limit': self._parse_amount(fields.get('credit_limit', '0')),
            'available_credit': self._parse_amount(fields.get('available_credit', '0')),
            'reward_points': fields.get('reward_points', '0'),
            'customer_name': fields.get('customer_name')
        }
        
        # 交易记录已经是标准格式
        transactions = parsed_data.get('transactions', [])
        
        return info, transactions


def parse_with_bank_template(text: str, bank_name: Optional[str] = None) -> tuple:
    """
    使用银行模版解析账单文本
    
    Args:
        text: Document AI提取的完整文本
        bank_name: 银行名称（可选，如果未提供会自动检测）
    
    Returns:
        (info_dict, transactions_list)
    """
    parser = BankSpecificParser()
    
    # 自动检测银行
    if not bank_name:
        bank_name = parser.detect_bank(text)
    
    # 解析账单
    parsed_data = parser.parse_bank_statement(text, bank_name)
    
    # 转换为标准格式
    info, transactions = parser.convert_to_standard_format(parsed_data)
    
    return info, transactions
