"""
数据完整性验证器
1:1原件保护系统：确保所有业务记录都关联到原始文档
防止虚构交易和数据篡改
"""
from sqlalchemy import select, and_
from accounting_app.db import SessionLocal
from accounting_app.models import (
    BankStatement, JournalEntryLine, PurchaseInvoice, SalesInvoice,
    RawDocument, RawLine, Exception as ExceptionModel
)
from datetime import datetime
from typing import Optional, Dict, List, Tuple


class DataIntegrityValidator:
    """
    数据完整性验证器
    四层数据保护：
    1. 原始文档必须存在 (raw_documents)
    2. 原始行数据必须存在 (raw_lines)
    3. 业务记录必须关联raw_line_id
    4. 禁止孤儿记录（没有源文档的业务记录）
    """
    
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        self.db = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()
    
    def validate_bank_statement(self, statement_id: int, company_id: int) -> Tuple[bool, Optional[str]]:
        """
        验证银行对账单的数据完整性（四层保护）
        
        Returns:
            (is_valid, error_message)
        """
        stmt = select(BankStatement).where(
            and_(
                BankStatement.id == statement_id,
                BankStatement.company_id == company_id
            )
        )
        result = self.db.execute(stmt)
        bank_statement = result.scalar_one_or_none()
        
        if not bank_statement:
            return False, "银行对账单不存在 / Bank statement not found"
        
        if not bank_statement.raw_line_id:
            return False, "缺少原始文档关联 / Missing source document link (raw_line_id)"
        
        stmt = select(RawLine).where(RawLine.id == bank_statement.raw_line_id)
        result = self.db.execute(stmt)
        raw_line = result.scalar_one_or_none()
        
        if not raw_line:
            return False, "原始文档行不存在 / Source document line not found"
        
        stmt = select(RawDocument).where(RawDocument.id == raw_line.raw_document_id)
        result = self.db.execute(stmt)
        raw_document = result.scalar_one_or_none()
        
        if not raw_document:
            return False, "原始文档不存在 / Source document not found"
        
        if raw_document.company_id != company_id:
            return False, "原始文档不属于此公司 / Source document does not belong to this company"
        
        return True, None
    
    def validate_purchase_invoice(self, invoice_id: int, company_id: int) -> Tuple[bool, Optional[str]]:
        """验证采购发票的数据完整性（四层保护）"""
        stmt = select(PurchaseInvoice).where(
            and_(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.company_id == company_id
            )
        )
        result = self.db.execute(stmt)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return False, "采购发票不存在 / Purchase invoice not found"
        
        if not invoice.raw_line_id:
            return False, "缺少原始文档关联 / Missing source document link (raw_line_id)"
        
        stmt = select(RawLine).where(RawLine.id == invoice.raw_line_id)
        result = self.db.execute(stmt)
        raw_line = result.scalar_one_or_none()
        
        if not raw_line:
            return False, "原始文档行不存在 / Source document line not found"
        
        stmt = select(RawDocument).where(RawDocument.id == raw_line.raw_document_id)
        result = self.db.execute(stmt)
        raw_document = result.scalar_one_or_none()
        
        if not raw_document:
            return False, "原始文档不存在 / Source document not found"
        
        if raw_document.company_id != company_id:
            return False, "原始文档不属于此公司 / Source document does not belong to this company"
        
        return True, None
    
    def validate_sales_invoice(self, invoice_id: int, company_id: int) -> Tuple[bool, Optional[str]]:
        """验证销售发票的数据完整性（四层保护）"""
        stmt = select(SalesInvoice).where(
            and_(
                SalesInvoice.id == invoice_id,
                SalesInvoice.company_id == company_id
            )
        )
        result = self.db.execute(stmt)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return False, "销售发票不存在 / Sales invoice not found"
        
        if not invoice.raw_line_id:
            return False, "缺少原始文档关联 / Missing source document link (raw_line_id)"
        
        stmt = select(RawLine).where(RawLine.id == invoice.raw_line_id)
        result = self.db.execute(stmt)
        raw_line = result.scalar_one_or_none()
        
        if not raw_line:
            return False, "原始文档行不存在 / Source document line not found"
        
        stmt = select(RawDocument).where(RawDocument.id == raw_line.raw_document_id)
        result = self.db.execute(stmt)
        raw_document = result.scalar_one_or_none()
        
        if not raw_document:
            return False, "原始文档不存在 / Source document not found"
        
        if raw_document.company_id != company_id:
            return False, "原始文档不属于此公司 / Source document does not belong to this company"
        
        return True, None
    
    def validate_journal_entry_line(self, line_id: int, company_id: int) -> Tuple[bool, Optional[str]]:
        """验证记账分录行的数据完整性（四层保护）"""
        stmt = select(JournalEntryLine).where(JournalEntryLine.id == line_id)
        result = self.db.execute(stmt)
        line = result.scalar_one_or_none()
        
        if not line:
            return False, "记账分录行不存在 / Journal entry line not found"
        
        if not line.raw_line_id:
            return False, "缺少原始文档关联 / Missing source document link (raw_line_id)"
        
        stmt = select(RawLine).where(RawLine.id == line.raw_line_id)
        result = self.db.execute(stmt)
        raw_line = result.scalar_one_or_none()
        
        if not raw_line:
            return False, "原始文档行不存在 / Source document line not found"
        
        if not raw_line.raw_document_id:
            return False, "原始文档行缺少文档关联 / Raw line missing document link"
        
        stmt = select(RawDocument).where(RawDocument.id == raw_line.raw_document_id)
        result = self.db.execute(stmt)
        raw_document = result.scalar_one_or_none()
        
        if not raw_document:
            return False, "原始文档不存在 / Source document not found"
        
        return True, None
    
    def find_orphan_records(self, entity_type: str, company_id: int) -> List[Dict]:
        """
        查找孤儿记录（没有关联原始文档的业务记录）
        
        Args:
            entity_type: 'bank_statement', 'purchase_invoice', 'sales_invoice', 'journal_entry_line'
            company_id: 公司ID
        
        Returns:
            孤儿记录列表
        """
        orphans = []
        
        if entity_type == 'bank_statement':
            stmt = select(BankStatement).where(
                and_(
                    BankStatement.company_id == company_id,
                    BankStatement.raw_line_id.is_(None)
                )
            )
            result = self.db.execute(stmt)
            for record in result.scalars():
                orphans.append({
                    'id': record.id,
                    'type': 'bank_statement',
                    'date': record.transaction_date,
                    'amount': float(record.amount) if record.amount else 0,
                    'description': record.description
                })
        
        elif entity_type == 'purchase_invoice':
            stmt = select(PurchaseInvoice).where(
                and_(
                    PurchaseInvoice.company_id == company_id,
                    PurchaseInvoice.raw_line_id.is_(None)
                )
            )
            result = self.db.execute(stmt)
            for record in result.scalars():
                orphans.append({
                    'id': record.id,
                    'type': 'purchase_invoice',
                    'date': record.invoice_date,
                    'amount': float(record.total_amount) if record.total_amount else 0,
                    'supplier': record.supplier_name
                })
        
        elif entity_type == 'sales_invoice':
            stmt = select(SalesInvoice).where(
                and_(
                    SalesInvoice.company_id == company_id,
                    SalesInvoice.raw_line_id.is_(None)
                )
            )
            result = self.db.execute(stmt)
            for record in result.scalars():
                orphans.append({
                    'id': record.id,
                    'type': 'sales_invoice',
                    'date': record.invoice_date,
                    'amount': float(record.total_amount) if record.total_amount else 0,
                    'customer': record.customer_name
                })
        
        elif entity_type == 'journal_entry_line':
            stmt = select(JournalEntryLine).where(
                JournalEntryLine.raw_line_id.is_(None)
            )
            result = self.db.execute(stmt)
            for record in result.scalars():
                orphans.append({
                    'id': record.id,
                    'type': 'journal_entry_line',
                    'account': record.account_code,
                    'debit': float(record.debit_amount) if record.debit_amount else 0,
                    'credit': float(record.credit_amount) if record.credit_amount else 0
                })
        
        return orphans
    
    def create_exception_for_orphan(self, orphan: Dict, company_id: int) -> int:
        """
        为孤儿记录创建异常
        
        Returns:
            Exception ID
        """
        exception = ExceptionModel(
            company_id=company_id,
            exception_type='missing_source',
            severity='high',
            source_type=orphan['type'],
            source_id=orphan['id'],
            description=f"孤儿记录：{orphan['type']} #{orphan['id']} 缺少原始文档关联 / Orphan record: missing source document link",
            status='new',
            next_action='upload_new_file',
            retryable=False
        )
        
        self.db.add(exception)
        self.db.commit()
        
        return exception.id
    
    def scan_all_orphans(self, company_id: int) -> Dict[str, List[Dict]]:
        """
        扫描所有孤儿记录
        
        Returns:
            {
                'bank_statement': [...],
                'purchase_invoice': [...],
                'sales_invoice': [...],
                'journal_entry_line': [...]
            }
        """
        entity_types = ['bank_statement', 'purchase_invoice', 'sales_invoice', 'journal_entry_line']
        
        all_orphans = {}
        for entity_type in entity_types:
            orphans = self.find_orphan_records(entity_type, company_id)
            all_orphans[entity_type] = orphans
        
        return all_orphans
    
    def enforce_integrity_on_create(self, entity_type: str, raw_line_id: Optional[int], company_id: int) -> Tuple[bool, Optional[str]]:
        """
        在创建业务记录时强制执行完整性检查（四层保护）
        
        Args:
            entity_type: 实体类型
            raw_line_id: 原始文档行ID
            company_id: 公司ID
        
        Returns:
            (is_valid, error_message)
        """
        if not raw_line_id:
            exception = ExceptionModel(
                company_id=company_id,
                exception_type='ingest_validation_failed',
                severity='critical',
                source_type=entity_type,
                description=f"创建 {entity_type} 时缺少 raw_line_id / Missing raw_line_id when creating {entity_type}",
                status='new',
                next_action='upload_new_file',
                retryable=False
            )
            self.db.add(exception)
            self.db.commit()
            
            return False, "必须关联原始文档 / Source document link required"
        
        stmt = select(RawLine).where(RawLine.id == raw_line_id)
        result = self.db.execute(stmt)
        raw_line = result.scalar_one_or_none()
        
        if not raw_line:
            exception = ExceptionModel(
                company_id=company_id,
                exception_type='missing_source',
                severity='critical',
                source_type=entity_type,
                description=f"RawLine {raw_line_id} 不存在 / RawLine not found",
                status='new',
                next_action='upload_new_file',
                retryable=False
            )
            self.db.add(exception)
            self.db.commit()
            
            return False, f"原始文档行 {raw_line_id} 不存在 / Source document line not found"
        
        if not raw_line.raw_document_id:
            return False, "原始文档行缺少文档关联 / Raw line missing document link"
        
        stmt = select(RawDocument).where(RawDocument.id == raw_line.raw_document_id)
        result = self.db.execute(stmt)
        raw_document = result.scalar_one_or_none()
        
        if not raw_document:
            exception = ExceptionModel(
                company_id=company_id,
                exception_type='missing_source',
                severity='critical',
                source_type=entity_type,
                description=f"RawDocument {raw_line.raw_document_id} 不存在 / RawDocument not found",
                status='new',
                next_action='upload_new_file',
                retryable=False
            )
            self.db.add(exception)
            self.db.commit()
            
            return False, "原始文档不存在 / Source document not found"
        
        if raw_document.company_id != company_id:
            return False, "原始文档不属于此公司 / Source document does not belong to this company"
        
        return True, None


def validate_business_record(entity_type: str, entity_id: int, company_id: int) -> Dict:
    """
    快捷函数：验证业务记录的数据完整性
    
    Returns:
        {
            'is_valid': bool,
            'error_message': str or None,
            'has_source_document': bool,
            'source_document_path': str or None
        }
    """
    with DataIntegrityValidator() as validator:
        if entity_type == 'bank_statement':
            is_valid, error = validator.validate_bank_statement(entity_id, company_id)
        elif entity_type == 'purchase_invoice':
            is_valid, error = validator.validate_purchase_invoice(entity_id, company_id)
        elif entity_type == 'sales_invoice':
            is_valid, error = validator.validate_sales_invoice(entity_id, company_id)
        elif entity_type == 'journal_entry_line':
            is_valid, error = validator.validate_journal_entry_line(entity_id, company_id)
        else:
            return {
                'is_valid': False,
                'error_message': f'不支持的实体类型: {entity_type}',
                'has_source_document': False,
                'source_document_path': None
            }
        
        return {
            'is_valid': is_valid,
            'error_message': error,
            'has_source_document': is_valid,
            'source_document_path': None  # TODO: 从RawDocument获取文件路径
        }
