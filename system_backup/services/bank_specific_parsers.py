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
        elif special_parser == 'standard_chartered':
            return self._extract_standard_chartered(text, trans_patterns, customer_name)
        elif special_parser == 'ocbc':
            return self._extract_ocbc(text, trans_patterns, customer_name)
        elif special_parser == 'hsbc':
            return self._extract_hsbc(text, trans_patterns, customer_name)
        elif special_parser == 'hong_leong':
            return self._extract_hong_leong(text, trans_patterns, customer_name)
        elif special_parser == 'uob':
            return self._extract_uob(text, trans_patterns, customer_name)
        
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
    
    def _extract_standard_chartered(self, text: str, trans_patterns: Dict, customer_name: Optional[str] = None) -> List[Dict]:
        """
        SC专用解析器 - 处理5行交易格式（修复版）
        
        SC格式（5行）:
        - 行1: Posting Date (DD MMM, e.g. 09 Jun)
        - 行2: Transaction Date (DD MMM, e.g. 08 Jun)
        - 行3: 描述行1 (商家名称和地点)
        - 行4: 描述行2 (Txn Ref: 交易参考号)
        - 行5: 金额 (纯数字如29,999.00 或带CR如1,250.00 CR)
        """
        from decimal import Decimal
        import re
        
        transactions = []
        lines = text.split('\n')
        
        logger.info("🔍 使用STANDARD_CHARTERED专用解析器（修复版）")
        
        # 查找交易区域开始标记（支持多种表头格式）
        trans_start = None
        for i, line in enumerate(lines):
            # 方式1: 找到包含"Posting Date"的表头
            if 'Posting' in line and 'Date' in line:
                trans_start = i + 5
                logger.info(f"  找到SC交易表头(Posting Date)，起始位置: line {trans_start}")
                break
            # 方式2: 找到"Posting"单独一行（表头可能是分散的）
            if line.strip() == 'Posting':
                # 往下找10行内是否有日期格式
                for j in range(i+1, min(i+15, len(lines))):
                    if re.match(r'^\d{1,2}\s+[A-Z][a-z]{2}$', lines[j].strip()):
                        trans_start = j
                        logger.info(f"  找到SC交易表头(Posting)，起始位置: line {trans_start}")
                        break
                if trans_start:
                    break
        
        # 方式3: 如果还没找到，查找"BALANCE FROM PREVIOUS"后的第一个日期
        if not trans_start:
            for i, line in enumerate(lines):
                if 'BALANCE FROM PREVIOUS' in line or 'Baki dari penyata sebelumnya' in line:
                    # 往下找日期
                    for j in range(i+1, min(i+10, len(lines))):
                        if re.match(r'^\d{1,2}\s+[A-Z][a-z]{2}$', lines[j].strip()):
                            trans_start = j
                            logger.info(f"  找到SC交易起始(BALANCE)，起始位置: line {trans_start}")
                            break
                    if trans_start:
                        break
        
        if not trans_start or trans_start >= len(lines):
            logger.warning("⚠️ 未找到STANDARD_CHARTERED交易区域")
            return transactions
        
        # 解析交易（5行模式）
        i = trans_start
        date_pattern = r'^\d{1,2}\s+[A-Z][a-z]{2}$'
        dr_cr_config = trans_patterns.get('dr_cr_detection', {})
        
        while i < len(lines) - 4:
            line = lines[i].strip()
            
            # 检测第1行：Posting Date (DD MMM)
            if re.match(date_pattern, line):
                posting_date = line
                
                # 验证第2行：Transaction Date (也是DD MMM)
                if i + 1 < len(lines):
                    trans_date = lines[i+1].strip()
                    if not re.match(date_pattern, trans_date):
                        i += 1
                        continue
                else:
                    i += 1
                    continue
                
                # 第3-4行：描述
                if i + 2 < len(lines) and i + 3 < len(lines):
                    desc1 = lines[i+2].strip()
                    desc2 = lines[i+3].strip()
                else:
                    i += 1
                    continue
                
                # 第5行：金额
                if i + 4 < len(lines):
                    amount_line = lines[i+4].strip()
                    
                    # 验证金额格式（纯数字或带CR）
                    amount_match = re.match(r'^([\d,]+\.?\d{0,2})(\s+CR)?$', amount_line)
                    if amount_match:
                        try:
                            amount_str = amount_match.group(1)
                            amount_decimal = Decimal(amount_str.replace(',', ''))
                            
                            # 检查是否为0（跳过0金额交易如BALANCE行）
                            if amount_decimal == 0:
                                logger.debug(f"  ⏭️ 跳过0金额行: {desc1}")
                                i += 5
                                continue
                            
                            is_credit = amount_match.group(2) is not None
                            
                            # 合并描述
                            description = f"{desc1} {desc2}".strip()
                            
                            # 判断DR/CR
                            if not is_credit:
                                is_credit = self._is_credit_transaction(description, amount_str, dr_cr_config)
                            
                            dr_amount = Decimal('0') if is_credit else amount_decimal
                            cr_amount = amount_decimal if is_credit else Decimal('0')
                            
                            # 分类
                            classification = self._classify_transaction(description, is_credit, customer_name)
                            
                            transaction = {
                                'date': posting_date,
                                'description': description,
                                'dr_amount': dr_amount,
                                'cr_amount': cr_amount,
                                'type': 'CR' if is_credit else 'DR',
                                'classification': classification,
                                'amount': amount_decimal
                            }
                            
                            transactions.append(transaction)
                            logger.debug(f"  ✅ SC交易: {posting_date} {description[:40]}... {amount_str}")
                            
                            # 跳过已处理的5行
                            i += 5
                            continue
                            
                        except Exception as e:
                            logger.warning(f"⚠️ SC交易解析失败: {e}")
            
            i += 1
        
        logger.info(f"📊 STANDARD_CHARTERED提取了 {len(transactions)} 笔交易")
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


    def _extract_ocbc(self, text: str, trans_patterns: Dict, customer_name: Optional[str] = None) -> List[Dict]:
        """
        OCBC专用解析器 - 处理6行多行格式
        
        OCBC格式 (6行):
        - 描述行1 (地点)
        - 描述行2 (国家代码如MYS)
        - 交易日期 (DD/MM/YYYY)
        - 入账日期 (DD/MM/YYYY)
        - DR/CR标记
        - 金额
        """
        from decimal import Decimal
        import re
        
        transactions = []
        lines = text.split('\n')
        
        logger.info("🔍 使用OCBC专用解析器")
        
        # 查找包含日期格式DD/MM/YYYY的行
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 检测交易日期格式 (DD/MM/YYYY)
            date_match = re.match(r'^(\d{2}/\d{2}/\d{4})$', line)
            if date_match and i >= 2 and i + 3 < len(lines):
                trans_date = date_match.group(1)
                
                # 前2行是描述
                desc1 = lines[i-2].strip() if i >= 2 else ''
                desc2 = lines[i-1].strip() if i >= 1 else ''
                
                # 后2行应该是：入账日期、DR/CR标记
                post_date = lines[i+1].strip()
                dr_cr_marker = lines[i+2].strip()
                
                # 再下一行应该是金额
                if i + 3 < len(lines):
                    amount_line = lines[i+3].strip()
                    
                    # 验证DR/CR标记
                    if dr_cr_marker in ['DR', 'CR']:
                        # 验证金额格式
                        amount_match = re.match(r'^([\d,]+\.?\d{2})$', amount_line)
                        if amount_match:
                            try:
                                description = f"{desc1} {desc2}".strip()
                                amount_str = amount_match.group(1)
                                amount_decimal = Decimal(amount_str.replace(',', ''))
                                
                                is_credit = (dr_cr_marker == 'CR')
                                
                                dr_amount = Decimal('0') if is_credit else amount_decimal
                                cr_amount = amount_decimal if is_credit else Decimal('0')
                                
                                # 分类
                                dr_cr_config = trans_patterns.get('dr_cr_detection', {})
                                classification = self._classify_transaction(description, is_credit, customer_name)
                                
                                transaction = {
                                    'date': trans_date,
                                    'description': description,
                                    'dr_amount': dr_amount,
                                    'cr_amount': cr_amount,
                                    'type': dr_cr_marker,
                                    'classification': classification,
                                    'amount': amount_decimal
                                }
                                
                                transactions.append(transaction)
                                logger.debug(f"  ✅ OCBC交易: {trans_date} {description[:30]}... {dr_cr_marker} {amount_str}")
                                
                                # 跳过已处理的行
                                i += 4
                                continue
                                
                            except Exception as e:
                                logger.warning(f"⚠️ OCBC交易解析失败: {e}")
            
            i += 1
        
        logger.info(f"📊 OCBC提取了 {len(transactions)} 笔交易")
        return transactions
    
    def _extract_hsbc(self, text: str, trans_patterns: Dict, customer_name: Optional[str] = None) -> List[Dict]:
        """
        HSBC专用解析器 - 处理多列格式
        
        HSBC格式（列式布局）:
        - Post date列（多行日期）
        - Transaction date列（多行日期）
        - Transaction details列（多行描述）
        - Amount列（多行金额，可能有CR标记）
        """
        from decimal import Decimal
        import re
        
        transactions = []
        lines = text.split('\n')
        
        logger.info("🔍 使用HSBC专用解析器")
        
        # 查找交易表头（HSBC表头可能分散在多行）
        trans_start = None
        for i, line in enumerate(lines):
            if 'Transaction date' in line:
                trans_start = i + 1
                break
            # 备选：查找"Post date"
            if 'Post date' in line:
                trans_start = i + 1
                break
        
        if not trans_start:
            logger.warning("⚠️ 未找到HSBC交易表头，尝试查找数据区域...")
            # 尝试查找包含日期的行作为起点
            for i, line in enumerate(lines):
                if re.search(r'\d{1,2}\s+[A-Z]{3}', line):
                    trans_start = i
                    logger.info(f"  找到可能的交易起始位置: line {i}")
                    break
        
        if not trans_start:
            logger.warning("⚠️ 完全未找到HSBC交易数据")
            return transactions
        
        # 收集日期列
        dates = []
        date_pattern = r'^\d{1,2}\s+[A-Z]{3}$'
        
        for i in range(trans_start, min(trans_start + 50, len(lines))):
            line = lines[i].strip()
            if re.match(date_pattern, line):
                dates.append(line)
        
        logger.info(f"  找到 {len(dates)} 个日期")
        
        # 收集描述列（查找包含商家名称的行）
        descriptions = []
        for i in range(trans_start, min(trans_start + 100, len(lines))):
            line = lines[i].strip()
            # HSBC描述通常包含商家名和地点
            if line and not re.match(r'^\d', line) and len(line) > 5:
                # 跳过表头和金额
                if line not in ['Transaction date', 'Transaction details', 'Amount (RM)', 'Post date']:
                    if not re.match(r'^[\d,]+\.?\d{2}(\s+CR)?$', line):
                        # 检查是否像商家名称
                        if any(keyword in line for keyword in ['ShopeePay', 'SMART', 'PETRON', 'PAYMENT', 'CASHBACK', 'Top Up']):
                            descriptions.append(line)
        
        logger.info(f"  找到 {len(descriptions)} 行描述")
        
        # 收集金额列
        amounts = []
        for i in range(trans_start, min(trans_start + 100, len(lines))):
            line = lines[i].strip()
            amount_match = re.match(r'^([\d,]+\.?\d{2})(\s+CR)?$', line)
            if amount_match:
                amounts.append(line)
        
        logger.info(f"  找到 {len(amounts)} 个金额")
        
        # 匹配交易
        min_len = min(len(dates), len(descriptions), len(amounts))
        
        if min_len == 0:
            logger.warning(f"⚠️ HSBC数据不完整: dates={len(dates)}, desc={len(descriptions)}, amounts={len(amounts)}")
            return transactions
        
        dr_cr_config = trans_patterns.get('dr_cr_detection', {})
        
        for i in range(min_len):
            try:
                date = dates[i]
                description = descriptions[i]
                amount_str = amounts[i]
                
                # 解析金额和CR标记
                is_credit = 'CR' in amount_str
                amount_cleaned = amount_str.replace('CR', '').strip()
                amount_decimal = Decimal(amount_cleaned.replace(',', ''))
                
                # 或者通过描述判断
                if not is_credit:
                    is_credit = self._is_credit_transaction(description, amount_cleaned, dr_cr_config)
                
                dr_amount = Decimal('0') if is_credit else amount_decimal
                cr_amount = amount_decimal if is_credit else Decimal('0')
                
                # 分类
                classification = self._classify_transaction(description, is_credit, customer_name)
                
                transaction = {
                    'date': date,
                    'description': description,
                    'dr_amount': dr_amount,
                    'cr_amount': cr_amount,
                    'type': 'CR' if is_credit else 'DR',
                    'classification': classification,
                    'amount': amount_decimal
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"⚠️ HSBC交易{i+1}解析失败: {e}")
                continue
        
        logger.info(f"📊 HSBC提取了 {len(transactions)} 笔交易")
        return transactions
    
    def _extract_hong_leong(self, text: str, trans_patterns: Dict, customer_name: Optional[str] = None) -> List[Dict]:
        """
        HONG_LEONG专用解析器 - 处理分列布局
        
        HL格式（分列布局）:
        - 第1块：所有Transaction Date (DD MMM)
        - 第2块：所有Posting Date (DD MMM)  
        - 第3块：所有Description (商家名称)
        - 第4块：所有Amount (金额)
        """
        from decimal import Decimal
        import re
        
        transactions = []
        lines = text.split('\n')
        
        logger.info("🔍 使用HONG_LEONG专用解析器（分列布局）")
        
        # 查找交易区域开始标记
        trans_start = None
        for i, line in enumerate(lines):
            if 'YOUR TRANSACTION DETAILS' in line or 'TRANSAKSI TERPERINCI ANDA' in line:
                trans_start = i + 10
                logger.info(f"  找到HL交易表头，起始位置: line {trans_start}")
                break
        
        if not trans_start or trans_start >= len(lines):
            logger.warning("⚠️ 未找到HONG_LEONG交易区域")
            return transactions
        
        # 简化策略：直接查找并收集所有数据
        trans_dates = []
        descriptions = []
        amounts = []
        
        date_pattern = r'^\d{1,2}\s+[A-Z]{3}$'
        # 金额必须有小数点（排除交易参考号）
        amount_pattern = r'^([\d,]+\.\d{2})(\s+CR)?$'
        
        # 标记各区域
        in_date_section = True
        in_desc_section = False
        in_amount_section = False
        
        for i in range(trans_start, min(trans_start + 400, len(lines))):
            line = lines[i].strip()
            
            # 跳过空行
            if not line:
                continue
            
            # 阶段1：收集日期（直到遇到非日期行）
            if in_date_section:
                if re.match(date_pattern, line):
                    # 只收集前N个（第1列），当日期数达到一定数量后检查是否进入描述区
                    if len(trans_dates) < 100:
                        trans_dates.append(line)
                elif 'MYS' in line or 'PAYMENT' in line:
                    # 发现描述行，切换到描述区
                    in_date_section = False
                    in_desc_section = True
                    # 处理这一行
                    if not any(skip in line for skip in ['PREVIOUS', 'NEW TRANSACTION']):
                        descriptions.append(line)
                        
            # 阶段2：收集描述（直到遇到金额行）
            elif in_desc_section:
                if re.match(amount_pattern, line):
                    # 发现金额行，切换到金额区
                    in_desc_section = False
                    in_amount_section = True
                    amounts.append(line)
                elif 'MYS' in line or 'PAYMENT' in line or 'REBATE' in line:
                    descriptions.append(line)
                    
            # 阶段3：收集金额
            elif in_amount_section:
                if re.match(amount_pattern, line):
                    amounts.append(line)
                elif line and not re.match(date_pattern, line):
                    # 遇到非金额行，停止收集
                    break
        
        logger.info(f"  收集: {len(trans_dates)}个日期, {len(descriptions)}行描述, {len(amounts)}个金额")
        
        # 匹配交易（取最小长度）
        min_len = min(len(trans_dates), len(descriptions), len(amounts))
        
        if min_len == 0:
            logger.warning(f"⚠️ HL数据不完整: dates={len(trans_dates)}, desc={len(descriptions)}, amounts={len(amounts)}")
            return transactions
        
        dr_cr_config = trans_patterns.get('dr_cr_detection', {})
        
        for i in range(min_len):
            try:
                date = trans_dates[i]
                description = descriptions[i]
                amount_str = amounts[i]
                
                # 解析金额和CR标记
                is_credit = 'CR' in amount_str
                amount_cleaned = amount_str.replace('CR', '').strip()
                amount_decimal = Decimal(amount_cleaned.replace(',', ''))
                
                # 或者通过描述判断
                if not is_credit:
                    is_credit = self._is_credit_transaction(description, amount_cleaned, dr_cr_config)
                
                dr_amount = Decimal('0') if is_credit else amount_decimal
                cr_amount = amount_decimal if is_credit else Decimal('0')
                
                # 分类
                classification = self._classify_transaction(description, is_credit, customer_name)
                
                transaction = {
                    'date': date,
                    'description': description,
                    'dr_amount': dr_amount,
                    'cr_amount': cr_amount,
                    'type': 'CR' if is_credit else 'DR',
                    'classification': classification,
                    'amount': amount_decimal
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"⚠️ HL交易{i+1}解析失败: {e}")
                continue
        
        logger.info(f"📊 HONG_LEONG提取了 {len(transactions)} 笔交易")
        return transactions
    
    def _extract_uob(self, text: str, trans_patterns: Dict, customer_name: Optional[str] = None) -> List[Dict]:
        """
        UOB专用解析器 - 处理多行交易格式
        
        UOB格式（多行）:
        日期行：26 MAY
        描述行1：LAZADA TOPUP
        描述行2：KUALA LUMPUR
        描述行3：MY
        金额行：2,500.00 (或 370.00 CR)
        """
        from decimal import Decimal
        import re
        
        transactions = []
        lines = text.split('\n')
        
        logger.info("🔍 使用UOB专用解析器（多行格式）")
        
        # 查找交易区域（在"Transaction Date"标记之后）
        trans_start = None
        for i, line in enumerate(lines):
            if 'Transaction Date' in line and i > 400:
                trans_start = i + 10  # 跳过表头
                logger.info(f"  找到UOB交易表头，起始位置: line {trans_start}")
                break
        
        if not trans_start or trans_start >= len(lines):
            logger.warning("⚠️ 未找到UOB交易区域")
            return transactions
        
        # 策略：从金额行向上查找日期和描述
        # 金额pattern（必须有小数点，可能有CR）
        amount_pattern = r'^([\d,]+\.\d{2})(\s+CR)?$'
        date_pattern = r'^\d{2}\s+[A-Z]{3}$'
        
        dr_cr_config = trans_patterns.get('dr_cr_detection', {})
        
        i = trans_start
        while i < min(trans_start + 300, len(lines)):
            line = lines[i].strip()
            
            # 找到金额行
            amount_match = re.match(amount_pattern, line)
            if amount_match:
                try:
                    amount_str = amount_match.group(1)
                    cr_marker = amount_match.group(2)
                    amount_decimal = Decimal(amount_str.replace(',', ''))
                    
                    # 跳过PREVIOUS BAL, CREDIT LIMIT等的金额
                    if amount_decimal < 0.5:  # 跳过太小的金额
                        i += 1
                        continue
                    
                    # 向上查找日期和描述（最多向上看10行）
                    date = None
                    description_lines = []
                    
                    for j in range(i-1, max(i-12, trans_start-1), -1):
                        prev_line = lines[j].strip()
                        
                        # 找到日期
                        if re.match(date_pattern, prev_line):
                            date = prev_line
                            # 收集日期和金额之间的所有描述行
                            for k in range(j+1, i):
                                desc_line = lines[k].strip()
                                if desc_line and not re.match(amount_pattern, desc_line):
                                    # 跳过特殊标记
                                    if not any(skip in desc_line for skip in ['PREVIOUS', 'PAYMENT REC', 'CREDIT LIMIT', 'WORLD MASTERCARD']):
                                        description_lines.append(desc_line)
                            break
                    
                    # 如果没有日期，向上查找描述（可能是PAYMENT这种）
                    if not date:
                        for j in range(i-1, max(i-5, trans_start-1), -1):
                            prev_line = lines[j].strip()
                            if prev_line and len(prev_line) > 5:
                                if any(keyword in prev_line for keyword in ['PAYMENT', 'PREVIOUS', 'INTEREST', 'INSTALMENT']):
                                    description_lines = [prev_line]
                                    date = "UNKNOWN"
                                    break
                    
                    if date and description_lines:
                        description = ' '.join(description_lines)
                        
                        # 判断CR/DR
                        is_credit = bool(cr_marker) or self._is_credit_transaction(description, amount_str, dr_cr_config)
                        
                        dr_amount = Decimal('0') if is_credit else amount_decimal
                        cr_amount = amount_decimal if is_credit else Decimal('0')
                        
                        # 分类
                        classification = self._classify_transaction(description, is_credit, customer_name)
                        
                        transaction = {
                            'date': date,
                            'description': description,
                            'dr_amount': dr_amount,
                            'cr_amount': cr_amount,
                            'type': 'CR' if is_credit else 'DR',
                            'classification': classification,
                            'amount': amount_decimal
                        }
                        
                        transactions.append(transaction)
                        
                except Exception as e:
                    logger.warning(f"⚠️ UOB金额行{i}解析失败: {line} - {e}")
            
            # 遇到结束标记，停止
            if 'END OF STATEMENT' in line or 'SUB-TOTAL' in line:
                break
            
            i += 1
        
        logger.info(f"📊 UOB提取了 {len(transactions)} 笔交易")
        return transactions


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
