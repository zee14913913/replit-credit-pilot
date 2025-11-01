"""
PDF解析服务
支持文本型PDF和OCR扫描件
"""
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
import re
import os
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PDFParseResult:
    """PDF解析结果"""
    
    def __init__(self):
        self.success = False
        self.method = None  # 'text', 'ocr', 'hybrid'
        self.confidence = 0.0
        self.text_content = ""
        self.tables = []
        self.extracted_data = {}
        self.error_message = None
        self.pages_processed = 0
        
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "method": self.method,
            "confidence": self.confidence,
            "text_length": len(self.text_content),
            "tables_count": len(self.tables),
            "extracted_data": self.extracted_data,
            "error_message": self.error_message,
            "pages_processed": self.pages_processed
        }


class PDFParser:
    """统一PDF解析器"""
    
    def __init__(self, enable_ocr=True, ocr_language='eng+chi_sim', dpi=300):
        self.enable_ocr = enable_ocr
        self.ocr_language = ocr_language
        self.dpi = dpi
        
    def parse(self, pdf_path: str) -> PDFParseResult:
        """
        解析PDF文件
        先尝试文本提取，失败则使用OCR
        """
        result = PDFParseResult()
        
        try:
            # 先尝试文本型PDF
            result = self._parse_text_pdf(pdf_path)
            
            if result.success and result.confidence > 0.5:
                logger.info(f"文本PDF解析成功: {pdf_path}")
                return result
            
            # 如果文本提取失败或置信度低，尝试OCR
            if self.enable_ocr:
                logger.info(f"尝试OCR解析: {pdf_path}")
                ocr_result = self._parse_ocr_pdf(pdf_path)
                
                if ocr_result.success and ocr_result.confidence > result.confidence:
                    logger.info(f"OCR解析成功: {pdf_path}")
                    return ocr_result
            
            return result
            
        except Exception as e:
            logger.error(f"PDF解析失败: {pdf_path}, 错误: {str(e)}")
            result.success = False
            result.error_message = str(e)
            return result
    
    def _parse_text_pdf(self, pdf_path: str) -> PDFParseResult:
        """解析文本型PDF"""
        result = PDFParseResult()
        result.method = 'text'
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_text = []
                all_tables = []
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # 提取文本
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                    
                    # 提取表格
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
                    
                    result.pages_processed = page_num
                
                result.text_content = "\n".join(all_text)
                result.tables = all_tables
                
                # 计算置信度（基于提取到的文本量）
                if len(result.text_content) > 100:
                    result.confidence = min(1.0, len(result.text_content) / 1000)
                    result.success = True
                else:
                    result.confidence = 0.2
                    result.success = False
                    result.error_message = "提取的文本过少，可能是扫描件"
                
        except Exception as e:
            result.success = False
            result.error_message = f"文本提取失败: {str(e)}"
            result.confidence = 0.0
        
        return result
    
    def _parse_ocr_pdf(self, pdf_path: str) -> PDFParseResult:
        """使用OCR解析扫描件PDF"""
        result = PDFParseResult()
        result.method = 'ocr'
        
        try:
            # 将PDF转换为图片
            images = convert_from_path(pdf_path, dpi=self.dpi)
            
            all_text = []
            for page_num, image in enumerate(images, 1):
                # OCR识别
                text = pytesseract.image_to_string(
                    image, 
                    lang=self.ocr_language,
                    config='--psm 6'  # Assume uniform text block
                )
                
                if text:
                    all_text.append(text)
                
                result.pages_processed = page_num
            
            result.text_content = "\n".join(all_text)
            
            # OCR置信度通常较低
            if len(result.text_content) > 100:
                result.confidence = min(0.8, len(result.text_content) / 2000)
                result.success = True
            else:
                result.confidence = 0.1
                result.success = False
                result.error_message = "OCR识别失败或文本过少"
            
        except Exception as e:
            result.success = False
            result.error_message = f"OCR处理失败: {str(e)}"
            result.confidence = 0.0
        
        return result
    
    def extract_bank_statement(self, pdf_path: str) -> Dict:
        """
        从PDF中提取银行月结单信息
        """
        parse_result = self.parse(pdf_path)
        
        if not parse_result.success:
            return {
                "success": False,
                "error": parse_result.error_message
            }
        
        # 从文本中提取银行信息
        text = parse_result.text_content
        
        extracted = {
            "success": True,
            "bank_name": self._extract_bank_name(text),
            "account_number": self._extract_account_number(text),
            "statement_period": self._extract_statement_period(text),
            "transactions": self._extract_transactions(parse_result),
            "parse_method": parse_result.method,
            "confidence": parse_result.confidence
        }
        
        return extracted
    
    def extract_supplier_invoice(self, pdf_path: str) -> Dict:
        """
        从PDF中提取供应商发票信息
        """
        parse_result = self.parse(pdf_path)
        
        if not parse_result.success:
            return {
                "success": False,
                "error": parse_result.error_message
            }
        
        text = parse_result.text_content
        
        extracted = {
            "success": True,
            "supplier_name": self._extract_supplier_name(text),
            "invoice_number": self._extract_invoice_number(text),
            "invoice_date": self._extract_date(text, "invoice"),
            "due_date": self._extract_date(text, "due"),
            "total_amount": self._extract_amount(text, "total"),
            "tax_amount": self._extract_amount(text, "tax"),
            "items": self._extract_invoice_items(parse_result),
            "parse_method": parse_result.method,
            "confidence": parse_result.confidence
        }
        
        return extracted
    
    def extract_pos_report(self, pdf_path: str) -> Dict:
        """
        从PDF中提取POS日报信息
        """
        parse_result = self.parse(pdf_path)
        
        if not parse_result.success:
            return {
                "success": False,
                "error": parse_result.error_message
            }
        
        text = parse_result.text_content
        
        extracted = {
            "success": True,
            "report_date": self._extract_date(text, "report"),
            "transactions": self._extract_pos_transactions(parse_result),
            "total_sales": self._extract_amount(text, "total"),
            "transaction_count": len(parse_result.tables[0]) if parse_result.tables else 0,
            "parse_method": parse_result.method,
            "confidence": parse_result.confidence
        }
        
        return extracted
    
    # ========== 辅助提取方法 ==========
    
    def _extract_bank_name(self, text: str) -> Optional[str]:
        """提取银行名称"""
        bank_keywords = {
            'maybank': 'Maybank',
            'public bank': 'Public Bank',
            'cimb': 'CIMB',
            'hong leong': 'Hong Leong Bank',
            'rhb': 'RHB Bank',
            'ambank': 'AmBank',
            'uob': 'UOB',
            'ocbc': 'OCBC',
            'hsbc': 'HSBC'
        }
        
        text_lower = text.lower()
        for keyword, bank_name in bank_keywords.items():
            if keyword in text_lower:
                return bank_name
        
        return None
    
    def _extract_account_number(self, text: str) -> Optional[str]:
        """提取账号"""
        # 匹配10-16位数字
        patterns = [
            r'account.*?(\d{10,16})',
            r'a/c.*?(\d{10,16})',
            r'\b(\d{10,16})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_statement_period(self, text: str) -> Optional[str]:
        """提取月结单期间"""
        # 匹配日期范围
        patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})\s*(?:to|至|-)\s*(\d{1,2}[/-]\d{4})',
            r'statement period.*?(\d{4}-\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_transactions(self, parse_result: PDFParseResult) -> List[Dict]:
        """从表格中提取交易记录"""
        transactions = []
        
        if not parse_result.tables:
            return transactions
        
        # 假设第一个大表格是交易明细
        for table in parse_result.tables:
            if len(table) < 2:  # 至少要有表头和一行数据
                continue
            
            # 尝试识别列
            headers = [str(h).lower() if h else '' for h in table[0]]
            
            for row in table[1:]:
                if len(row) < 3:
                    continue
                
                try:
                    transaction = {
                        "date": row[0] if len(row) > 0 else None,
                        "description": row[1] if len(row) > 1 else None,
                        "debit": self._parse_amount(row[2]) if len(row) > 2 else 0,
                        "credit": self._parse_amount(row[3]) if len(row) > 3 else 0,
                        "balance": self._parse_amount(row[4]) if len(row) > 4 else 0
                    }
                    transactions.append(transaction)
                except:
                    continue
        
        return transactions
    
    def _extract_supplier_name(self, text: str) -> Optional[str]:
        """提取供应商名称"""
        patterns = [
            r'from:?\s*(.+?)(?:\n|$)',
            r'supplier:?\s*(.+?)(?:\n|$)',
            r'vendor:?\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()[:200]
        
        return None
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """提取发票号"""
        patterns = [
            r'invoice\s*(?:no|number)?:?\s*([A-Z0-9-]+)',
            r'inv\s*(?:no|#)?:?\s*([A-Z0-9-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_date(self, text: str, date_type: str) -> Optional[str]:
        """提取日期"""
        keywords = {
            "invoice": ["invoice date", "date"],
            "due": ["due date", "payment due"],
            "report": ["report date", "date"]
        }
        
        for keyword in keywords.get(date_type, []):
            pattern = f"{keyword}:?\\s*(\\d{{1,2}}[/-]\\d{{1,2}}[/-]\\d{{4}})"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_amount(self, text: str, amount_type: str) -> Optional[Decimal]:
        """提取金额"""
        keywords = {
            "total": ["total", "grand total", "amount due"],
            "tax": ["tax", "gst", "sst"],
            "subtotal": ["subtotal", "sub total"]
        }
        
        for keyword in keywords.get(amount_type, []):
            pattern = f"{keyword}:?\\s*(?:RM|MYR)?\\s*([0-9,]+\\.?\\d{{0,2}})"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        
        return None
    
    def _extract_invoice_items(self, parse_result: PDFParseResult) -> List[Dict]:
        """提取发票明细项"""
        items = []
        
        if not parse_result.tables:
            return items
        
        for table in parse_result.tables:
            if len(table) < 2:
                continue
            
            for row in table[1:]:
                if len(row) < 3:
                    continue
                
                try:
                    item = {
                        "description": row[0] if len(row) > 0 else None,
                        "quantity": float(row[1]) if len(row) > 1 else 1,
                        "unit_price": self._parse_amount(row[2]) if len(row) > 2 else 0,
                        "amount": self._parse_amount(row[3]) if len(row) > 3 else 0
                    }
                    items.append(item)
                except:
                    continue
        
        return items
    
    def _extract_pos_transactions(self, parse_result: PDFParseResult) -> List[Dict]:
        """提取POS交易记录"""
        transactions = []
        
        if not parse_result.tables:
            return transactions
        
        for table in parse_result.tables:
            if len(table) < 2:
                continue
            
            for row in table[1:]:
                if len(row) < 4:
                    continue
                
                try:
                    transaction = {
                        "time": row[0] if len(row) > 0 else None,
                        "member_id": row[1] if len(row) > 1 else None,
                        "amount": self._parse_amount(row[2]) if len(row) > 2 else 0,
                        "payment_method": row[3] if len(row) > 3 else None
                    }
                    transactions.append(transaction)
                except:
                    continue
        
        return transactions
    
    def _parse_amount(self, amount_str: str) -> Decimal:
        """解析金额字符串"""
        if not amount_str:
            return Decimal('0')
        
        # 移除货币符号和逗号
        cleaned = str(amount_str).replace(',', '').replace('RM', '').replace('MYR', '').strip()
        
        try:
            return Decimal(cleaned)
        except:
            return Decimal('0')


# ========== 便捷函数 ==========

def parse_pdf_file(pdf_path: str, file_type: str = 'auto') -> Dict:
    """
    便捷函数：解析PDF文件
    
    Args:
        pdf_path: PDF文件路径
        file_type: 文件类型 ('bank-statement', 'supplier-invoice', 'pos-report', 'auto')
    
    Returns:
        解析结果字典
    """
    parser = PDFParser(enable_ocr=True)
    
    if file_type == 'bank-statement':
        return parser.extract_bank_statement(pdf_path)
    elif file_type == 'supplier-invoice':
        return parser.extract_supplier_invoice(pdf_path)
    elif file_type == 'pos-report':
        return parser.extract_pos_report(pdf_path)
    else:
        # 自动检测类型
        result = parser.parse(pdf_path)
        return result.to_dict()


def validate_parse_result(result: Dict, min_confidence: float = 0.3) -> Tuple[bool, Optional[str]]:
    """
    验证解析结果是否可用
    
    Returns:
        (is_valid, reason)
    """
    if not result.get('success'):
        return False, result.get('error', '解析失败')
    
    confidence = result.get('confidence', 0)
    if confidence < min_confidence:
        return False, f'置信度过低: {confidence:.2f} < {min_confidence}'
    
    return True, None
