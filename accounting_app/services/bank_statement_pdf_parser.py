"""
银行月结单PDF解析器
专门用于解析马来西亚各大银行的PDF月结单
"""
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import re
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BankStatementPDFParser:
    """银行月结单PDF解析器"""
    
    def __init__(self, enable_ocr=True):
        self.enable_ocr = enable_ocr
        
    def parse_bank_statement(self, pdf_path: str) -> Dict:
        """
        解析银行月结单PDF，提取交易记录
        
        返回格式:
        {
            "success": True,
            "method": "text" or "ocr",
            "bank_name": "Maybank",
            "account_number": "3824549009",
            "statement_month": "2024-12",
            "transactions": [
                {
                    "date": "2024-12-01",
                    "description": "...",
                    "debit": 100.00,
                    "credit": 0.00,
                    "balance": 5000.00
                }
            ],
            "opening_balance": 5000.00,
            "closing_balance": 4900.00,
            "confidence": 0.85
        }
        """
        result = {
            "success": False,
            "method": None,
            "bank_name": None,
            "account_number": None,
            "statement_month": None,
            "transactions": [],
            "opening_balance": None,
            "closing_balance": None,
            "confidence": 0,
            "error_message": None
        }
        
        try:
            # 尝试文本PDF解析
            text_result = self._parse_text_pdf(pdf_path)
            if text_result["success"] and text_result["confidence"] > 0.5:
                return text_result
            
            # 如果文本解析失败，尝试OCR
            if self.enable_ocr:
                ocr_result = self._parse_ocr_pdf(pdf_path)
                if ocr_result["success"]:
                    return ocr_result
            
            result["error_message"] = "无法解析PDF，建议转换为CSV格式上传"
            return result
            
        except Exception as e:
            logger.error(f"PDF解析异常: {str(e)}")
            result["error_message"] = f"解析错误: {str(e)}"
            return result
    
    def _parse_text_pdf(self, pdf_path: str) -> Dict:
        """解析文本型PDF"""
        result = {
            "success": False,
            "method": "text",
            "bank_name": None,
            "account_number": None,
            "statement_month": None,
            "transactions": [],
            "confidence": 0
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_text = ""
                all_tables = []
                
                for page in pdf.pages:
                    # 提取文本
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
                    
                    # 提取表格
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
                
                if not all_text and not all_tables:
                    result["error_message"] = "PDF无法提取文本或表格数据。如果是扫描件，请使用CSV格式上传。"
                    return result
                
                # 识别银行信息
                result["bank_name"] = self._extract_bank_name(all_text)
                result["account_number"] = self._extract_account_number(all_text)
                result["statement_month"] = self._extract_statement_month(all_text)
                
                # 从表格提取交易记录
                if all_tables:
                    result["transactions"] = self._extract_transactions_from_tables(all_tables)
                else:
                    # 如果没有表格，尝试从文本解析交易
                    result["transactions"] = self._extract_transactions_from_ocr_text(all_text)
                
                # 计算置信度
                confidence = 0
                if result["bank_name"]:
                    confidence += 0.3
                if result["account_number"]:
                    confidence += 0.3
                if result["statement_month"]:
                    confidence += 0.2
                if len(result["transactions"]) > 0:
                    confidence += 0.2
                
                result["confidence"] = round(confidence, 2)
                result["success"] = confidence > 0.5
                
                return result
                
        except Exception as e:
            logger.error(f"文本PDF解析失败: {str(e)}")
            result["error_message"] = str(e)
            return result
    
    def _parse_ocr_pdf(self, pdf_path: str) -> Dict:
        """使用OCR解析扫描件PDF"""
        result = {
            "success": False,
            "method": "ocr",
            "bank_name": None,
            "account_number": None,
            "statement_month": None,
            "transactions": [],
            "confidence": 0
        }
        
        try:
            from pdf2image import convert_from_path
            import pytesseract
            from PIL import Image
            
            # 转换PDF为图片
            images = convert_from_path(pdf_path, dpi=300)
            
            all_text = ""
            all_tables_text = []
            
            for i, image in enumerate(images):
                # OCR识别
                ocr_text = pytesseract.image_to_string(image, lang='eng')
                all_text += ocr_text + "\n"
                
                # 尝试识别表格结构
                ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                all_tables_text.append(ocr_data)
            
            if not all_text.strip():
                result["error_message"] = "OCR无法识别PDF内容"
                return result
            
            # 识别银行信息
            result["bank_name"] = self._extract_bank_name(all_text)
            result["account_number"] = self._extract_account_number(all_text)
            result["statement_month"] = self._extract_statement_month(all_text)
            
            # 从OCR文本提取交易记录
            result["transactions"] = self._extract_transactions_from_ocr_text(all_text)
            
            # 计算置信度
            confidence = 0
            if result["bank_name"]:
                confidence += 0.3
            if result["account_number"]:
                confidence += 0.3
            if result["statement_month"]:
                confidence += 0.2
            if len(result["transactions"]) > 0:
                confidence += 0.2
            
            result["confidence"] = round(confidence, 2)
            result["success"] = confidence > 0.3  # 降低阈值，OCR准确度较低
            
            return result
            
        except ImportError as e:
            logger.error(f"OCR依赖缺失: {str(e)}")
            result["error_message"] = f"OCR功能需要安装依赖: {str(e)}"
            return result
        except Exception as e:
            logger.error(f"OCR解析失败: {str(e)}")
            result["error_message"] = f"OCR解析错误: {str(e)}"
            return result
    
    def _extract_bank_name(self, text: str) -> Optional[str]:
        """从文本提取银行名称"""
        bank_keywords = {
            'maybank': 'Maybank',
            'malayan banking': 'Maybank',
            'public bank': 'Public Bank',
            'cimb': 'CIMB',
            'hong leong': 'Hong Leong Bank',
            'rhb': 'RHB Bank',
            'ambank': 'AmBank',
            'uob': 'UOB',
            'ocbc': 'OCBC',
            'hsbc': 'HSBC',
            'standard chartered': 'Standard Chartered',
            'alliance': 'Alliance Bank',
            'affin': 'Affin Bank',
            'bank islam': 'Bank Islam',
            'bank rakyat': 'Bank Rakyat',
            'bsn': 'BSN'
        }
        
        text_lower = text.lower()
        for keyword, bank_name in bank_keywords.items():
            if keyword in text_lower:
                return bank_name
        
        return None
    
    def _extract_account_number(self, text: str) -> Optional[str]:
        """提取账号"""
        # 查找10-16位连续数字
        patterns = [
            r'account\s*(?:no|number)[\s:]*(\d{10,16})',
            r'a/c\s*(?:no|number)?[\s:]*(\d{10,16})',
            r'\b(\d{10,16})\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_statement_month(self, text: str) -> Optional[str]:
        """提取月结单月份"""
        # 查找日期模式
        patterns = [
            r'statement.*?(\d{4})[-/](\d{1,2})',
            r'period.*?(\d{4})[-/](\d{1,2})',
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    if len(matches[0]) == 2:  # YYYY-MM
                        year, month = matches[0]
                        return f"{year}-{month.zfill(2)}"
                    elif len(matches[0]) == 3:  # DD-MM-YYYY
                        day, month, year = matches[0]
                        return f"{year}-{month.zfill(2)}"
                except:
                    pass
        
        return None
    
    def _extract_transactions_from_tables(self, tables: List) -> List[Dict]:
        """从表格提取交易记录"""
        transactions = []
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # 第一行通常是表头
            headers = [str(h).strip().lower() if h else '' for h in table[0]]
            
            # 查找日期列、描述列、借方列、贷方列、余额列
            date_col = self._find_column(headers, ['date', 'transaction date', 'value date'])
            desc_col = self._find_column(headers, ['description', 'particulars', 'transaction description'])
            debit_col = self._find_column(headers, ['debit', 'withdrawal', 'payments'])
            credit_col = self._find_column(headers, ['credit', 'deposit', 'receipts'])
            balance_col = self._find_column(headers, ['balance', 'running balance'])
            
            # 解析数据行
            for row in table[1:]:
                if not row or len(row) < 2:
                    continue
                
                try:
                    transaction = {}
                    
                    # 提取日期
                    if date_col is not None and date_col < len(row):
                        date_str = str(row[date_col]).strip()
                        parsed_date = self._parse_date(date_str)
                        if parsed_date:
                            transaction["date"] = parsed_date
                    
                    # 提取描述
                    if desc_col is not None and desc_col < len(row):
                        transaction["description"] = str(row[desc_col]).strip()
                    
                    # 提取金额
                    if debit_col is not None and debit_col < len(row):
                        debit = self._parse_amount(str(row[debit_col]))
                        transaction["debit"] = float(debit) if debit else 0
                    else:
                        transaction["debit"] = 0
                    
                    if credit_col is not None and credit_col < len(row):
                        credit = self._parse_amount(str(row[credit_col]))
                        transaction["credit"] = float(credit) if credit else 0
                    else:
                        transaction["credit"] = 0
                    
                    if balance_col is not None and balance_col < len(row):
                        balance = self._parse_amount(str(row[balance_col]))
                        transaction["balance"] = float(balance) if balance else None
                    
                    # 只添加有日期的交易
                    if "date" in transaction and transaction.get("description"):
                        transactions.append(transaction)
                        
                except Exception as e:
                    logger.warning(f"跳过无效行: {e}")
                    continue
        
        return transactions
    
    def _find_column(self, headers: List[str], keywords: List[str]) -> Optional[int]:
        """查找包含关键词的列索引"""
        for i, header in enumerate(headers):
            for keyword in keywords:
                if keyword in header:
                    return i
        return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析日期字符串，返回YYYY-MM-DD格式"""
        if not date_str or date_str.lower() in ['none', 'null', '']:
            return None
        
        # 移除Excel公式格式
        date_str = re.sub(r'^="(.*)"$', r'\1', date_str)
        date_str = date_str.strip()
        
        # 支持多种日期格式
        date_formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%d %b %Y',
            '%d %B %Y'
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """解析金额字符串"""
        if not amount_str or amount_str.lower() in ['none', 'null', '']:
            return None
        
        try:
            # 移除Excel公式格式
            amount_str = re.sub(r'^="(.*)"$', r'\1', amount_str)
            # 移除货币符号和逗号
            amount_str = re.sub(r'[RM$,\s]', '', amount_str)
            if amount_str:
                return Decimal(amount_str)
        except:
            pass
        
        return None
    
    def _extract_transactions_from_ocr_text(self, text: str) -> List[Dict]:
        """从OCR识别的文本中提取交易记录"""
        transactions = []
        
        # 按行分割
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 尝试匹配交易行模式：日期 描述 金额
            # 示例：07-12-2024 Transfer 1000.00
            pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})\s+(.+?)\s+([\d,]+\.\d{2})'
            match = re.search(pattern, line)
            
            if match:
                date_str, description, amount_str = match.groups()
                parsed_date = self._parse_date(date_str)
                
                if parsed_date:
                    transaction = {
                        "date": parsed_date,
                        "description": description.strip(),
                        "debit": 0,
                        "credit": 0
                    }
                    
                    # 判断借方还是贷方（简单规则：如果描述包含关键词）
                    amount = float(self._parse_amount(amount_str) or 0)
                    if any(kw in description.lower() for kw in ['deposit', 'credit', 'transfer in', 'receipt']):
                        transaction["credit"] = amount
                    else:
                        transaction["debit"] = amount
                    
                    transactions.append(transaction)
        
        return transactions
