"""
Phase 1-4: 审计日志API路由
提供审计日志查询接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from ..db import get_db
from ..models import AuditLog
from ..schemas.audit_schemas import AuditLogResponse, AuditLogList, AuditLogFilter

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


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
