"""
异常中心 Exception Center API路由
集中管理所有异常：PDF解析失败、OCR错误、客户/供应商未匹配、记账失败
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from datetime import datetime

from ..db import get_db
from ..models import Exception as ExceptionModel
from ..schemas import (
    ExceptionCreate, ExceptionUpdate, ExceptionResponse, 
    ExceptionListResponse, ExceptionSummary
)
from ..middleware.multi_tenant import get_current_company_id

router = APIRouter(prefix="/exceptions", tags=["Exception Center"])
logger = logging.getLogger(__name__)


@router.get("/summary", response_model=ExceptionSummary)
def get_exception_summary(
    company_id: int = Depends(get_current_company_id),
    status_filter: Optional[str] = Query(None, description="状态过滤 (new/in_progress/resolved/ignored)"),
    db: Session = Depends(get_db)
):
    """
    获取异常摘要统计
    
    返回：
    - 异常总数
    - 按类型分组统计
    - 按严重程度分组统计
    - 按状态分组统计
    - 严重/高危异常数量
    """
    logger.info(f"获取异常摘要: company_id={company_id}, status_filter={status_filter}")
    
    # 基础查询
    query = db.query(ExceptionModel).filter(ExceptionModel.company_id == company_id)
    
    if status_filter:
        query = query.filter(ExceptionModel.status == status_filter)
    
    exceptions = query.all()
    
    # 统计
    total = len(exceptions)
    
    # 按类型统计
    by_type = {}
    for exc in exceptions:
        by_type[exc.exception_type] = by_type.get(exc.exception_type, 0) + 1
    
    # 按严重程度统计
    by_severity = {}
    for exc in exceptions:
        by_severity[exc.severity] = by_severity.get(exc.severity, 0) + 1
    
    # 按状态统计
    by_status = {}
    for exc in exceptions:
        by_status[exc.status] = by_status.get(exc.status, 0) + 1
    
    # 严重/高危统计
    critical_count = by_severity.get('critical', 0)
    high_count = by_severity.get('high', 0)
    
    return ExceptionSummary(
        total=total,
        by_type=by_type,
        by_severity=by_severity,
        by_status=by_status,
        critical_count=critical_count,
        high_count=high_count
    )


@router.get("/", response_model=ExceptionListResponse)
def list_exceptions(
    company_id: int = Depends(get_current_company_id),
    exception_type: Optional[str] = Query(None, description="异常类型过滤"),
    severity: Optional[str] = Query(None, description="严重程度过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取异常列表（分页）
    
    过滤条件：
    - exception_type: pdf_parse, ocr_error, customer_mismatch, supplier_mismatch, posting_error
    - severity: low, medium, high, critical
    - status: new, in_progress, resolved, ignored
    """
    logger.info(f"查询异常列表: company_id={company_id}, type={exception_type}, severity={severity}, status={status}")
    
    # 构建查询
    query = db.query(ExceptionModel).filter(ExceptionModel.company_id == company_id)
    
    if exception_type:
        query = query.filter(ExceptionModel.exception_type == exception_type)
    if severity:
        query = query.filter(ExceptionModel.severity == severity)
    if status:
        query = query.filter(ExceptionModel.status == status)
    
    # 总数
    total = query.count()
    
    # 分页（按创建时间倒序）
    exceptions = query.order_by(ExceptionModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return ExceptionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        exceptions=[ExceptionResponse.from_orm(exc) for exc in exceptions]
    )


@router.get("/{exception_id}", response_model=ExceptionResponse)
def get_exception(
    exception_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    获取单个异常详情
    
    ⚠️ 多租户隔离：必须同时验证exception_id和company_id
    """
    exception = db.query(ExceptionModel).filter(
        ExceptionModel.id == exception_id,
        ExceptionModel.company_id == company_id  # ✅ 租户隔离
    ).first()
    
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")
    
    return ExceptionResponse.from_orm(exception)


@router.post("/", response_model=ExceptionResponse)
def create_exception(
    exception: ExceptionCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    创建新异常记录
    
    ⚠️ 多租户隔离：company_id从get_current_company_id注入，不接受用户输入
    （通常由系统自动调用，不需要手动创建）
    """
    logger.warning(f"创建异常: company_id={company_id}, type={exception.exception_type}, severity={exception.severity}")
    
    # 使用注入的company_id，不信任用户输入
    exception_data = exception.dict()
    exception_data['company_id'] = company_id
    
    db_exception = ExceptionModel(**exception_data)
    db.add(db_exception)
    db.commit()
    db.refresh(db_exception)
    
    return ExceptionResponse.from_orm(db_exception)


@router.put("/{exception_id}/resolve", response_model=ExceptionResponse)
def resolve_exception(
    exception_id: int,
    update: ExceptionUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    标记异常为已解决
    
    ⚠️ 多租户隔离：必须同时验证exception_id和company_id
    """
    exception = db.query(ExceptionModel).filter(
        ExceptionModel.id == exception_id,
        ExceptionModel.company_id == company_id  # ✅ 租户隔离
    ).first()
    
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")
    
    # 更新状态
    exception.status = 'resolved'
    if update.resolved_by:
        exception.resolved_by = update.resolved_by
    exception.resolved_at = datetime.utcnow()
    if update.resolution_notes:
        exception.resolution_notes = update.resolution_notes
    
    db.commit()
    db.refresh(exception)
    
    logger.info(f"异常已解决: id={exception_id}, resolved_by={update.resolved_by}")
    
    return ExceptionResponse.from_orm(exception)


@router.put("/{exception_id}/ignore", response_model=ExceptionResponse)
def ignore_exception(
    exception_id: int,
    update: ExceptionUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    忽略异常
    
    ⚠️ 多租户隔离：必须同时验证exception_id和company_id
    """
    exception = db.query(ExceptionModel).filter(
        ExceptionModel.id == exception_id,
        ExceptionModel.company_id == company_id  # ✅ 租户隔离
    ).first()
    
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")
    
    # 更新状态
    exception.status = 'ignored'
    if update.resolved_by:
        exception.resolved_by = update.resolved_by
    if update.resolution_notes:
        exception.resolution_notes = update.resolution_notes
    
    db.commit()
    db.refresh(exception)
    
    logger.info(f"异常已忽略: id={exception_id}, ignored_by={update.resolved_by}")
    
    return ExceptionResponse.from_orm(exception)


@router.delete("/{exception_id}")
def delete_exception(
    exception_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    删除异常记录
    
    ⚠️ 多租户隔离：必须同时验证exception_id和company_id
    （谨慎使用，建议使用ignore而非删除）
    """
    exception = db.query(ExceptionModel).filter(
        ExceptionModel.id == exception_id,
        ExceptionModel.company_id == company_id  # ✅ 租户隔离
    ).first()
    
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")
    
    db.delete(exception)
    db.commit()
    
    logger.warning(f"异常已删除: id={exception_id}")
    
    return {"message": "Exception deleted successfully"}
