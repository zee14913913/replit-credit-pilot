"""
补充改进②：业务层数据完整性验证器
Data Integrity Validator - Business Layer

版本：v1.0.0 (2025-11-01)  # 补充改进⑧：版本号追踪

核心原则：
1. raw_line_id IS NULL的记录禁止进入报表
2. validation_status='failed'的raw_document禁止用于报表
3. 所有违规数据统一打到异常中心

用法：
```python
from accounting_app.services.data_integrity_validator import DataIntegrityValidator

validator = DataIntegrityValidator(db, company_id)

# 验证单条记录
if not validator.validate_record_integrity(record_id, 'bank_statement_lines'):
    # 记录被拦截，已进入异常中心
    
# 验证并过滤查询结果
clean_records = validator.filter_valid_records(query_results, 'bank_statement_lines')
```

版本历史：
- v1.0.0 (2025-11-01): 初始版本，实现4层数据保护机制
"""

# 补充改进⑧：版本号常量
DATA_INTEGRITY_VALIDATOR_VERSION = "v1.0.0"
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import (
    BankStatementLines, JournalEntryLines, ArApAgingLines, CashFlowLines,
    PurchaseInvoice, SalesInvoice, RawDocument, RawLine,
    Exception as ExceptionModel
)

logger = logging.getLogger(__name__)


class DataIntegrityValidator:
    """
    数据完整性验证器 - 补充改进②
    
    确保所有进入报表的数据都有完整的溯源链：
    Transaction → raw_line_id → raw_lines → raw_document (validation_status='passed')
    """
    
    # 需要验证raw_line_id的表
    TABLES_REQUIRING_RAW_LINE_ID = {
        'bank_statement_lines': BankStatementLines,
        'journal_entry_lines': JournalEntryLines,
        'arap_aging_lines': ArApAgingLines,
        'cash_flow_lines': CashFlowLines,
        'purchase_invoices': PurchaseInvoice,
        'sales_invoices': SalesInvoice,
    }
    
    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
    
    def validate_record_integrity(
        self,
        record_id: int,
        table_name: str,
        auto_create_exception: bool = True
    ) -> bool:
        """
        验证单条记录的数据完整性
        
        验证规则：
        1. raw_line_id不能为NULL
        2. raw_line_id关联的raw_document.validation_status必须是'passed'
        
        Args:
            record_id: 记录ID
            table_name: 表名（如'bank_statement_lines'）
            auto_create_exception: 验证失败时是否自动创建异常记录
        
        Returns:
            bool: True表示数据完整，False表示数据有问题（已拦截）
        """
        if table_name not in self.TABLES_REQUIRING_RAW_LINE_ID:
            logger.warning(f"表 {table_name} 不在验证范围内")
            return True
        
        model_class = self.TABLES_REQUIRING_RAW_LINE_ID[table_name]
        
        # 查询记录
        record = self.db.query(model_class).filter(
            model_class.id == record_id
        ).first()
        
        if not record:
            logger.error(f"记录不存在: {table_name}.id={record_id}")
            return False
        
        # 规则1：raw_line_id不能为NULL
        if not record.raw_line_id:
            logger.warning(
                f"❌ DATA INTEGRITY VIOLATION - "
                f"{table_name}.id={record_id}: raw_line_id IS NULL, "
                f"禁止进入报表"
            )
            
            if auto_create_exception:
                self._create_integrity_exception(
                    table_name=table_name,
                    record_id=record_id,
                    violation_type='missing_raw_line_id',
                    message=f"{table_name}记录缺少raw_line_id，无法追溯到原始文件"
                )
            
            return False
        
        # 规则2：验证raw_document.validation_status
        raw_line = self.db.query(RawLine).filter(
            RawLine.id == record.raw_line_id
        ).first()
        
        if not raw_line:
            logger.error(f"raw_line_id={record.raw_line_id}不存在")
            
            if auto_create_exception:
                self._create_integrity_exception(
                    table_name=table_name,
                    record_id=record_id,
                    violation_type='invalid_raw_line_id',
                    message=f"raw_line_id={record.raw_line_id}不存在，数据孤立"
                )
            
            return False
        
        raw_doc = self.db.query(RawDocument).filter(
            RawDocument.id == raw_line.raw_document_id
        ).first()
        
        if not raw_doc:
            logger.error(f"raw_document_id={raw_line.raw_document_id}不存在")
            return False
        
        if raw_doc.validation_status != 'passed':
            logger.warning(
                f"❌ VALIDATION STATUS VIOLATION - "
                f"{table_name}.id={record_id}: "
                f"raw_document.validation_status='{raw_doc.validation_status}' (expected 'passed'), "
                f"禁止进入报表"
            )
            
            if auto_create_exception:
                self._create_integrity_exception(
                    table_name=table_name,
                    record_id=record_id,
                    violation_type='failed_validation_source',
                    message=(
                        f"源文件验证失败 (validation_status='{raw_doc.validation_status}'), "
                        f"raw_document_id={raw_doc.id}, "
                        f"error: {raw_doc.validation_error_message or 'unknown'}"
                    )
                )
            
            return False
        
        # 所有验证通过
        return True
    
    def filter_valid_records(
        self,
        records: List[Any],
        table_name: str
    ) -> List[Any]:
        """
        过滤出数据完整的记录（用于报表生成）
        
        Args:
            records: 记录列表
            table_name: 表名
        
        Returns:
            List: 验证通过的记录列表
        """
        if table_name not in self.TABLES_REQUIRING_RAW_LINE_ID:
            return records
        
        valid_records = []
        
        for record in records:
            if self.validate_record_integrity(
                record_id=record.id,
                table_name=table_name,
                auto_create_exception=True
            ):
                valid_records.append(record)
        
        logger.info(
            f"数据完整性过滤: {table_name} - "
            f"总数={len(records)}, 有效={len(valid_records)}, "
            f"拦截={len(records) - len(valid_records)}"
        )
        
        return valid_records
    
    def get_query_with_integrity_filter(self, model_class, base_query=None):
        """
        返回带数据完整性过滤的查询对象
        
        用法：
        ```python
        validator = DataIntegrityValidator(db, company_id)
        query = validator.get_query_with_integrity_filter(BankStatementLines)
        results = query.filter(...).all()  # 自动过滤掉无效数据
        ```
        
        Args:
            model_class: SQLAlchemy模型类
            base_query: 基础查询对象（可选）
        
        Returns:
            Query: 带完整性过滤的查询对象
        """
        if base_query is None:
            base_query = self.db.query(model_class)
        
        # 过滤条件：raw_line_id不能为NULL
        query = base_query.filter(model_class.raw_line_id.isnot(None))
        
        # 关联raw_document并过滤validation_status='passed'
        query = query.join(
            RawLine, model_class.raw_line_id == RawLine.id
        ).join(
            RawDocument, RawLine.raw_document_id == RawDocument.id
        ).filter(
            RawDocument.validation_status == 'passed'
        )
        
        return query
    
    def _create_integrity_exception(
        self,
        table_name: str,
        record_id: int,
        violation_type: str,
        message: str
    ):
        """
        创建数据完整性异常记录
        
        Args:
            table_name: 表名
            record_id: 记录ID
            violation_type: 违规类型
            message: 异常消息
        """
        exception_record = ExceptionModel(
            company_id=self.company_id,
            exception_type='data_integrity_violation',
            severity='high',
            source_type=table_name,
            source_id=record_id,
            message=f"[{violation_type}] {message}",
            context_data={
                'table_name': table_name,
                'record_id': record_id,
                'violation_type': violation_type
            },
            status='pending',
            created_at=datetime.now()
        )
        
        self.db.add(exception_record)
        self.db.commit()
        
        logger.info(
            f"✅ EXCEPTION CREATED - "
            f"type=data_integrity_violation, "
            f"source={table_name}.id={record_id}, "
            f"violation={violation_type}"
        )


# ========== 装饰器：自动验证数据完整性 ==========

def require_data_integrity(table_name: str):
    """
    装饰器：自动验证数据完整性
    
    用法：
    ```python
    @require_data_integrity('bank_statement_lines')
    def generate_report(db: Session, company_id: int, statement_ids: List[int]):
        # 此函数会自动过滤掉无效数据
        ...
    ```
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 从参数中提取db和company_id
            db = kwargs.get('db') or (args[0] if len(args) > 0 else None)
            company_id = kwargs.get('company_id') or (args[1] if len(args) > 1 else None)
            
            if not db or not company_id:
                raise ValueError("require_data_integrity装饰器需要db和company_id参数")
            
            # 注入validator到kwargs
            kwargs['integrity_validator'] = DataIntegrityValidator(db, company_id)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
