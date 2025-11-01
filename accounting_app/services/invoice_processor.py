"""
供应商发票处理服务
处理发票上传、解析、会计分录生成、Aging更新
"""
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date, datetime, timedelta
import re
import logging

from ..models import (
    PurchaseInvoice, Supplier, JournalEntry, JournalEntryLine,
    ChartOfAccounts, Company
)
from .pdf_parser import PDFParser

logger = logging.getLogger(__name__)


class InvoiceProcessor:
    """
    供应商发票处理器
    
    功能：
    1. 解析发票内容（PDF/Excel/JPG）
    2. 检测重复发票
    3. 自动生成会计分录
    4. 更新Aging报表状态
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.pdf_parser = PDFParser()
    
    def process_invoice_file(
        self,
        company_id: int,
        file_content: bytes,
        filename: str,
        file_type: str  # 'pdf', 'excel', 'image'
    ) -> Dict:
        """
        处理发票文件（完整流程）
        
        Returns:
            {
                "success": True/False,
                "invoice_id": 123,
                "invoice_number": "INV-2025-001",
                "parsed_data": {...},
                "journal_entry_id": 456,
                "duplicate_check": {...}
            }
        """
        logger.info(f"开始处理发票: company_id={company_id}, file={filename}, type={file_type}")
        
        # 1. 解析文件内容
        parsed_data = self._parse_invoice_content(file_content, file_type)
        
        if not parsed_data["success"]:
            return {
                "success": False,
                "error": "发票解析失败",
                "details": parsed_data
            }
        
        # 2. 检测重复发票（双层检测：发票号 + 复合指纹）
        duplicate_check = self._check_duplicate_invoice(
            company_id,
            parsed_data.get("invoice_number"),
            parsed_data.get("supplier_name"),
            parsed_data.get("invoice_date"),
            parsed_data.get("total_amount")
        )
        
        if duplicate_check["is_duplicate"]:
            logger.warning(f"检测到重复发票: {parsed_data.get('invoice_number')}")
            return {
                "success": False,
                "error": "重复发票",
                "duplicate_check": duplicate_check,
                "parsed_data": parsed_data
            }
        
        # 3-7. 事务处理：创建供应商、发票、会计分录
        try:
            # 3. 创建或获取供应商
            supplier = self._get_or_create_supplier(
                company_id,
                parsed_data.get("supplier_name", "Unknown Supplier"),
                parsed_data.get("supplier_info", {})
            )
            
            # 4. 创建发票记录
            invoice = self._create_purchase_invoice(
                company_id=company_id,
                supplier_id=supplier.id,
                invoice_data=parsed_data
            )
            
            # 5. 生成会计分录
            journal_entry = self._create_journal_entry_for_invoice(
                company_id=company_id,
                invoice=invoice,
                supplier=supplier
            )
            
            # 6. 更新发票的journal_entry_id
            invoice.journal_entry_id = journal_entry.id
            
            # 7. 更新Aging状态
            self._update_aging_status(invoice)
            
            # 提交事务
            self.db.commit()
            
        except Exception as e:
            # 回滚事务
            self.db.rollback()
            logger.error(f"发票处理失败，事务已回滚: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "发票处理失败",
                "details": str(e)
            }
        
        logger.info(f"发票处理成功: invoice_id={invoice.id}, journal_id={journal_entry.id}")
        
        return {
            "success": True,
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "supplier_name": supplier.supplier_name,
            "total_amount": float(invoice.total_amount),
            "journal_entry_id": journal_entry.id,
            "journal_entry_number": journal_entry.entry_number,
            "parsed_data": parsed_data,
            "duplicate_check": duplicate_check
        }
    
    def _parse_invoice_content(self, file_content: bytes, file_type: str) -> Dict:
        """
        解析发票内容
        
        使用3段式PDF解析器
        """
        if file_type == 'pdf':
            # 使用PDFParser（3段式：文本→OCR→待处理）
            pdf_result = self.pdf_parser.parse_pdf(file_content)
            
            if pdf_result["stage"] == "text_extracted":
                # 成功提取文本，进行结构化解析
                extracted_data = self._extract_invoice_fields(pdf_result["text"])
                return {
                    "success": True,
                    "stage": "parsed",
                    **extracted_data
                }
            elif pdf_result["stage"] == "ocr_extracted":
                # OCR提取成功
                extracted_data = self._extract_invoice_fields(pdf_result["text"])
                return {
                    "success": True,
                    "stage": "ocr_parsed",
                    **extracted_data
                }
            else:
                # 解析失败，标记为pending
                return {
                    "success": False,
                    "stage": "pending",
                    "error": "PDF解析失败，需要人工处理"
                }
        
        elif file_type == 'image':
            # 图片：直接OCR
            ocr_result = self.pdf_parser._perform_ocr(file_content)
            if ocr_result["success"]:
                extracted_data = self._extract_invoice_fields(ocr_result["text"])
                return {
                    "success": True,
                    "stage": "ocr_parsed",
                    **extracted_data
                }
            else:
                return {
                    "success": False,
                    "stage": "pending",
                    "error": "OCR失败"
                }
        
        elif file_type == 'excel':
            # Excel/CSV解析
            try:
                import io
                import pandas as pd
                
                # 智能判断文件类型（使用magic bytes和扩展名）
                # .xlsx: PK (zip), .xls: D0CF11E0 (OLE), .csv: 文本
                if file_content.startswith(b'PK'):
                    # .xlsx (Office Open XML)
                    df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
                elif file_content.startswith(b'\xd0\xcf\x11\xe0'):
                    # .xls (OLE2/BIFF)
                    df = pd.read_excel(io.BytesIO(file_content), engine='xlrd')
                else:
                    # .csv (默认)
                    df = pd.read_csv(io.BytesIO(file_content))
                
                # 提取发票信息（假设第一行是header，第二行是数据）
                if len(df) == 0:
                    return {
                        "success": False,
                        "stage": "pending",
                        "error": "Excel文件为空"
                    }
                
                # 智能匹配列名
                extracted_data = self._extract_from_dataframe(df)
                return {
                    "success": True,
                    "stage": "excel_parsed",
                    **extracted_data
                }
            except Exception as e:
                logger.error(f"Excel解析失败: {str(e)}")
                return {
                    "success": False,
                    "stage": "pending",
                    "error": f"Excel解析失败: {str(e)}"
                }
        
        else:
            return {
                "success": False,
                "error": f"不支持的文件类型: {file_type}"
            }
    
    def _extract_from_dataframe(self, df) -> Dict:
        """
        从DataFrame中提取发票字段
        
        智能匹配常见列名
        """
        import pandas as pd
        
        extracted = {
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "total_amount": None,
            "supplier_name": None,
            "supplier_info": {}
        }
        
        # 列名映射（不区分大小写）
        column_mapping = {
            'invoice_number': ['invoice number', 'invoice no', 'inv no', 'invoice_no', 'number'],
            'invoice_date': ['invoice date', 'date', 'inv date', 'invoice_date'],
            'due_date': ['due date', 'payment due', 'due_date'],
            'total_amount': ['total', 'amount', 'total amount', 'grand total', 'invoice amount'],
            'supplier_name': ['supplier', 'vendor', 'supplier name', 'vendor name', 'from']
        }
        
        # 标准化列名（转小写）
        df.columns = [str(col).lower().strip() for col in df.columns]
        
        # 匹配字段
        for field, possible_names in column_mapping.items():
            for col_name in possible_names:
                if col_name in df.columns and not df[col_name].empty:
                    value = df[col_name].iloc[0]
                    
                    if pd.notna(value):
                        if field in ['invoice_date', 'due_date']:
                            # 日期字段
                            try:
                                extracted[field] = pd.to_datetime(value).date()
                            except:
                                pass
                        elif field == 'total_amount':
                            # 金额字段
                            try:
                                # 移除货币符号和逗号
                                amount_str = str(value).replace('RM', '').replace(',', '').strip()
                                extracted[field] = Decimal(amount_str)
                            except:
                                pass
                        else:
                            # 文本字段
                            extracted[field] = str(value).strip()[:200]
                    break
        
        # 默认值
        if not extracted["invoice_number"]:
            extracted["invoice_number"] = f"EXCEL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if not extracted["invoice_date"]:
            extracted["invoice_date"] = date.today()
        
        if not extracted["due_date"]:
            extracted["due_date"] = extracted["invoice_date"] + timedelta(days=30)
        
        if not extracted["total_amount"]:
            extracted["total_amount"] = Decimal('0.00')
        
        if not extracted["supplier_name"]:
            extracted["supplier_name"] = "Unknown Supplier"
        
        return extracted
    
    def _extract_invoice_fields(self, text: str) -> Dict:
        """
        从文本中提取发票字段
        
        使用正则表达式匹配常见发票格式
        """
        extracted = {
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "total_amount": None,
            "supplier_name": None,
            "supplier_info": {}
        }
        
        # 发票号码（多种格式）
        invoice_patterns = [
            r'Invoice\s*(?:No|Number|#)?[\s:]*([A-Z0-9\-/]+)',
            r'INV[\s\-]*([A-Z0-9\-/]+)',
            r'Bill\s*(?:No|Number)?[\s:]*([A-Z0-9\-/]+)'
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted["invoice_number"] = match.group(1).strip()
                break
        
        # 日期（多种格式）
        date_patterns = [
            r'Date[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Invoice Date[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                extracted["invoice_date"] = self._parse_date(date_str)
                break
        
        # 总金额（多种格式）
        amount_patterns = [
            r'Total[\s:]*RM?[\s]*([\d,]+\.?\d*)',
            r'Amount[\s:]*RM?[\s]*([\d,]+\.?\d*)',
            r'Grand Total[\s:]*RM?[\s]*([\d,]+\.?\d*)',
            r'RM[\s]*([\d,]+\.?\d*)'
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    extracted["total_amount"] = Decimal(amount_str)
                    break
                except:
                    pass
        
        # 供应商名称（第一行通常是供应商名）
        lines = text.split('\n')
        if lines:
            extracted["supplier_name"] = lines[0].strip()[:100]
        
        # 默认值
        if not extracted["invoice_number"]:
            extracted["invoice_number"] = f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if not extracted["invoice_date"]:
            extracted["invoice_date"] = date.today()
        
        if not extracted["due_date"]:
            extracted["due_date"] = extracted["invoice_date"] + timedelta(days=30)
        
        if not extracted["total_amount"]:
            extracted["total_amount"] = Decimal('0.00')
        
        return extracted
    
    def _parse_date(self, date_str: str) -> date:
        """
        解析日期字符串
        """
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        
        return date.today()
    
    def _check_duplicate_invoice(
        self,
        company_id: int,
        invoice_number: Optional[str],
        supplier_name: Optional[str],
        invoice_date: Optional[date] = None,
        total_amount: Optional[Decimal] = None
    ) -> Dict:
        """
        检测重复发票（双层检测）
        
        策略1：如果有真实发票号（非AUTO-），检查发票号是否重复
        策略2：如果是AUTO-号或无发票号，使用复合指纹（supplier+date+amount）
        
        这样可以：
        - 防止真实发票号重复
        - 防止OCR失败时同一张发票被重复上传
        """
        # 策略1：真实发票号检测
        if invoice_number and not invoice_number.startswith(("AUTO-", "EXCEL-")):
            existing = self.db.query(PurchaseInvoice).filter(
                PurchaseInvoice.company_id == company_id,
                PurchaseInvoice.invoice_number == invoice_number
            ).first()
            
            if existing:
                return {
                    "is_duplicate": True,
                    "detection_method": "invoice_number",
                    "existing_invoice_id": existing.id,
                    "existing_invoice_number": existing.invoice_number,
                    "existing_invoice_date": existing.invoice_date.isoformat(),
                    "message": f"发票号 {invoice_number} 已存在"
                }
        
        # 策略2：复合指纹检测（supplier + date + amount）
        # 防止OCR失败时的重复上传
        if supplier_name and invoice_date and total_amount:
            # 查找供应商
            supplier = self.db.query(Supplier).filter(
                Supplier.company_id == company_id,
                Supplier.supplier_name == supplier_name
            ).first()
            
            if supplier:
                # 检查是否存在相同的 supplier + date + amount
                existing = self.db.query(PurchaseInvoice).filter(
                    PurchaseInvoice.company_id == company_id,
                    PurchaseInvoice.supplier_id == supplier.id,
                    PurchaseInvoice.invoice_date == invoice_date,
                    PurchaseInvoice.total_amount == total_amount
                ).first()
                
                if existing:
                    return {
                        "is_duplicate": True,
                        "detection_method": "composite_fingerprint",
                        "existing_invoice_id": existing.id,
                        "existing_invoice_number": existing.invoice_number,
                        "existing_invoice_date": existing.invoice_date.isoformat(),
                        "message": f"已存在相同供应商、日期和金额的发票 (ID: {existing.id})"
                    }
        
        return {"is_duplicate": False}
    
    def _get_or_create_supplier(
        self,
        company_id: int,
        supplier_name: str,
        supplier_info: Dict = None
    ) -> Supplier:
        """
        获取或创建供应商
        """
        # 查询是否已存在
        existing = self.db.query(Supplier).filter(
            Supplier.company_id == company_id,
            Supplier.supplier_name == supplier_name
        ).first()
        
        if existing:
            return existing
        
        # 创建新供应商
        supplier_code = self._generate_supplier_code(company_id, supplier_name)
        
        supplier = Supplier(
            company_id=company_id,
            supplier_code=supplier_code,
            supplier_name=supplier_name,
            contact_person=supplier_info.get("contact") if supplier_info else None,
            phone=supplier_info.get("phone") if supplier_info else None,
            email=supplier_info.get("email") if supplier_info else None,
            status='active'
        )
        
        self.db.add(supplier)
        self.db.flush()  # 使用flush而非commit，保持事务
        self.db.refresh(supplier)
        
        logger.info(f"创建新供应商: {supplier_code} - {supplier_name}")
        
        return supplier
    
    def _generate_supplier_code(self, company_id: int, supplier_name: str) -> str:
        """
        生成供应商代码
        """
        # 使用供应商名称首字母 + 序号
        prefix = ''.join([c[0] for c in supplier_name.split()[:2]]).upper()
        if not prefix:
            prefix = "SUP"
        
        # 查询现有供应商数量
        count = self.db.query(Supplier).filter(
            Supplier.company_id == company_id
        ).count()
        
        return f"{prefix}{count + 1:04d}"
    
    def _create_purchase_invoice(
        self,
        company_id: int,
        supplier_id: int,
        invoice_data: Dict
    ) -> PurchaseInvoice:
        """
        创建购买发票记录
        """
        invoice = PurchaseInvoice(
            company_id=company_id,
            supplier_id=supplier_id,
            invoice_number=invoice_data["invoice_number"],
            invoice_date=invoice_data["invoice_date"],
            due_date=invoice_data.get("due_date") or invoice_data["invoice_date"] + timedelta(days=30),
            total_amount=invoice_data["total_amount"],
            paid_amount=Decimal('0.00'),
            balance_amount=invoice_data["total_amount"],
            status='unpaid'
        )
        
        self.db.add(invoice)
        self.db.flush()  # 使用flush而非commit，保持事务
        self.db.refresh(invoice)
        
        return invoice
    
    def _create_journal_entry_for_invoice(
        self,
        company_id: int,
        invoice: PurchaseInvoice,
        supplier: Supplier
    ) -> JournalEntry:
        """
        为发票生成会计分录
        
        会计分录规则（购买发票）：
        借：费用/资产科目（根据规则匹配）
        贷：应付账款（Accounts Payable）
        """
        # 生成分录号
        entry_number = self._generate_journal_entry_number(company_id)
        
        # 创建分录主表
        journal_entry = JournalEntry(
            company_id=company_id,
            entry_number=entry_number,
            entry_date=invoice.invoice_date,
            description=f"Purchase Invoice {invoice.invoice_number} - {supplier.supplier_name}",
            entry_type='invoice',
            reference_number=invoice.invoice_number,
            status='posted'
        )
        
        self.db.add(journal_entry)
        self.db.flush()
        
        # 获取会计科目
        expense_account = self._get_or_create_account(company_id, 'EXPENSE', 'Purchases')
        ap_account = self._get_or_create_account(company_id, 'LIABILITY', 'Accounts Payable')
        
        # 借方：费用
        debit_line = JournalEntryLine(
            journal_entry_id=journal_entry.id,
            account_id=expense_account.id,
            description=f"Purchase from {supplier.supplier_name}",
            debit_amount=invoice.total_amount,
            credit_amount=Decimal('0.00'),
            line_number=1
        )
        
        # 贷方：应付账款
        credit_line = JournalEntryLine(
            journal_entry_id=journal_entry.id,
            account_id=ap_account.id,
            description=f"Amount payable to {supplier.supplier_name}",
            debit_amount=Decimal('0.00'),
            credit_amount=invoice.total_amount,
            line_number=2
        )
        
        self.db.add(debit_line)
        self.db.add(credit_line)
        self.db.flush()  # 使用flush而非commit，保持事务
        self.db.refresh(journal_entry)
        
        logger.info(f"生成会计分录: {entry_number}, 金额: {invoice.total_amount}")
        
        return journal_entry
    
    def _generate_journal_entry_number(self, company_id: int) -> str:
        """
        生成分录号
        """
        # 格式：JE-YYYYMM-NNNN
        prefix = datetime.now().strftime('JE-%Y%m-')
        
        # 查询本月已有分录数量
        count = self.db.query(JournalEntry).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.entry_number.like(f'{prefix}%')
        ).count()
        
        return f"{prefix}{count + 1:04d}"
    
    def _get_or_create_account(
        self,
        company_id: int,
        account_type: str,
        account_name: str
    ) -> ChartOfAccounts:
        """
        获取或创建会计科目
        """
        # 查询现有科目
        existing = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.company_id == company_id,
            ChartOfAccounts.account_name == account_name
        ).first()
        
        if existing:
            return existing
        
        # 生成科目代码
        type_prefixes = {
            'ASSET': '1',
            'LIABILITY': '2',
            'EQUITY': '3',
            'INCOME': '4',
            'EXPENSE': '5'
        }
        
        prefix = type_prefixes.get(account_type.upper(), '9')
        count = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.company_id == company_id,
            ChartOfAccounts.account_type == account_type.lower()
        ).count()
        
        account_code = f"{prefix}{count + 1:03d}"
        
        # 创建新科目
        account = ChartOfAccounts(
            company_id=company_id,
            account_code=account_code,
            account_name=account_name,
            account_type=account_type.lower(),
            is_active=True
        )
        
        self.db.add(account)
        self.db.flush()  # 使用flush而非commit，保持事务
        self.db.refresh(account)
        
        return account
    
    def _update_aging_status(self, invoice: PurchaseInvoice):
        """
        更新Aging状态
        
        根据due_date自动更新status：
        - 未到期：unpaid
        - 已逾期：overdue
        
        注意：不commit，由外层事务统一提交
        """
        if invoice.balance_amount > 0 and invoice.due_date < date.today():
            invoice.status = 'overdue'
            # 不commit，由外层事务统一处理


# ========== 便捷函数 ==========

def process_supplier_invoice(
    db: Session,
    company_id: int,
    file_content: bytes,
    filename: str
) -> Dict:
    """
    便捷函数：处理供应商发票
    
    自动识别文件类型并处理
    """
    # 识别文件类型
    if filename.lower().endswith('.pdf'):
        file_type = 'pdf'
    elif filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        file_type = 'image'
    elif filename.lower().endswith(('.xlsx', '.xls', '.csv')):
        file_type = 'excel'
    else:
        return {
            "success": False,
            "error": f"不支持的文件类型: {filename}"
        }
    
    processor = InvoiceProcessor(db)
    return processor.process_invoice_file(company_id, file_content, filename, file_type)
