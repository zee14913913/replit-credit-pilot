
"""
Phase 1-11: 文件上传确认系统 - API路由
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import logging

from ..db import get_db
from ..services.pending_file_service import PendingFileService
from ..services.upload_handler import UploadHandler
from ..schemas.pending_file_schemas import (
    PendingFileCreate,
    PendingFileConfirm,
    PendingFileReject,
    PendingFileResponse,
    PendingFileListResponse,
    CustomerMatchInfo
)
from ..utils.file_hash import calculate_file_hash_chunked

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/files/pending", tags=["Pending Files"])


@router.post("/upload", response_model=PendingFileResponse)
async def upload_file_to_pending(
    file: UploadFile = File(...),
    company_id: int = Form(...),
    username: str = Form(default="system"),
    db: Session = Depends(get_db)
):
    """
    上传文件到待确认队列
    
    流程：
    1. 保存文件到临时位置
    2. OCR提取信息（姓名、IC、银行、期间）
    3. 自动匹配客户
    4. 创建pending_file记录
    """
    try:
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 生成临时文件路径
        temp_dir = os.path.join("accounting_data", "pending_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_safe = file.filename.replace(" ", "_").replace("/", "_")
        temp_path = os.path.join(temp_dir, f"{timestamp}_{filename_safe}")
        
        # 保存文件
        with open(temp_path, 'wb') as f:
            f.write(file_content)
        
        # 计算文件哈希
        file_hash = calculate_file_hash_chunked(file_path=temp_path)
        
        # TODO: 调用OCR服务提取信息
        # 这里暂时使用模拟数据
        extracted_info = {
            'customer_name': None,
            'ic_number': None,
            'bank': None,
            'period': None,
            'card_last4': None,
            'account_number': None
        }
        
        # 创建待确认文件记录
        service = PendingFileService(db)
        pending_file = service.create_pending_file(
            original_filename=file.filename,
            file_path=temp_path,
            file_size=file_size,
            file_hash=file_hash,
            extracted_info=extracted_info
        )
        
        return pending_file
    
    except Exception as e:
        logger.error(f"Upload to pending failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PendingFileListResponse)
def get_pending_files(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取待确认文件列表
    
    Args:
        status: 过滤状态（pending/matched/mismatch/confirmed/rejected）
        limit: 限制数量
        offset: 偏移量
    """
    service = PendingFileService(db)
    
    # 获取文件列表
    items, total = service.get_pending_files(status=status, limit=limit, offset=offset)
    
    # 获取统计信息
    stats = service.get_statistics()
    
    return PendingFileListResponse(
        total=total,
        pending_count=stats['pending'],
        matched_count=stats['matched'],
        mismatch_count=stats['mismatch'],
        confirmed_count=stats['confirmed'],
        rejected_count=stats['rejected'],
        items=items
    )


@router.get("/{file_id}", response_model=PendingFileResponse)
def get_pending_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """获取单个待确认文件详情"""
    service = PendingFileService(db)
    pending_file = service.get_pending_file(file_id)
    
    if not pending_file:
        raise HTTPException(status_code=404, detail="Pending file not found")
    
    return pending_file


@router.post("/{file_id}/confirm", response_model=PendingFileResponse)
def confirm_pending_file(
    file_id: int,
    request: PendingFileConfirm,
    db: Session = Depends(get_db)
):
    """
    确认文件可以处理
    
    确认后文件将进入正常处理流程
    """
    try:
        service = PendingFileService(db)
        pending_file = service.confirm_file(
            file_id=file_id,
            confirmed_by=request.confirmed_by,
            matched_customer_id=request.matched_customer_id,
            matched_company_id=request.matched_company_id,
            notes=request.notes
        )
        
        return pending_file
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Confirm pending file failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{file_id}/reject", response_model=PendingFileResponse)
def reject_pending_file(
    file_id: int,
    request: PendingFileReject,
    db: Session = Depends(get_db)
):
    """
    拒绝文件
    
    拒绝后文件不会被处理
    """
    try:
        service = PendingFileService(db)
        pending_file = service.reject_file(
            file_id=file_id,
            rejected_reason=request.rejected_reason,
            rejected_by=request.rejected_by
        )
        
        return pending_file
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Reject pending file failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}/search-customers", response_model=List[CustomerMatchInfo])
def search_matching_customers(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    搜索可能匹配的客户
    
    基于OCR提取的信息，返回最可能的客户列表
    """
    service = PendingFileService(db)
    pending_file = service.get_pending_file(file_id)
    
    if not pending_file:
        raise HTTPException(status_code=404, detail="Pending file not found")
    
    # 构建提取信息
    extracted_info = {
        'customer_name': pending_file.extracted_customer_name,
        'ic_number': pending_file.extracted_ic_number,
        'bank': pending_file.extracted_bank,
        'period': pending_file.extracted_period,
        'card_last4': pending_file.extracted_card_last4,
        'account_number': pending_file.extracted_account_number
    }
    
    # 搜索匹配客户
    candidates = service.search_customers(extracted_info, limit=5)
    
    return candidates


@router.get("/statistics/summary")
def get_pending_statistics(db: Session = Depends(get_db)):
    """获取待确认文件统计信息"""
    service = PendingFileService(db)
    stats = service.get_statistics()
    
    return {
        "success": True,
        "statistics": stats
    }
