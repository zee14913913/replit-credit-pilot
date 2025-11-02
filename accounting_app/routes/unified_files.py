"""
统一文件管理API - 支持Flask和FastAPI双引擎
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from ..db import get_db
from ..services.unified_file_service import UnifiedFileService
from ..models import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["unified-files"])


class FileRegistration(BaseModel):
    """文件注册请求"""
    company_id: int
    filename: str
    file_path: str
    module: str
    from_engine: str = 'flask'
    uploaded_by: Optional[str] = None
    file_size_kb: Optional[int] = None
    validation_status: str = 'pending'
    status: str = 'processing'


@router.get("/recent")
def get_recent_files(
    company_id: int = Query(..., description="公司ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    module: Optional[str] = Query(None, description="模块过滤"),
    db: Session = Depends(get_db)
):
    """
    获取最近上传的文件
    前端首页只用这个接口
    
    返回格式：
    [
      {
        "file_id": "...",
        "file_name": "...",
        "module": "bank|credit-card|pos|supplier|reports|management",
        "storage_path": "...",
        "status": "active|processing|failed|archived",
        "uploaded_at": "...",
        "uploaded_by": "...",
        "from_engine": "flask|fastapi",
        "validation_status": "passed|failed|pending",
        "is_new": true  // 10分钟内的新文件
      }
    ]
    """
    try:
        files = UnifiedFileService.get_recent_files(
            db=db,
            company_id=company_id,
            limit=limit,
            module=module
        )
        
        return {
            "success": True,
            "company_id": company_id,
            "total": len(files),
            "files": files
        }
    
    except Exception as e:
        logger.error(f"Error getting recent files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{file_id}")
def get_file_detail(
    file_id: int,
    company_id: int = Query(..., description="公司ID"),
    db: Session = Depends(get_db)
):
    """
    获取文件详情（带降级策略）
    
    降级策略：
    1. 按新目录找
    2. 按旧目录找  
    3. 返回缺失提示
    """
    try:
        result = UnifiedFileService.get_file_with_fallback(
            db=db,
            file_id=file_id,
            company_id=company_id
        )
        
        # 如果文件缺失，记录审计日志
        if result["status"] == "missing":
            try:
                audit_log = AuditLog(
                    action_type="file_upload",  # ✅ 修复：使用正确的字段名
                    entity_type="file",
                    entity_id=file_id,
                    company_id=company_id,
                    description=f"User attempted to access missing file: {result.get('file_name')}",  # ✅ 添加必填字段
                    old_value={
                        "file_id": file_id,
                        "file_name": result.get("file_name"),
                        "module": result.get("module")
                    }
                )
                db.add(audit_log)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to log missing file access: {str(e)}")
                pass  # 审计日志失败不影响主流程
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting file detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
def register_file(
    file_data: FileRegistration,
    db: Session = Depends(get_db)
):
    """
    注册文件到统一索引
    Flask上传成功后要调用这个接口
    """
    try:
        file_record = UnifiedFileService.register_file(
            db=db,
            company_id=file_data.company_id,
            filename=file_data.filename,
            file_path=file_data.file_path,
            module=file_data.module,
            from_engine=file_data.from_engine,
            uploaded_by=file_data.uploaded_by,
            file_size_kb=file_data.file_size_kb,
            validation_status=file_data.validation_status,
            status=file_data.status
        )
        
        return {
            "success": True,
            "file_id": file_record.id,
            "message": "文件已注册到统一索引"
        }
    
    except Exception as e:
        logger.error(f"Error registering file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/status/{file_id}")
def update_file_status(
    file_id: int,
    status: Optional[str] = Query(None),
    validation_status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """更新文件状态"""
    try:
        success = UnifiedFileService.update_file_status(
            db=db,
            file_id=file_id,
            status=status,
            validation_status=validation_status
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "success": True,
            "message": "状态更新成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
