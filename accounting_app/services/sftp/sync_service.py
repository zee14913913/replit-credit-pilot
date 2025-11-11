"""
SFTP 同步服务协调器
负责扫描文件、管理上传任务、重试逻辑和审计日志
"""
import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .sftp_client import SFTPClient
from ...models import SFTPUploadJob
from ...utils.audit_logger import log_event

logger = logging.getLogger(__name__)


class SFTPSyncService:
    """SFTP同步服务：文件扫描、上传管理、重试策略"""
    
    # 允许上传的文件扩展名
    ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
    
    # 文件夹到payload_type的映射
    FOLDER_MAPPING = {
        "sales": "sales",
        "suppliers": "suppliers",
        "payments": "payments",
        "customers": "customers",
        "bank": "bank",
        "payroll": "payroll",
        "loan": "loan"
    }
    
    def __init__(self, db_session: Session, company_id: int = 1):
        """
        初始化同步服务
        
        Args:
            db_session: 数据库会话
            company_id: 公司ID（默认1）
        """
        self.db = db_session
        self.company_id = company_id
        self.sftp_client = SFTPClient()
        self.base_upload_dir = "accounting_data/uploads"
    
    def scan_and_upload_files(self, is_manual: bool = False, uploaded_by: str = "system") -> Dict[str, Any]:
        """
        扫描所有待上传文件并执行上传（支持多公司层级结构）
        
        目录结构：
        accounting_data/uploads/
            ├── company_1/
            │   ├── sales/
            │   ├── suppliers/
            │   └── payments/
            ├── company_2/
            │   ├── sales/
            │   └── bank/
        
        Args:
            is_manual: 是否手动触发
            uploaded_by: 触发用户
        
        Returns:
            上传结果统计
        """
        logger.info(f"📂 Scanning upload directories: {self.base_upload_dir}")
        
        uploaded_count = 0
        failed_count = 0
        skipped_count = 0
        results = []
        
        # 确保基础目录存在
        if not os.path.exists(self.base_upload_dir):
            logger.warning(f"⚠️  Base upload directory not found: {self.base_upload_dir}")
            return {
                "success": True,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
                "total_scanned": 0,
                "results": []
            }
        
        # 🔄 向后兼容：检测目录结构（legacy平面结构 vs 新的多公司层级）
        is_legacy_layout = any(
            folder_name in os.listdir(self.base_upload_dir)
            for folder_name in self.FOLDER_MAPPING.keys()
        )
        
        if is_legacy_layout:
            # Legacy 平面结构：accounting_data/uploads/sales/
            logger.info("📁 Detected legacy flat directory structure")
            company_folders = ["."]  # 当前目录作为单一公司
        else:
            # 新的多公司层级结构：accounting_data/uploads/company_1/sales/
            logger.info("📁 Detected multi-company directory structure")
            company_folders = [
                f for f in os.listdir(self.base_upload_dir)
                if os.path.isdir(os.path.join(self.base_upload_dir, f))
                and not f.startswith('.')  # 排除隐藏文件夹
            ]
        
        # 遍历所有公司目录
        for company_folder in company_folders:
            if company_folder == ".":
                company_path = self.base_upload_dir
                company_name = "default"
                logger.info(f"📁 Scanning legacy flat structure")
            else:
                company_path = os.path.join(self.base_upload_dir, company_folder)
                company_name = company_folder
                
                # 🔒 安全性：验证company_folder只包含安全字符
                if not self._is_safe_folder_name(company_folder):
                    logger.error(f"❌ Unsafe company folder name detected: {company_folder}")
                    continue
                
                # 🔒 安全性：确保这是真实目录，非符号链接
                if os.path.islink(company_path):
                    logger.error(f"❌ Symlink detected, skipping: {company_folder}")
                    continue
                
                logger.info(f"📁 Scanning company folder: {company_folder}")
            
            # 遍历每个数据类型文件夹
            for folder_name, payload_type in self.FOLDER_MAPPING.items():
                folder_path = os.path.join(company_path, folder_name)
                
                # 确保文件夹存在
                if not os.path.exists(folder_path):
                    continue
                
                # 获取文件夹中的文件（支持 CSV, XLSX, XLS）
                try:
                    files = [
                        f for f in os.listdir(folder_path)
                        if os.path.isfile(os.path.join(folder_path, f))
                        and os.path.splitext(f)[1].lower() in self.ALLOWED_EXTENSIONS
                        and not f.startswith('.')  # 排除隐藏文件
                    ]
                except PermissionError as e:
                    logger.error(f"❌ Permission denied: {folder_path} | {e}")
                    continue
                
                if files:
                    logger.info(f"📄 Found {len(files)} files in {company_folder}/{folder_name}/")
                
                # 上传每个文件
                for file_name in files:
                    local_path = os.path.join(folder_path, file_name)
                    
                    # 安全性检查：确保路径规范化（防止目录遍历攻击）
                    normalized_path = os.path.normpath(os.path.abspath(local_path))
                    base_abs = os.path.normpath(os.path.abspath(self.base_upload_dir))
                    if not normalized_path.startswith(base_abs):
                        logger.error(f"❌ Path traversal attempt detected: {local_path}")
                        continue
                    
                    # 检查文件是否已成功上传过（基于内容哈希）
                    if self._is_file_already_uploaded(local_path):
                        logger.debug(f"⏭️  File already uploaded successfully, skipping: {file_name}")
                        skipped_count += 1
                        continue
                    
                    # 执行上传
                    result = self._upload_single_file(
                        local_path=local_path,
                        file_name=file_name,
                        payload_type=payload_type,
                        is_manual=is_manual,
                        uploaded_by=uploaded_by,
                        company_folder=company_name
                    )
                    
                    results.append(result)
                    
                    if result['success']:
                        uploaded_count += 1
                    else:
                        failed_count += 1
        
        summary = {
            "success": True,
            "uploaded": uploaded_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "total_scanned": uploaded_count + failed_count + skipped_count,
            "results": results
        }
        
        logger.info(f"✅ Sync completed: {uploaded_count} uploaded, {failed_count} failed, {skipped_count} skipped")
        
        # 记录审计日志
        log_event(
            db=self.db,
            action_type="SFTP_SYNC",
            entity_type="sftp_upload_job",
            description=f"SFTP sync completed: {uploaded_count} uploaded, {failed_count} failed",
            metadata=summary
        )
        
        return summary
    
    def _upload_single_file(self, local_path: str, file_name: str, payload_type: str,
                           is_manual: bool, uploaded_by: str, company_folder: str = "unknown") -> Dict[str, Any]:
        """
        上传单个文件并记录到数据库
        
        Args:
            local_path: 本地文件路径
            file_name: 文件名
            payload_type: 数据类型
            is_manual: 是否手动触发
            uploaded_by: 触发用户
        
        Returns:
            上传结果
        """
        try:
            # 计算文件哈希
            file_hash = self._calculate_file_hash(local_path)
            file_size = os.path.getsize(local_path)
            
            # 获取远程路径（包含公司文件夹层级）
            remote_base = self.sftp_client.get_payload_remote_path(payload_type)
            remote_dir = os.path.join(remote_base, company_folder).replace('\\', '/')
            remote_path = os.path.join(remote_dir, file_name).replace('\\', '/')
            
            # 生成job编号
            job_number = self._generate_job_number()
            
            # 创建上传任务记录
            job = SFTPUploadJob(
                company_id=self.company_id,
                job_number=job_number,
                file_path=local_path,
                file_name=file_name,
                payload_type=payload_type,
                remote_path=remote_path,
                file_size=file_size,
                file_hash=file_hash,
                status='uploading',
                attempts=1,
                sftp_host=self.sftp_client.host,
                sftp_username=self.sftp_client.username,
                uploaded_by=uploaded_by,
                is_manual=is_manual,
                started_at=datetime.utcnow()
            )
            
            self.db.add(job)
            self.db.commit()
            
            logger.info(f"📤 Uploading {file_name} → {remote_path}")
            
            # 执行上传
            upload_result = self.sftp_client.upload_file(local_path, remote_path)
            
            # 更新任务状态
            if upload_result['success']:
                job.status = 'success'
                job.completed_at = datetime.utcnow()
                job.duration_seconds = upload_result.get('duration', 0)
                logger.info(f"✅ Upload successful: {file_name} ({job.job_number})")
            else:
                job.status = 'failed'
                job.last_error = upload_result.get('error', 'Unknown error')
                logger.error(f"❌ Upload failed: {file_name} | Error: {job.last_error}")
            
            self.db.commit()
            
            # 记录审计日志
            log_event(
                db=self.db,
                action_type="SFTP_UPLOAD",
                entity_type="sftp_upload_job",
                entity_id=job.id,
                description=f"File upload {'succeeded' if upload_result['success'] else 'failed'}: {file_name}",
                metadata={
                    "file_name": file_name,
                    "payload_type": payload_type,
                    "file_size": file_size,
                    "remote_path": remote_path,
                    "success": upload_result['success']
                }
            )
            
            return {
                "success": upload_result['success'],
                "job_number": job_number,
                "file_name": file_name,
                "payload_type": payload_type,
                "file_size": file_size,
                "message": upload_result.get('message', '')
            }
            
        except Exception as e:
            logger.error(f"❌ Exception uploading {file_name}: {e}")
            return {
                "success": False,
                "file_name": file_name,
                "payload_type": payload_type,
                "error": str(e)
            }
    
    def retry_failed_uploads(self) -> Dict[str, Any]:
        """
        重试所有失败的上传任务
        
        Returns:
            重试结果统计
        """
        # 查找需要重试的任务
        now = datetime.utcnow()
        failed_jobs = self.db.query(SFTPUploadJob).filter(
            SFTPUploadJob.company_id == self.company_id,
            SFTPUploadJob.status.in_(['failed', 'retry']),
            SFTPUploadJob.attempts < SFTPUploadJob.max_attempts,
            (SFTPUploadJob.next_retry_at == None) | (SFTPUploadJob.next_retry_at <= now)
        ).all()
        
        logger.info(f"🔄 Found {len(failed_jobs)} failed jobs to retry")
        
        retried_count = 0
        succeeded_count = 0
        failed_count = 0
        
        for job in failed_jobs:
            # 增加尝试次数
            job.attempts += 1
            job.status = 'uploading'
            job.started_at = datetime.utcnow()
            self.db.commit()
            
            # 重新上传
            upload_result = self.sftp_client.upload_file(job.file_path, job.remote_path)
            
            if upload_result['success']:
                job.status = 'success'
                job.completed_at = datetime.utcnow()
                job.duration_seconds = upload_result.get('duration', 0)
                job.last_error = None
                succeeded_count += 1
                logger.info(f"✅ Retry successful: {job.file_name} (attempt {job.attempts})")
            else:
                job.status = 'failed' if job.attempts >= job.max_attempts else 'retry'
                job.last_error = upload_result.get('error', 'Unknown error')
                # 指数退避：2分钟、4分钟、8分钟
                backoff_minutes = 2 ** job.attempts
                job.next_retry_at = datetime.utcnow() + timedelta(minutes=backoff_minutes)
                failed_count += 1
                logger.warning(f"⚠️  Retry failed: {job.file_name} (attempt {job.attempts}/{job.max_attempts})")
            
            self.db.commit()
            retried_count += 1
        
        summary = {
            "success": True,
            "retried": retried_count,
            "succeeded": succeeded_count,
            "failed": failed_count
        }
        
        logger.info(f"🔄 Retry completed: {succeeded_count} succeeded, {failed_count} failed")
        
        return summary
    
    def _is_file_already_uploaded(self, local_path: str) -> bool:
        """
        检查文件是否已成功上传
        
        Args:
            local_path: 本地文件路径
        
        Returns:
            是否已上传
        """
        file_hash = self._calculate_file_hash(local_path)
        
        existing_job = self.db.query(SFTPUploadJob).filter(
            SFTPUploadJob.company_id == self.company_id,
            SFTPUploadJob.file_hash == file_hash,
            SFTPUploadJob.status == 'success'
        ).first()
        
        return existing_job is not None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件SHA256哈希
        
        Args:
            file_path: 文件路径
        
        Returns:
            SHA256哈希值（hex格式）
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _generate_job_number(self) -> str:
        """
        生成唯一的job编号
        
        Returns:
            Job编号格式: SFTP-YYYYMMDD-HHMMSS-XXX
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        
        # 获取今天已有的job数量
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.db.query(SFTPUploadJob).filter(
            SFTPUploadJob.created_at >= today_start
        ).count()
        
        sequence = str(count + 1).zfill(3)
        
        return f"SFTP-{timestamp}-{sequence}"
    
    def _is_safe_folder_name(self, folder_name: str) -> bool:
        """
        验证文件夹名称只包含安全字符
        
        Args:
            folder_name: 文件夹名称
        
        Returns:
            是否安全
        """
        import re
        # 只允许字母、数字、下划线、连字符
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, folder_name))
    
    def get_upload_statistics(self) -> Dict[str, Any]:
        """
        获取上传统计信息
        
        Returns:
            统计数据
        """
        total = self.db.query(SFTPUploadJob).filter(
            SFTPUploadJob.company_id == self.company_id
        ).count()
        
        success = self.db.query(SFTPUploadJob).filter(
            SFTPUploadJob.company_id == self.company_id,
            SFTPUploadJob.status == 'success'
        ).count()
        
        failed = self.db.query(SFTPUploadJob).filter(
            SFTPUploadJob.company_id == self.company_id,
            SFTPUploadJob.status == 'failed'
        ).count()
        
        pending = self.db.query(SFTPUploadJob).filter(
            SFTPUploadJob.company_id == self.company_id,
            SFTPUploadJob.status.in_(['pending', 'retry', 'uploading'])
        ).count()
        
        return {
            "total_jobs": total,
            "successful": success,
            "failed": failed,
            "pending": pending,
            "success_rate": round(success / total * 100, 2) if total > 0 else 0
        }
