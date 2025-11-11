"""
SFTP同步 API路由
提供手动触发同步、查看状态、管理上传任务等接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from ..db import get_db
from ..services.sftp.sftp_client import SFTPClient
from ..services.sftp.sync_service import SFTPSyncService
from ..services.sftp.scheduler import get_scheduler
from ..models import SFTPUploadJob
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sftp", tags=["SFTP Sync"])


class SyncResponse(BaseModel):
    """同步响应模型"""
    success: bool
    message: str
    uploaded: Optional[int] = 0
    failed: Optional[int] = 0
    skipped: Optional[int] = 0
    total_scanned: Optional[int] = 0


class SchedulerStatusResponse(BaseModel):
    """调度器状态响应模型"""
    is_running: bool
    sync_interval_minutes: int
    company_id: int
    pending_jobs: int
    next_run: Optional[str] = None


class UploadJobResponse(BaseModel):
    """上传任务响应模型"""
    id: int
    job_number: str
    file_name: str
    payload_type: str
    status: str
    attempts: int
    file_size: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    last_error: Optional[str] = None


# 依赖注入：获取当前company_id（简化版，实际应从JWT token获取）
def get_current_company_id() -> int:
    """获取当前公司ID（TODO: 从JWT token获取）"""
    return 1  # 默认公司ID


@router.get("/health", summary="SFTP服务健康检查")
def health_check() -> Dict[str, Any]:
    """
    检查SFTP服务健康状态
    
    Returns:
        服务状态信息
    """
    try:
        client = SFTPClient()
        test_result = client.test_connection()
        
        return {
            "service": "SFTP Sync",
            "status": "healthy" if test_result['success'] else "unhealthy",
            "sftp_connection": test_result['success'],
            "message": test_result.get('message', '')
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "service": "SFTP Sync",
            "status": "unhealthy",
            "sftp_connection": False,
            "error": str(e)
        }


@router.post("/sync-now", summary="立即触发手动同步", response_model=SyncResponse)
def manual_sync(
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
) -> SyncResponse:
    """
    手动触发立即同步所有待上传文件
    
    Returns:
        同步结果统计
    """
    try:
        logger.info(f"📤 Manual sync triggered for company_id={company_id}")
        
        sync_service = SFTPSyncService(db_session=db, company_id=company_id)
        result = sync_service.scan_and_upload_files(
            is_manual=True,
            uploaded_by="api_user"  # TODO: 从JWT获取真实用户
        )
        
        return SyncResponse(
            success=True,
            message=f"Manual sync completed: {result['uploaded']} uploaded, {result['failed']} failed",
            uploaded=result['uploaded'],
            failed=result['failed'],
            skipped=result['skipped'],
            total_scanned=result['total_scanned']
        )
        
    except Exception as e:
        logger.error(f"❌ Manual sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manual sync failed: {str(e)}"
        )


@router.post("/retry-failed", summary="重试失败的上传")
def retry_failed(
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
) -> Dict[str, Any]:
    """
    重试所有失败的上传任务
    
    Returns:
        重试结果统计
    """
    try:
        logger.info(f"🔄 Retry failed uploads triggered for company_id={company_id}")
        
        sync_service = SFTPSyncService(db_session=db, company_id=company_id)
        result = sync_service.retry_failed_uploads()
        
        return {
            "success": True,
            "message": f"Retry completed: {result['succeeded']} succeeded, {result['failed']} failed",
            **result
        }
        
    except Exception as e:
        logger.error(f"❌ Retry failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retry failed: {str(e)}"
        )


@router.get("/scheduler/status", summary="获取调度器状态", response_model=SchedulerStatusResponse)
def get_scheduler_status() -> SchedulerStatusResponse:
    """
    获取后台调度器运行状态
    
    Returns:
        调度器状态信息
    """
    try:
        scheduler = get_scheduler()
        status_info = scheduler.get_status()
        
        return SchedulerStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"❌ Get scheduler status failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get scheduler status failed: {str(e)}"
        )


@router.get("/jobs", summary="获取上传任务列表")
def get_upload_jobs(
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id),
    status_filter: Optional[str] = None,
    payload_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    获取上传任务列表（分页）
    
    Args:
        status_filter: 状态过滤（success, failed, pending等）
        payload_type: 数据类型过滤（sales, bank等）
        limit: 每页数量
        offset: 偏移量
    
    Returns:
        上传任务列表
    """
    try:
        query = db.query(SFTPUploadJob).filter(
            SFTPUploadJob.company_id == company_id
        )
        
        if status_filter:
            query = query.filter(SFTPUploadJob.status == status_filter)
        
        if payload_type:
            query = query.filter(SFTPUploadJob.payload_type == payload_type)
        
        total = query.count()
        
        jobs = query.order_by(SFTPUploadJob.created_at.desc()).limit(limit).offset(offset).all()
        
        job_list = [
            {
                "id": job.id,
                "job_number": job.job_number,
                "file_name": job.file_name,
                "payload_type": job.payload_type,
                "status": job.status,
                "attempts": job.attempts,
                "file_size": job.file_size,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "last_error": job.last_error
            }
            for job in jobs
        ]
        
        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": job_list
        }
        
    except Exception as e:
        logger.error(f"❌ Get upload jobs failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get upload jobs failed: {str(e)}"
        )


@router.get("/statistics", summary="获取上传统计")
def get_statistics(
    db: Session = Depends(get_db),
    company_id: int = Depends(get_current_company_id)
) -> Dict[str, Any]:
    """
    获取上传统计信息
    
    Returns:
        统计数据
    """
    try:
        sync_service = SFTPSyncService(db_session=db, company_id=company_id)
        stats = sync_service.get_upload_statistics()
        
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        logger.error(f"❌ Get statistics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get statistics failed: {str(e)}"
        )


@router.get("/test-connection", summary="测试SFTP连接")
def test_sftp_connection() -> Dict[str, Any]:
    """
    测试与客户ERP服务器的SFTP连接
    
    Returns:
        连接测试结果
    """
    try:
        client = SFTPClient()
        result = client.test_connection()
        
        return {
            "success": result['success'],
            "message": result.get('message', ''),
            "server_info": result.get('server_info', {})
        }
        
    except Exception as e:
        logger.error(f"❌ Test connection failed: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "error": str(e)
        }
