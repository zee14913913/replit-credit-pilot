"""
异常管理服务 ExceptionManager
用于在系统各处统一记录和管理异常
"""
import logging
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import Exception as ExceptionModel

logger = logging.getLogger(__name__)


class ExceptionManager:
    """
    异常管理器 - 统一异常记录接口
    
    支持5类异常：
    1. pdf_parse - PDF解析失败
    2. ocr_error - OCR识别错误
    3. customer_mismatch - 客户未匹配
    4. supplier_mismatch - 供应商未匹配
    5. posting_error - 记账失败
    """
    
    @staticmethod
    def record_exception(
        db: Session,
        company_id: int,
        exception_type: str,
        severity: str,
        error_message: str,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> ExceptionModel:
        """
        记录异常到数据库
        
        Args:
            db: 数据库会话
            company_id: 公司ID
            exception_type: 异常类型 (pdf_parse, ocr_error, customer_mismatch, supplier_mismatch, posting_error)
            severity: 严重程度 (low, medium, high, critical)
            error_message: 错误信息
            source_type: 来源类型 (bank_statement, pos_report, sales_invoice, purchase_invoice, journal_entry)
            source_id: 来源记录ID
            raw_data: 原始数据（字典）
        
        Returns:
            ExceptionModel: 创建的异常记录
        """
        # 验证异常类型
        valid_types = ['pdf_parse', 'ocr_error', 'customer_mismatch', 'supplier_mismatch', 'posting_error']
        if exception_type not in valid_types:
            raise ValueError(f"Invalid exception_type: {exception_type}. Must be one of {valid_types}")
        
        # 验证严重程度
        valid_severities = ['low', 'medium', 'high', 'critical']
        if severity not in valid_severities:
            raise ValueError(f"Invalid severity: {severity}. Must be one of {valid_severities}")
        
        # 转换raw_data为JSON字符串
        raw_data_str = None
        if raw_data:
            try:
                raw_data_str = json.dumps(raw_data, ensure_ascii=False, default=str)
            except Exception as e:
                logger.warning(f"无法序列化raw_data: {e}")
                raw_data_str = str(raw_data)
        
        # 创建异常记录
        exception = ExceptionModel(
            company_id=company_id,
            exception_type=exception_type,
            severity=severity,
            source_type=source_type,
            source_id=source_id,
            error_message=error_message,
            raw_data=raw_data_str,
            status='new'
        )
        
        db.add(exception)
        db.commit()
        db.refresh(exception)
        
        # 记录日志
        logger.warning(
            f"⚠️ 异常已记录: [ID={exception.id}] "
            f"Type={exception_type}, Severity={severity}, "
            f"Company={company_id}, Source={source_type}:{source_id}, "
            f"Message={error_message[:100]}"
        )
        
        return exception
    
    @staticmethod
    def record_pdf_parse_error(
        db: Session,
        company_id: int,
        error_message: str,
        file_path: Optional[str] = None,
        severity: str = 'high'
    ) -> ExceptionModel:
        """
        记录PDF解析失败异常（快捷方法）
        """
        raw_data = {}
        if file_path:
            raw_data['file_path'] = file_path
        
        return ExceptionManager.record_exception(
            db=db,
            company_id=company_id,
            exception_type='pdf_parse',
            severity=severity,
            error_message=error_message,
            source_type='bank_statement',
            raw_data=raw_data
        )
    
    @staticmethod
    def record_ocr_error(
        db: Session,
        company_id: int,
        error_message: str,
        image_path: Optional[str] = None,
        severity: str = 'medium'
    ) -> ExceptionModel:
        """
        记录OCR识别错误（快捷方法）
        """
        raw_data = {}
        if image_path:
            raw_data['image_path'] = image_path
        
        return ExceptionManager.record_exception(
            db=db,
            company_id=company_id,
            exception_type='ocr_error',
            severity=severity,
            error_message=error_message,
            raw_data=raw_data
        )
    
    @staticmethod
    def record_customer_mismatch(
        db: Session,
        company_id: int,
        customer_name: str,
        source_type: str,
        source_id: int,
        severity: str = 'medium'
    ) -> ExceptionModel:
        """
        记录客户未匹配异常（快捷方法）
        """
        error_message = f"客户未找到: {customer_name}"
        
        raw_data = {
            'customer_name': customer_name,
            'suggestions': []  # 可以添加相似客户建议
        }
        
        return ExceptionManager.record_exception(
            db=db,
            company_id=company_id,
            exception_type='customer_mismatch',
            severity=severity,
            error_message=error_message,
            source_type=source_type,
            source_id=source_id,
            raw_data=raw_data
        )
    
    @staticmethod
    def record_supplier_mismatch(
        db: Session,
        company_id: int,
        supplier_name: str,
        source_type: str,
        source_id: int,
        severity: str = 'medium'
    ) -> ExceptionModel:
        """
        记录供应商未匹配异常（快捷方法）
        """
        error_message = f"供应商未找到: {supplier_name}"
        
        raw_data = {
            'supplier_name': supplier_name,
            'suggestions': []  # 可以添加相似供应商建议
        }
        
        return ExceptionManager.record_exception(
            db=db,
            company_id=company_id,
            exception_type='supplier_mismatch',
            severity=severity,
            error_message=error_message,
            source_type=source_type,
            source_id=source_id,
            raw_data=raw_data
        )
    
    @staticmethod
    def record_posting_error(
        db: Session,
        company_id: int,
        error_message: str,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        context: Optional[Dict] = None,
        severity: str = 'critical'
    ) -> ExceptionModel:
        """
        记录记账失败异常（快捷方法）
        
        Args:
            db: 数据库会话
            company_id: 公司ID
            error_message: 错误信息
            source_type: 来源类型 (bank_import, sales_invoice, purchase_invoice等)
            source_id: 来源记录ID
            context: 上下文数据（字典）
            severity: 严重程度
        """
        raw_data = {}
        if context:
            raw_data.update(context)
        
        return ExceptionManager.record_exception(
            db=db,
            company_id=company_id,
            exception_type='posting_error',
            severity=severity,
            error_message=error_message,
            source_type=source_type or 'journal_entry',
            source_id=source_id,
            raw_data=raw_data
        )
    
    @staticmethod
    def record_validation_error(
        db: Session,
        company_id: int,
        source_type: str,
        source_id: int,
        message: str,
        context: Optional[Dict] = None,
        severity: str = 'high'
    ) -> ExceptionModel:
        """
        记录数据验证失败异常（快捷方法）
        
        用于记录CSV/PDF等文件数据验证失败
        内部使用'pdf_parse'类型（因为验证失败本质上是解析失败）
        
        Args:
            db: 数据库会话
            company_id: 公司ID
            source_type: 来源类型 (bank_import, invoice_import等)
            source_id: raw_document的ID
            message: 错误信息
            context: 上下文数据（包含详细错误列表）
            severity: 严重程度
        """
        raw_data = {}
        if context:
            raw_data.update(context)
        
        return ExceptionManager.record_exception(
            db=db,
            company_id=company_id,
            exception_type='pdf_parse',  # 使用pdf_parse类型表示文件解析/验证失败
            severity=severity,
            error_message=message,
            source_type=source_type,
            source_id=source_id,
            raw_data=raw_data
        )
    
    @staticmethod
    def get_exception_summary(
        db: Session,
        company_id: int,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取异常摘要（用于Management Report）
        
        Returns:
            {
                'total': 15,
                'critical': 2,
                'high': 5,
                'by_type': {...},
                'by_status': {...}
            }
        """
        query = db.query(ExceptionModel).filter(ExceptionModel.company_id == company_id)
        
        if status_filter:
            query = query.filter(ExceptionModel.status == status_filter)
        
        exceptions = query.all()
        
        # 统计
        total = len(exceptions)
        critical_count = sum(1 for e in exceptions if e.severity == 'critical')
        high_count = sum(1 for e in exceptions if e.severity == 'high')
        
        # 按类型统计
        by_type = {}
        for exc in exceptions:
            by_type[exc.exception_type] = by_type.get(exc.exception_type, 0) + 1
        
        # 按状态统计
        by_status = {}
        for exc in exceptions:
            by_status[exc.status] = by_status.get(exc.status, 0) + 1
        
        return {
            'total': total,
            'critical': critical_count,
            'high': high_count,
            'by_type': by_type,
            'by_status': by_status
        }
