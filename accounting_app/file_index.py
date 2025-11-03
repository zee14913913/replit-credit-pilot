"""
文件统一索引系统 / Unified File Index System

功能：
1. 所有上传文件统一登记
2. 文件状态追踪（上传→处理→完成/失败）
3. 文件关联管理（RawDocument关联）

Phase 1-7: Unified File Storage Manager
"""

from typing import Optional, List, Dict
from datetime import datetime, date
import os
from pathlib import Path
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import Session

from .models import UploadStaging, RawDocument, Company
from .db import get_db_session


class FileIndexManager:
    """文件索引管理器"""
    
    STATUS_DISPLAY = {
        'uploaded': {'zh': '已上传', 'en': 'Uploaded', 'color': 'info'},
        'processing': {'zh': '处理中', 'en': 'Processing', 'color': 'warning'},
        'completed': {'zh': '处理完成', 'en': 'Completed', 'color': 'success'},
        'failed': {'zh': '处理失败', 'en': 'Failed', 'color': 'danger'},
        'archived': {'zh': '已归档', 'en': 'Archived', 'color': 'secondary'}
    }
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or next(get_db_session())
        self._should_close = db is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close and self.db:
            self.db.close()
    
    def register_upload(
        self,
        company_id: int,
        file_type: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        uploaded_by: str,
        metadata: Optional[Dict] = None
    ) -> UploadStaging:
        """
        注册上传文件
        
        Args:
            company_id: 公司ID
            file_type: 文件类型 (bank_statement, invoice, receipt, etc.)
            original_filename: 原始文件名
            file_path: 存储路径
            file_size: 文件大小（字节）
            uploaded_by: 上传人
            metadata: 额外元数据（JSON格式）
        
        Returns:
            UploadStaging对象
        """
        import json
        
        upload = UploadStaging(
            company_id=company_id,
            file_type=file_type,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            status='uploaded',
            uploaded_by=uploaded_by,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)
        
        return upload
    
    def update_status(
        self,
        upload_id: int,
        status: str,
        error_message: Optional[str] = None,
        raw_document_id: Optional[int] = None
    ) -> UploadStaging:
        """更新文件处理状态"""
        stmt = select(UploadStaging).where(UploadStaging.id == upload_id)
        result = self.db.execute(stmt)
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise ValueError(f"上传记录 {upload_id} 不存在 / Upload record not found")
        
        upload.status = status
        upload.processed_at = datetime.now()
        
        if error_message:
            upload.error_message = error_message
        
        if raw_document_id:
            upload.raw_document_id = raw_document_id
        
        self.db.commit()
        self.db.refresh(upload)
        
        return upload
    
    def get_uploads(
        self,
        company_id: Optional[int] = None,
        file_type: Optional[str] = None,
        status: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """获取上传文件列表"""
        conditions = []
        
        if company_id is not None:
            conditions.append(UploadStaging.company_id == company_id)
        
        if file_type:
            conditions.append(UploadStaging.file_type == file_type)
        
        if status:
            conditions.append(UploadStaging.status == status)
        
        if uploaded_by:
            conditions.append(UploadStaging.uploaded_by == uploaded_by)
        
        if date_from:
            conditions.append(UploadStaging.uploaded_at >= date_from)
        
        if date_to:
            from datetime import datetime, time
            date_to_end = datetime.combine(date_to, time.max)
            conditions.append(UploadStaging.uploaded_at <= date_to_end)
        
        stmt = select(UploadStaging)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(desc(UploadStaging.uploaded_at))
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = self.db.execute(stmt)
        uploads = result.scalars().all()
        
        return [self._format_upload(upload) for upload in uploads]
    
    def _format_upload(self, upload: UploadStaging) -> Dict:
        """格式化上传记录"""
        import json
        
        status_info = self.STATUS_DISPLAY.get(upload.status, {
            'zh': upload.status,
            'en': upload.status,
            'color': 'secondary'
        })
        
        file_exists = os.path.exists(upload.file_path) if upload.file_path else False
        
        metadata = {}
        if upload.metadata:
            try:
                metadata = json.loads(upload.metadata)
            except:
                metadata = {}
        
        return {
            'id': upload.id,
            'company_id': upload.company_id,
            'file_type': upload.file_type,
            'original_filename': upload.original_filename,
            'file_path': upload.file_path,
            'file_size': upload.file_size,
            'file_size_display': self._format_file_size(upload.file_size),
            'status': upload.status,
            'status_display': status_info,
            'uploaded_by': upload.uploaded_by,
            'uploaded_at': upload.uploaded_at.isoformat(),
            'processed_at': upload.processed_at.isoformat() if upload.processed_at else None,
            'error_message': upload.error_message,
            'raw_document_id': upload.raw_document_id,
            'metadata': metadata,
            'file_exists': file_exists
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def get_upload_stats(self, company_id: Optional[int] = None) -> Dict:
        """获取上传统计"""
        conditions = []
        if company_id is not None:
            conditions.append(UploadStaging.company_id == company_id)
        
        base_query = select(UploadStaging)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        total_stmt = select(func.count()).select_from(base_query.subquery())
        result = self.db.execute(total_stmt)
        total = result.scalar()
        
        completed_stmt = base_query.where(UploadStaging.status == 'completed')
        result = self.db.execute(select(func.count()).select_from(completed_stmt.subquery()))
        completed = result.scalar()
        
        processing_stmt = base_query.where(UploadStaging.status == 'processing')
        result = self.db.execute(select(func.count()).select_from(processing_stmt.subquery()))
        processing = result.scalar()
        
        failed_stmt = base_query.where(UploadStaging.status == 'failed')
        result = self.db.execute(select(func.count()).select_from(failed_stmt.subquery()))
        failed = result.scalar()
        
        size_stmt = select(func.sum(UploadStaging.file_size)).select_from(base_query.subquery())
        result = self.db.execute(size_stmt)
        total_size = result.scalar() or 0
        
        return {
            'total': total,
            'completed': completed,
            'processing': processing,
            'failed': failed,
            'total_size': total_size,
            'total_size_display': self._format_file_size(total_size)
        }
    
    def link_to_raw_document(
        self,
        upload_id: int,
        raw_document_id: int
    ) -> UploadStaging:
        """关联到RawDocument"""
        stmt = select(UploadStaging).where(UploadStaging.id == upload_id)
        result = self.db.execute(stmt)
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise ValueError(f"上传记录 {upload_id} 不存在 / Upload record not found")
        
        stmt = select(RawDocument).where(RawDocument.id == raw_document_id)
        result = self.db.execute(stmt)
        raw_doc = result.scalar_one_or_none()
        
        if not raw_doc:
            raise ValueError(f"RawDocument {raw_document_id} 不存在 / RawDocument not found")
        
        if upload.company_id != raw_doc.company_id:
            raise ValueError("公司ID不匹配 / Company ID mismatch")
        
        upload.raw_document_id = raw_document_id
        upload.status = 'completed'
        upload.processed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(upload)
        
        return upload
    
    def get_orphan_uploads(
        self,
        company_id: Optional[int] = None,
        days_old: int = 7
    ) -> List[Dict]:
        """
        获取孤儿文件（已上传但未关联到RawDocument的文件）
        
        Args:
            company_id: 公司ID
            days_old: 天数阈值（超过多少天未处理）
        """
        from datetime import timedelta
        
        conditions = [
            UploadStaging.raw_document_id.is_(None),
            UploadStaging.status.in_(['uploaded', 'processing'])
        ]
        
        if company_id is not None:
            conditions.append(UploadStaging.company_id == company_id)
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        conditions.append(UploadStaging.uploaded_at < cutoff_date)
        
        stmt = select(UploadStaging).where(and_(*conditions)).order_by(
            desc(UploadStaging.uploaded_at)
        )
        
        result = self.db.execute(stmt)
        uploads = result.scalars().all()
        
        return [self._format_upload(upload) for upload in uploads]
    
    def archive_upload(
        self,
        upload_id: int,
        archived_by: str,
        archive_reason: Optional[str] = None
    ) -> UploadStaging:
        """归档文件"""
        stmt = select(UploadStaging).where(UploadStaging.id == upload_id)
        result = self.db.execute(stmt)
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise ValueError(f"上传记录 {upload_id} 不存在 / Upload record not found")
        
        upload.status = 'archived'
        upload.processed_at = datetime.now()
        
        if archive_reason:
            import json
            metadata = {}
            if upload.metadata:
                try:
                    metadata = json.loads(upload.metadata)
                except:
                    pass
            
            metadata['archive_reason'] = archive_reason
            metadata['archived_by'] = archived_by
            metadata['archived_at'] = datetime.now().isoformat()
            
            upload.metadata = json.dumps(metadata)
        
        self.db.commit()
        self.db.refresh(upload)
        
        return upload
    
    def cleanup_old_uploads(
        self,
        company_id: Optional[int] = None,
        days_old: int = 90,
        delete_files: bool = False
    ) -> Dict:
        """
        清理旧文件
        
        Args:
            company_id: 公司ID
            days_old: 天数阈值
            delete_files: 是否删除物理文件
        
        Returns:
            {
                'archived': 归档数量,
                'deleted_files': 删除文件数量
            }
        """
        from datetime import timedelta
        
        conditions = [
            UploadStaging.status.in_(['completed', 'failed']),
        ]
        
        if company_id is not None:
            conditions.append(UploadStaging.company_id == company_id)
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        conditions.append(UploadStaging.uploaded_at < cutoff_date)
        
        stmt = select(UploadStaging).where(and_(*conditions))
        result = self.db.execute(stmt)
        uploads = result.scalars().all()
        
        archived = 0
        deleted_files = 0
        
        for upload in uploads:
            if upload.status != 'archived':
                upload.status = 'archived'
                archived += 1
            
            if delete_files and upload.file_path and os.path.exists(upload.file_path):
                try:
                    os.remove(upload.file_path)
                    deleted_files += 1
                except Exception:
                    pass
        
        self.db.commit()
        
        return {
            'archived': archived,
            'deleted_files': deleted_files
        }
