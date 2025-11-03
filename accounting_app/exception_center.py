"""
异常中心 / Exception Center

功能：
1. 统一异常管理
2. 可行动化UI（根据next_action显示操作按钮）
3. 一键重试机制
4. 异常优先级排序

Phase 1-6: Exception Center - 集中化异常管理
"""

from typing import Optional, List, Dict
from datetime import datetime, date
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import Session

from .models import Exception as ExceptionModel, Company, RawDocument
from .db import get_db_session


class ExceptionCenter:
    """异常中心管理器"""
    
    SEVERITY_ORDER = {
        'critical': 1,
        'high': 2,
        'medium': 3,
        'low': 4
    }
    
    ACTION_CONFIGS = {
        'review_manually': {
            'icon': 'eye',
            'label': '人工审核',
            'label_en': 'Manual Review',
            'color': 'warning',
            'requires_reason': True
        },
        'upload_new_file': {
            'icon': 'upload',
            'label': '重新上传文件',
            'label_en': 'Upload New File',
            'color': 'primary',
            'requires_reason': False
        },
        'edit_record': {
            'icon': 'pencil',
            'label': '编辑记录',
            'label_en': 'Edit Record',
            'color': 'info',
            'requires_reason': True
        },
        'delete_record': {
            'icon': 'trash',
            'label': '删除记录',
            'label_en': 'Delete Record',
            'color': 'danger',
            'requires_reason': True
        },
        'retry': {
            'icon': 'arrow-repeat',
            'label': '重试',
            'label_en': 'Retry',
            'color': 'success',
            'requires_reason': False
        },
        'ignore': {
            'icon': 'x-circle',
            'label': '忽略',
            'label_en': 'Ignore',
            'color': 'secondary',
            'requires_reason': True
        }
    }
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or next(get_db_session())
        self._should_close = db is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close and self.db:
            self.db.close()
    
    def get_exceptions(
        self,
        company_id: Optional[int] = None,
        exception_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        retryable_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        获取异常列表（带智能排序）
        
        优先级排序：
        1. severity (critical > high > medium > low)
        2. 创建时间（新的优先）
        """
        conditions = []
        
        if company_id is not None:
            conditions.append(ExceptionModel.company_id == company_id)
        
        if exception_type:
            conditions.append(ExceptionModel.exception_type == exception_type)
        
        if severity:
            conditions.append(ExceptionModel.severity == severity)
        
        if status:
            conditions.append(ExceptionModel.status == status)
        
        if source_type:
            conditions.append(ExceptionModel.source_type == source_type)
        
        if retryable_only:
            conditions.append(ExceptionModel.retryable == True)
        
        from sqlalchemy import case
        
        severity_order_case = case(
            (ExceptionModel.severity == 'critical', 1),
            (ExceptionModel.severity == 'high', 2),
            (ExceptionModel.severity == 'medium', 3),
            (ExceptionModel.severity == 'low', 4),
            else_=5
        )
        
        stmt = select(ExceptionModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(
            severity_order_case,
            desc(ExceptionModel.created_at)
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = self.db.execute(stmt)
        exceptions = result.scalars().all()
        
        return [self._format_exception(exc) for exc in exceptions]
    
    def _format_exception(self, exc: ExceptionModel) -> Dict:
        """格式化异常数据（添加可行动化信息）"""
        action_config = self.ACTION_CONFIGS.get(exc.next_action, {
            'icon': 'question',
            'label': exc.next_action,
            'label_en': exc.next_action,
            'color': 'secondary',
            'requires_reason': False
        })
        
        return {
            'id': exc.id,
            'company_id': exc.company_id,
            'exception_type': exc.exception_type,
            'exception_type_display': self._get_exception_type_display(exc.exception_type),
            'severity': exc.severity,
            'severity_color': self._get_severity_color(exc.severity),
            'source_type': exc.source_type,
            'source_id': exc.source_id,
            'description': exc.description,
            'status': exc.status,
            'status_display': self._get_status_display(exc.status),
            'next_action': exc.next_action,
            'next_action_config': action_config,
            'retryable': exc.retryable,
            'retry_count': exc.retry_count,
            'last_retry_at': exc.last_retry_at.isoformat() if exc.last_retry_at else None,
            'resolved_at': exc.resolved_at.isoformat() if exc.resolved_at else None,
            'resolved_by': exc.resolved_by,
            'resolution_notes': exc.resolution_notes,
            'created_at': exc.created_at.isoformat(),
            'updated_at': exc.updated_at.isoformat()
        }
    
    def _get_exception_type_display(self, exception_type: str) -> Dict:
        """获取异常类型显示名称"""
        type_map = {
            'ingest_validation_failed': {'zh': '导入验证失败', 'en': 'Ingest Validation Failed'},
            'duplicate_record': {'zh': '重复记录', 'en': 'Duplicate Record'},
            'missing_source': {'zh': '缺少原始文档', 'en': 'Missing Source Document'},
            'balance_mismatch': {'zh': '余额不匹配', 'en': 'Balance Mismatch'},
            'rule_matching_failed': {'zh': '规则匹配失败', 'en': 'Rule Matching Failed'}
        }
        return type_map.get(exception_type, {'zh': exception_type, 'en': exception_type})
    
    def _get_severity_color(self, severity: str) -> str:
        """获取严重程度对应的颜色"""
        color_map = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary'
        }
        return color_map.get(severity, 'secondary')
    
    def _get_status_display(self, status: str) -> Dict:
        """获取状态显示名称"""
        status_map = {
            'new': {'zh': '新建', 'en': 'New'},
            'in_progress': {'zh': '处理中', 'en': 'In Progress'},
            'resolved': {'zh': '已解决', 'en': 'Resolved'},
            'ignored': {'zh': '已忽略', 'en': 'Ignored'}
        }
        return status_map.get(status, {'zh': status, 'en': status})
    
    def get_exception_stats(self, company_id: Optional[int] = None) -> Dict:
        """获取异常统计"""
        conditions = []
        if company_id is not None:
            conditions.append(ExceptionModel.company_id == company_id)
        
        base_query = select(ExceptionModel)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        total_stmt = select(func.count()).select_from(base_query.subquery())
        result = self.db.execute(total_stmt)
        total = result.scalar()
        
        new_stmt = base_query.where(ExceptionModel.status == 'new')
        result = self.db.execute(select(func.count()).select_from(new_stmt.subquery()))
        new_count = result.scalar()
        
        critical_stmt = base_query.where(ExceptionModel.severity == 'critical')
        result = self.db.execute(select(func.count()).select_from(critical_stmt.subquery()))
        critical_count = result.scalar()
        
        retryable_stmt = base_query.where(
            and_(
                ExceptionModel.retryable == True,
                ExceptionModel.status != 'resolved'
            )
        )
        result = self.db.execute(select(func.count()).select_from(retryable_stmt.subquery()))
        retryable_count = result.scalar()
        
        return {
            'total': total,
            'new': new_count,
            'critical': critical_count,
            'retryable': retryable_count
        }
    
    def resolve_exception(
        self,
        exception_id: int,
        resolved_by: str,
        resolution_notes: Optional[str] = None
    ) -> ExceptionModel:
        """解决异常"""
        stmt = select(ExceptionModel).where(ExceptionModel.id == exception_id)
        result = self.db.execute(stmt)
        exception = result.scalar_one_or_none()
        
        if not exception:
            raise ValueError(f"异常 {exception_id} 不存在 / Exception not found")
        
        exception.status = 'resolved'
        exception.resolved_at = datetime.now()
        exception.resolved_by = resolved_by
        exception.resolution_notes = resolution_notes
        
        self.db.commit()
        self.db.refresh(exception)
        
        return exception
    
    def ignore_exception(
        self,
        exception_id: int,
        resolved_by: str,
        reason: str
    ) -> ExceptionModel:
        """忽略异常（需要提供原因）"""
        if not reason:
            raise ValueError("忽略异常必须提供原因 / Reason required for ignoring exception")
        
        stmt = select(ExceptionModel).where(ExceptionModel.id == exception_id)
        result = self.db.execute(stmt)
        exception = result.scalar_one_or_none()
        
        if not exception:
            raise ValueError(f"异常 {exception_id} 不存在 / Exception not found")
        
        exception.status = 'ignored'
        exception.resolved_at = datetime.now()
        exception.resolved_by = resolved_by
        exception.resolution_notes = f"忽略原因: {reason}"
        
        self.db.commit()
        self.db.refresh(exception)
        
        return exception
    
    def retry_exception(
        self,
        exception_id: int,
        retry_by: str
    ) -> Dict:
        """
        重试异常（仅适用于retryable=True的异常）
        
        Returns:
            {
                'success': bool,
                'message': str,
                'exception': ExceptionModel (如果重试失败)
            }
        """
        stmt = select(ExceptionModel).where(ExceptionModel.id == exception_id)
        result = self.db.execute(stmt)
        exception = result.scalar_one_or_none()
        
        if not exception:
            raise ValueError(f"异常 {exception_id} 不存在 / Exception not found")
        
        if not exception.retryable:
            raise ValueError("此异常不支持重试 / Exception is not retryable")
        
        exception.retry_count += 1
        exception.last_retry_at = datetime.now()
        exception.status = 'in_progress'
        
        try:
            if exception.exception_type == 'rule_matching_failed':
                from .posting_engine import PostingRuleEngine
                
                with PostingRuleEngine(self.db) as engine:
                    if exception.source_type == 'bank_statement':
                        from .models import BankStatement
                        stmt = select(BankStatement).where(BankStatement.id == exception.source_id)
                        result = self.db.execute(stmt)
                        record = result.scalar_one_or_none()
                        
                        if record:
                            keywords = [record.description] if record.description else []
                            amount = record.debit_amount or record.credit_amount
                            transaction_type = 'deposit' if record.debit_amount else 'withdrawal'
                            
                            rule = engine.find_matching_rule(
                                exception.company_id,
                                exception.source_type,
                                transaction_type,
                                keywords,
                                amount
                            )
                            
                            if rule:
                                engine.apply_rule_to_bank_statement(record, rule, retry_by)
                                exception.status = 'resolved'
                                exception.resolved_at = datetime.now()
                                exception.resolved_by = retry_by
                                exception.resolution_notes = '重试成功，规则匹配并自动过账'
                                self.db.commit()
                                
                                return {
                                    'success': True,
                                    'message': '重试成功 / Retry successful'
                                }
            
            self.db.commit()
            return {
                'success': False,
                'message': '重试失败，仍未找到解决方案 / Retry failed, solution not found',
                'exception': exception
            }
        
        except Exception as e:
            exception.status = 'new'
            exception.resolution_notes = f"重试失败: {str(e)}"
            self.db.commit()
            
            return {
                'success': False,
                'message': f'重试失败: {str(e)} / Retry failed: {str(e)}',
                'exception': exception
            }
    
    def bulk_resolve(
        self,
        exception_ids: List[int],
        resolved_by: str,
        resolution_notes: Optional[str] = None
    ) -> Dict:
        """批量解决异常"""
        resolved = 0
        failed = []
        
        for exc_id in exception_ids:
            try:
                self.resolve_exception(exc_id, resolved_by, resolution_notes)
                resolved += 1
            except Exception as e:
                failed.append({
                    'id': exc_id,
                    'error': str(e)
                })
        
        return {
            'resolved': resolved,
            'failed': len(failed),
            'errors': failed
        }
    
    def create_exception(
        self,
        company_id: int,
        exception_type: str,
        severity: str,
        source_type: str,
        description: str,
        source_id: Optional[int] = None,
        next_action: str = 'review_manually',
        retryable: bool = False
    ) -> ExceptionModel:
        """创建新异常"""
        exception = ExceptionModel(
            company_id=company_id,
            exception_type=exception_type,
            severity=severity,
            source_type=source_type,
            source_id=source_id,
            description=description,
            status='new',
            next_action=next_action,
            retryable=retryable,
            retry_count=0
        )
        
        self.db.add(exception)
        self.db.commit()
        self.db.refresh(exception)
        
        return exception
