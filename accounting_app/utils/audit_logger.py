"""
Phase 1-4: 审计日志装饰器和工具函数
用于追踪所有敏感操作，确保合规性
"""
from functools import wraps
from typing import Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
from fastapi import Request
import json
from datetime import datetime

from ..models import AuditLog


class AuditLogger:
    """
    审计日志记录器
    负责记录所有敏感操作到audit_logs表
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        action_type: str,
        description: str,
        company_id: Optional[int] = None,
        username: Optional[str] = None,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        reason: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        记录审计日志
        
        Args:
            action_type: 操作类型（export, delete, rule_change, manual_entry, etc.）
            description: 操作描述
            company_id: 公司ID
            username: 操作人姓名或邮箱
            user_id: 用户ID
            entity_type: 实体类型（bank_statement, invoice, etc.）
            entity_id: 实体ID
            reason: 操作原因（手工改账必须填写）
            old_value: 修改前的值（字典）
            new_value: 修改后的值（字典）
            ip_address: IP地址
            user_agent: 浏览器UA
            request_method: HTTP方法
            request_path: API路径
            success: 操作是否成功
            error_message: 错误信息
        
        Returns:
            AuditLog对象
        """
        # Phase 1-4强制规则：手工改账/删除操作必须提供reason
        if action_type in ['manual_entry', 'delete', 'rule_change'] and not reason:
            raise ValueError(
                f"操作类型 '{action_type}' 必须提供reason（操作原因）。"
                "这是审计合规的强制要求。"
            )
        
        # 创建审计日志记录
        audit_log = AuditLog(
            company_id=company_id,
            user_id=user_id,
            username=username,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            old_value=old_value,
            new_value=new_value,
            success=success,
            error_message=error_message
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    def log_export(
        self,
        company_id: int,
        username: str,
        export_type: str,
        file_path: str,
        record_count: int,
        **kwargs
    ) -> AuditLog:
        """记录数据导出操作"""
        return self.log(
            action_type='export',
            description=f"导出{export_type}数据，共{record_count}条记录，文件：{file_path}",
            company_id=company_id,
            username=username,
            entity_type=export_type,
            new_value={'file_path': file_path, 'record_count': record_count},
            **kwargs
        )
    
    def log_delete(
        self,
        company_id: int,
        username: str,
        entity_type: str,
        entity_id: int,
        reason: str,
        old_data: Optional[Dict] = None,
        **kwargs
    ) -> AuditLog:
        """记录删除操作（强制要求reason）"""
        return self.log(
            action_type='delete',
            description=f"删除{entity_type} ID={entity_id}",
            company_id=company_id,
            username=username,
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason,  # 强制字段
            old_value=old_data,
            **kwargs
        )
    
    def log_manual_entry(
        self,
        company_id: int,
        username: str,
        journal_entry_id: int,
        reason: str,
        entry_data: Dict,
        **kwargs
    ) -> AuditLog:
        """记录手工分录操作（强制要求reason）"""
        return self.log(
            action_type='manual_entry',
            description=f"手工创建会计分录 ID={journal_entry_id}",
            company_id=company_id,
            username=username,
            entity_type='journal_entry',
            entity_id=journal_entry_id,
            reason=reason,  # 强制字段
            new_value=entry_data,
            **kwargs
        )
    
    def log_rule_change(
        self,
        company_id: int,
        username: str,
        rule_id: int,
        reason: str,
        old_rule: Optional[Dict] = None,
        new_rule: Optional[Dict] = None,
        **kwargs
    ) -> AuditLog:
        """记录规则变更操作（强制要求reason）"""
        return self.log(
            action_type='rule_change',
            description=f"修改自动过账规则 ID={rule_id}",
            company_id=company_id,
            username=username,
            entity_type='auto_posting_rule',
            entity_id=rule_id,
            reason=reason,  # 强制字段
            old_value=old_rule,
            new_value=new_rule,
            **kwargs
        )
    
    def log_file_upload(
        self,
        company_id: int,
        username: str,
        filename: str,
        file_type: str,
        file_size: int,
        **kwargs
    ) -> AuditLog:
        """记录文件上传操作"""
        return self.log(
            action_type='file_upload',
            description=f"上传文件：{filename} ({file_size} bytes)",
            company_id=company_id,
            username=username,
            entity_type=file_type,
            new_value={'filename': filename, 'file_size': file_size},
            **kwargs
        )
    
    def log_batch_import(
        self,
        company_id: int,
        username: str,
        import_type: str,
        success_count: int,
        failed_count: int,
        **kwargs
    ) -> AuditLog:
        """记录批量导入操作"""
        return self.log(
            action_type='batch_import',
            description=f"批量导入{import_type}：成功{success_count}条，失败{failed_count}条",
            company_id=company_id,
            username=username,
            entity_type=import_type,
            new_value={'success_count': success_count, 'failed_count': failed_count},
            **kwargs
        )


def log_audit(
    action_type: str,
    entity_type: Optional[str] = None,
    require_reason: bool = False
):
    """
    审计日志装饰器
    
    用法：
        @log_audit('delete', entity_type='bank_statement', require_reason=True)
        async def delete_bank_statement(statement_id: int, reason: str, db: Session):
            # 删除逻辑
            pass
    
    Args:
        action_type: 操作类型
        entity_type: 实体类型
        require_reason: 是否强制要求reason参数
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 提取db和request对象
            db: Optional[Session] = kwargs.get('db')
            request: Optional[Request] = kwargs.get('request')
            
            # 提取审计参数
            company_id = kwargs.get('company_id')
            username = kwargs.get('username', 'system')
            reason = kwargs.get('reason')
            entity_id = kwargs.get('entity_id') or kwargs.get('id')
            
            # Phase 1-4强制规则检查
            if require_reason and not reason:
                raise ValueError(
                    f"操作 '{func.__name__}' 需要强制提供reason参数。"
                    "这是审计合规的要求。"
                )
            
            # 初始化状态变量
            success = True
            error_msg = None
            result = None
            
            # 执行原函数
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                # 记录审计日志
                if db:
                    logger = AuditLogger(db)
                    
                    # 提取请求信息
                    ip_addr = None
                    user_agent = None
                    req_method = None
                    req_path = None
                    
                    if request:
                        ip_addr = request.client.host if request.client else None
                        user_agent = request.headers.get('user-agent')
                        req_method = request.method
                        req_path = str(request.url.path)
                    
                    logger.log(
                        action_type=action_type,
                        description=f"{func.__name__} 操作",
                        company_id=company_id,
                        username=username,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        reason=reason,
                        ip_address=ip_addr,
                        user_agent=user_agent,
                        request_method=req_method,
                        request_path=req_path,
                        success=success,
                        error_message=error_msg
                    )
            
            return result
        
        return wrapper
    return decorator


def extract_request_info(request: Request) -> Dict[str, Any]:
    """从FastAPI Request对象提取审计所需的信息"""
    return {
        'ip_address': request.client.host if request.client else None,
        'user_agent': request.headers.get('user-agent'),
        'request_method': request.method,
        'request_path': str(request.url.path)
    }
