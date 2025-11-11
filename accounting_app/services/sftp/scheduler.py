"""
SFTP 后台调度器
使用 schedule 库实现定时文件同步和重试逻辑
"""
import schedule
import time
import logging
import threading
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from .sync_service import SFTPSyncService
from ...db import SessionLocal

logger = logging.getLogger(__name__)


class SFTPScheduler:
    """SFTP自动同步调度器：后台持续运行，定时扫描和上传文件"""
    
    def __init__(self, company_id: int = 1, sync_interval_minutes: int = 10):
        """
        初始化调度器
        
        Args:
            company_id: 公司ID
            sync_interval_minutes: 同步间隔（分钟），默认10分钟
        """
        self.company_id = company_id
        self.sync_interval_minutes = sync_interval_minutes
        self.is_running = False
        self._stop_event = threading.Event()
        self._thread = None
        
        logger.info(f"⏰ SFTP Scheduler initialized (sync every {sync_interval_minutes} minutes)")
    
    def start(self):
        """启动调度器（在独立线程中运行）"""
        if self.is_running:
            logger.warning("⚠️  Scheduler is already running")
            return
        
        self.is_running = True
        self._stop_event.clear()
        
        # 注册定时任务
        schedule.every(self.sync_interval_minutes).minutes.do(self._sync_task)
        
        # 注册重试任务（每5分钟检查一次）
        schedule.every(5).minutes.do(self._retry_task)
        
        # 启动后台线程
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        
        logger.info(f"✅ SFTP Scheduler started in background thread")
        
        # 立即执行一次同步
        self._sync_task()
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            logger.warning("⚠️  Scheduler is not running")
            return
        
        self.is_running = False
        self._stop_event.set()
        
        # 清除所有scheduled任务
        schedule.clear()
        
        # 等待线程结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        
        logger.info("🛑 SFTP Scheduler stopped")
    
    def _run_scheduler(self):
        """后台线程主循环"""
        logger.info("🔄 Scheduler loop started")
        
        while self.is_running and not self._stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(30)  # 每30秒检查一次
            except Exception as e:
                logger.error(f"❌ Scheduler loop error: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
        
        logger.info("🛑 Scheduler loop ended")
    
    def _sync_task(self):
        """同步任务：扫描并上传新文件"""
        try:
            logger.info(f"⏰ [Scheduled Sync] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 创建数据库会话
            db: Session = SessionLocal()
            
            try:
                # 执行同步
                sync_service = SFTPSyncService(db_session=db, company_id=self.company_id)
                result = sync_service.scan_and_upload_files(
                    is_manual=False,
                    uploaded_by="scheduler"
                )
                
                logger.info(f"✅ [Scheduled Sync] Completed: {result['uploaded']} uploaded, "
                           f"{result['failed']} failed, {result['skipped']} skipped")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ [Scheduled Sync] Error: {e}")
    
    def _retry_task(self):
        """重试任务：重新上传失败的文件"""
        try:
            logger.info(f"🔄 [Scheduled Retry] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 创建数据库会话
            db: Session = SessionLocal()
            
            try:
                # 执行重试
                sync_service = SFTPSyncService(db_session=db, company_id=self.company_id)
                result = sync_service.retry_failed_uploads()
                
                if result['retried'] > 0:
                    logger.info(f"✅ [Scheduled Retry] Completed: {result['succeeded']} succeeded, "
                               f"{result['failed']} failed")
                else:
                    logger.debug(f"ℹ️  [Scheduled Retry] No failed uploads to retry")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ [Scheduled Retry] Error: {e}")
    
    def get_status(self) -> dict:
        """
        获取调度器状态
        
        Returns:
            状态信息
        """
        return {
            "is_running": self.is_running,
            "sync_interval_minutes": self.sync_interval_minutes,
            "company_id": self.company_id,
            "pending_jobs": len(schedule.get_jobs()),
            "next_run": str(schedule.next_run()) if schedule.get_jobs() else None
        }


# 全局调度器实例
_global_scheduler: Optional[SFTPScheduler] = None


def get_scheduler(company_id: int = 1, sync_interval_minutes: int = 10) -> SFTPScheduler:
    """
    获取全局调度器实例（单例模式）
    
    Args:
        company_id: 公司ID
        sync_interval_minutes: 同步间隔（分钟）
    
    Returns:
        调度器实例
    """
    global _global_scheduler
    
    if _global_scheduler is None:
        _global_scheduler = SFTPScheduler(
            company_id=company_id,
            sync_interval_minutes=sync_interval_minutes
        )
    
    return _global_scheduler


def start_global_scheduler(company_id: int = 1, sync_interval_minutes: int = 10):
    """
    启动全局调度器（在FastAPI startup事件中调用）
    
    Args:
        company_id: 公司ID
        sync_interval_minutes: 同步间隔（分钟）
    """
    scheduler = get_scheduler(company_id, sync_interval_minutes)
    
    if not scheduler.is_running:
        scheduler.start()
        logger.info("✅ Global SFTP scheduler started")
    else:
        logger.warning("⚠️  Global SFTP scheduler already running")


def stop_global_scheduler():
    """停止全局调度器（在FastAPI shutdown事件中调用）"""
    global _global_scheduler
    
    if _global_scheduler and _global_scheduler.is_running:
        _global_scheduler.stop()
        logger.info("🛑 Global SFTP scheduler stopped")
