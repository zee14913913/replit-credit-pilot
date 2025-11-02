"""
Phase 1-4: 审计日志API路由
提供审计日志查询接口

Phase 2-3 Task 2: 添加Flask上传事件审计端点
接受来自Flask (5000)的上传事件，记录审计日志（不阻塞上传）
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from ..db import get_db
from ..models import AuditLog
from ..schemas.audit_schemas import AuditLogResponse, AuditLogList, AuditLogFilter
from ..utils.audit_logger import AuditLogger

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


# Phase 2-3 Task 2: Flask上传事件审计Schema
class FlaskUploadEvent(BaseModel):
    """Flask上传事件数据模型"""
    customer_id: Optional[int] = None
    customer_code: Optional[str] = None
    customer_name: Optional[str] = None
    company_id: Optional[int] = None
    upload_type: str  # 'credit_card_statement', 'savings_statement', 'receipt', etc.
    filename: str
    file_size: int
    file_path: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_user: Optional[str] = None  # 如果有session用户信息
    success: bool = True
    error_message: Optional[str] = None
    additional_info: Optional[dict] = None


@router.post("/upload-event", summary="记录Flask上传事件（Phase 2-3 Task 2）")
async def record_upload_event(
    event: FlaskUploadEvent = Body(...),
    db: Session = Depends(get_db)
):
    """
    接受来自Flask (5000端口)的文件上传事件，记录到审计日志
    
    **设计原则**：
    - ✅ 不需要认证（unauthenticated-but-identifiable）
    - ✅ 不阻塞Flask的上传流程（即使失败也返回200）
    - ✅ 记录完整的上传上下文信息（谁、何时、何地、什么）
    
    **审计追溯字段**：
    - customer_id/customer_code: 客户身份
    - upload_type: 上传类型
    - filename, file_size: 文件信息
    - ip_address, user_agent: 客户端信息
    - session_user: Flask session中的用户信息（如果有）
    
    **使用场景**：
    - Flask客户上传信用卡账单
    - Flask客户上传储蓄账户月结单
    - Flask客户上传收据图片
    
    **示例请求**：
    ```json
    {
        "customer_id": 1,
        "customer_code": "Be_rich_KP",
        "customer_name": "KENG CHOW",
        "upload_type": "credit_card_statement",
        "filename": "maybank_jan_2025.pdf",
        "file_size": 524288,
        "ip_address": "203.192.1.100",
        "user_agent": "Mozilla/5.0...",
        "success": true
    }
    ```
    """
    try:
        # 使用AuditLogger记录上传事件
        audit_logger = AuditLogger(db)
        
        # 构建审计日志描述
        description_parts = [
            f"Flask上传事件: {event.upload_type}",
            f"文件名: {event.filename}",
            f"大小: {event.file_size} bytes"
        ]
        
        if event.customer_name:
            description_parts.append(f"客户: {event.customer_name}")
        
        if event.error_message:
            description_parts.append(f"错误: {event.error_message}")
        
        description = " | ".join(description_parts)
        
        # 构建new_value字典（包含所有上传信息）
        new_value = {
            "upload_type": event.upload_type,
            "filename": event.filename,
            "file_size": event.file_size,
            "file_path": event.file_path,
            "customer_id": event.customer_id,
            "customer_code": event.customer_code,
            "customer_name": event.customer_name,
            "company_id": event.company_id,
            "session_user": event.session_user,
            "source": "flask_5000"
        }
        
        if event.additional_info:
            new_value.update(event.additional_info)
        
        # 记录审计日志
        # Phase 2-3 Task 2: 使用 'file_upload' action_type（符合CHECK约束）
        audit_log = audit_logger.log(
            action_type='file_upload',
            description=description,
            company_id=event.company_id,
            username=event.session_user or event.customer_code or 'anonymous',
            entity_type=event.upload_type,
            entity_id=event.customer_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            new_value=new_value,
            success=event.success,
            error_message=event.error_message
        )
        
        # 关闭独立Session
        audit_logger.close()
        
        return {
            "success": True,
            "message": "Upload event recorded",
            "audit_log_id": audit_log.id
        }
    
    except Exception as e:
        # Phase 2-3 Task 2关键设计：即使审计日志失败，也返回200
        # 不阻塞Flask的上传流程
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Failed to record upload event: {e}")
        
        return {
            "success": False,
            "message": f"Audit log failed but upload can proceed: {str(e)}",
            "audit_log_id": None
        }


@router.get("/", response_model=AuditLogList, summary="查询审计日志")
def list_audit_logs(
    company_id: Optional[int] = Query(None, description="公司ID过滤"),
    action_type: Optional[str] = Query(None, description="操作类型过滤"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    username: Optional[str] = Query(None, description="操作人过滤"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    success: Optional[bool] = Query(None, description="是否成功"),
    limit: int = Query(100, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    查询审计日志（支持多条件过滤和分页）
    
    常见查询场景：
    - 查看某公司的所有操作记录
    - 查看某人的操作历史
    - 查看所有删除操作
    - 查看失败的操作
    """
    query = db.query(AuditLog)
    
    # 应用过滤条件
    if company_id:
        query = query.filter(AuditLog.company_id == company_id)
    
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if username:
        query = query.filter(AuditLog.username.ilike(f'%{username}%'))
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    if success is not None:
        query = query.filter(AuditLog.success == success)
    
    # 按创建时间倒序排列
    query = query.order_by(desc(AuditLog.created_at))
    
    # 获取总数（在应用limit/offset之前）
    total = query.count()
    
    # 分页
    items = query.limit(limit).offset(offset).all()
    
    # 转换为响应模型
    response_items = [AuditLogResponse.from_orm(item) for item in items]
    
    return AuditLogList(total=total, items=response_items)


@router.get("/{audit_id}", response_model=AuditLogResponse, summary="获取审计日志详情")
def get_audit_log(
    audit_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单条审计日志的详细信息
    """
    audit_log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    
    if not audit_log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="审计日志不存在")
    
    return AuditLogResponse.from_orm(audit_log)


@router.get("/entity/{entity_type}/{entity_id}", response_model=AuditLogList, summary="查询实体的操作历史")
def get_entity_audit_history(
    entity_type: str,
    entity_id: int,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    """
    查询特定实体的所有操作历史
    
    例如：
    - GET /api/audit-logs/entity/bank_statement/123
      查看银行月结单ID=123的所有操作记录
    """
    items = db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(desc(AuditLog.created_at)).limit(limit).all()
    
    response_items = [AuditLogResponse.from_orm(item) for item in items]
    
    return AuditLogList(total=len(response_items), items=response_items)


@router.get("/user/{username}", response_model=AuditLogList, summary="查询用户的操作历史")
def get_user_audit_history(
    username: str,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    查询特定用户的所有操作历史
    """
    query = db.query(AuditLog).filter(
        AuditLog.username == username
    ).order_by(desc(AuditLog.created_at))
    
    total = query.count()
    items = query.limit(limit).offset(offset).all()
    
    response_items = [AuditLogResponse.from_orm(item) for item in items]
    
    return AuditLogList(total=total, items=response_items)


@router.get("/failed/list", response_model=AuditLogList, summary="查询失败的操作")
def get_failed_operations(
    company_id: Optional[int] = Query(None, description="公司ID过滤"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    查询所有失败的操作（success=False）
    用于故障排查和审计
    """
    query = db.query(AuditLog).filter(AuditLog.success == False)
    
    if company_id:
        query = query.filter(AuditLog.company_id == company_id)
    
    query = query.order_by(desc(AuditLog.created_at))
    
    total = query.count()
    items = query.limit(limit).offset(offset).all()
    
    response_items = [AuditLogResponse.from_orm(item) for item in items]
    
    return AuditLogList(total=total, items=response_items)
