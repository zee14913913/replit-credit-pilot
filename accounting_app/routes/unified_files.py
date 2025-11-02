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
from ..models import AuditLog, User
from ..middleware.rbac_fixed import require_auth

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
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    module: Optional[str] = Query(None, description="模块过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    获取最近上传的文件
    前端首页只用这个接口
    
    🔒 强制认证：必须登录才能访问（current_user强制要求）
    🔒 租户隔离：自动使用当前用户的company_id，阻止跨租户访问
    
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
    # 🔒 强制使用当前用户的company_id，阻止跨租户访问
    company_id = current_user.company_id
    
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    获取文件详情（带降级策略）
    
    🔒 强制认证：必须登录才能访问
    🔒 租户隔离：只能查看自己公司的文件
    
    降级策略：
    1. 按新目录找
    2. 按旧目录找  
    3. 返回缺失提示
    """
    # 🔒 强制使用当前用户的company_id，阻止跨租户访问
    company_id = current_user.company_id
    
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    注册文件到统一索引
    Flask上传成功后要调用这个接口
    
    🔒 强制认证：必须登录才能注册文件
    🔒 租户隔离：只能注册到自己的公司，阻止跨租户注册
    """
    # 🔒 强制使用当前用户的company_id，覆盖请求中的company_id
    if current_user.role != 'admin' and file_data.company_id != current_user.company_id:
        logger.warning(f"⚠️ 租户隔离阻止：用户{current_user.username}(company_id={current_user.company_id})尝试注册文件到company_id={file_data.company_id}")
        raise HTTPException(status_code=403, detail="无权向其他公司注册文件")
    
    # 管理员可以为任何公司注册文件，普通用户强制使用自己的company_id
    final_company_id = file_data.company_id if current_user.role == 'admin' else current_user.company_id
    
    try:
        file_record = UnifiedFileService.register_file(
            db=db,
            company_id=final_company_id,  # 使用验证后的company_id
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    更新文件状态
    
    🔒 强制认证：必须登录才能更新状态
    🔒 租户隔离：只能更新自己公司的文件（管理员除外）
    """
    # 🔒 强制使用当前用户的company_id，阻止跨租户访问
    company_id = current_user.company_id
    
    # 🔒 管理员可以更新任何公司的文件，但需要先查询真实的company_id
    if current_user.role == 'admin':
        from ..models import FileIndex
        file_record = db.query(FileIndex).filter(FileIndex.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        company_id = file_record.company_id  # 管理员使用文件实际所属的company_id
    
    try:
        # ✅ 服务层会原子性验证file_id AND company_id，防止TOCTOU
        success = UnifiedFileService.update_file_status(
            db=db,
            file_id=file_id,
            company_id=company_id,  # 🔒 传递company_id进行原子性验证
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
