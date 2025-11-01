"""
Phase 1-3: 统一文件索引服务
确保Flask和FastAPI共用一套文件索引
关键规则：Flask上传完成后必须把company_id/customer_id识别结果一并传给FastAPI
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from ..models import FileIndex, Company


class FileIndexService:
    """
    统一文件索引服务
    负责：文件索引创建、查询、软删除、回收站管理
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_file_index(
        self,
        company_id: int,
        file_category: str,
        file_type: str,
        filename: str,
        file_path: str,
        module: str,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        file_size_kb: Optional[int] = None,
        file_extension: Optional[str] = None,
        mime_type: Optional[str] = None,
        period: Optional[str] = None,
        transaction_date: Optional[datetime] = None,
        upload_by: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
        raw_document_id: Optional[int] = None  # Phase 1-3修复：强制关联raw_documents
    ) -> FileIndex:
        """
        创建文件索引记录
        
        Args:
            company_id: 公司ID（必须）
            file_category: 文件分类（bank_statement, invoice, receipt, report）
            file_type: 文件类型（original | generated）
            filename: 文件名
            file_path: 文件路径
            module: 模块（credit-card | bank | savings | pos | supplier | reports）
            related_entity_type: 关联实体类型（可选）
            related_entity_id: 关联实体ID（可选）
            raw_document_id: raw_documents记录ID（强制，防绕过）
            其他参数：文件元数据
        
        Returns:
            FileIndex对象
        
        Raises:
            ValueError: 如果company_id无效、module不合法、或缺少raw_document_id
        """
        # Phase 1-3修复：强制验证raw_documents存在，防止绕过1:1封存
        from ..models import RawDocument
        
        if file_type == 'original' and not raw_document_id:
            raise ValueError(
                "原始文件（file_type='original'）必须先写入raw_documents表，然后传递raw_document_id。"
                "这是防虚构交易的强制规则，不可绕过。"
            )
        
        if raw_document_id:
            raw_doc = self.db.query(RawDocument).filter(RawDocument.id == raw_document_id).first()
            if not raw_doc:
                raise ValueError(f"raw_document_id {raw_document_id} 不存在，无法创建文件索引")
            
            # 验证路径一致性
            if raw_doc.storage_path != file_path:
                raise ValueError(
                    f"文件路径不匹配：raw_documents中为 {raw_doc.storage_path}，"
                    f"但传入的file_path为 {file_path}"
                )
        
        # 验证company_id
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"公司ID {company_id} 不存在")
        
        # 验证module
        valid_modules = ['credit-card', 'bank', 'savings', 'pos', 'supplier', 'reports', 'management', 'temp']
        if module and module not in valid_modules:
            raise ValueError(f"模块 {module} 不合法，必须是 {valid_modules} 之一")
        
        # 创建文件索引
        file_index = FileIndex(
            company_id=company_id,
            file_category=file_category,
            file_type=file_type,
            filename=filename,
            file_path=file_path,
            module=module,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            file_size_kb=file_size_kb,
            file_extension=file_extension,
            mime_type=mime_type,
            period=period,
            transaction_date=transaction_date,
            upload_by=upload_by,
            description=description,
            tags=tags,
            status='active',
            is_active=True,
            upload_date=datetime.now()
        )
        
        self.db.add(file_index)
        self.db.commit()
        self.db.refresh(file_index)
        
        return file_index
    
    def get_file_index(self, file_id: int) -> Optional[FileIndex]:
        """
        获取文件索引（只返回active状态的文件）
        """
        return self.db.query(FileIndex).filter(
            FileIndex.id == file_id,
            FileIndex.status == 'active'
        ).first()
    
    def list_files(
        self,
        company_id: int,
        module: Optional[str] = None,
        file_category: Optional[str] = None,
        status: str = 'active',
        limit: int = 100,
        offset: int = 0
    ) -> List[FileIndex]:
        """
        查询文件列表
        
        Args:
            company_id: 公司ID
            module: 模块过滤（可选）
            file_category: 分类过滤（可选）
            status: 状态过滤（默认active）
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            文件索引列表
        """
        query = self.db.query(FileIndex).filter(
            FileIndex.company_id == company_id,
            FileIndex.status == status
        )
        
        if module:
            query = query.filter(FileIndex.module == module)
        
        if file_category:
            query = query.filter(FileIndex.file_category == file_category)
        
        return query.order_by(FileIndex.created_at.desc()).limit(limit).offset(offset).all()
    
    def soft_delete(self, file_id: int, deleted_by: Optional[str] = None) -> bool:
        """
        软删除文件（标记为deleted，不物理删除）
        
        Args:
            file_id: 文件ID
            deleted_by: 删除人（可选）
        
        Returns:
            是否成功
        """
        file_index = self.db.query(FileIndex).filter(FileIndex.id == file_id).first()
        
        if not file_index:
            return False
        
        file_index.status = 'deleted'  # type: ignore
        file_index.deleted_at = datetime.now()  # type: ignore
        file_index.is_active = False  # type: ignore
        
        self.db.commit()
        return True
    
    def archive(self, file_id: int) -> bool:
        """
        归档文件（标记为archived）
        """
        file_index = self.db.query(FileIndex).filter(FileIndex.id == file_id).first()
        
        if not file_index:
            return False
        
        file_index.status = 'archived'  # type: ignore
        self.db.commit()
        return True
    
    def restore(self, file_id: int) -> bool:
        """
        从回收站恢复文件
        """
        file_index = self.db.query(FileIndex).filter(
            FileIndex.id == file_id,
            FileIndex.status.in_(['deleted', 'archived'])  # type: ignore
        ).first()
        
        if not file_index:
            return False
        
        file_index.status = 'active'  # type: ignore
        file_index.deleted_at = None  # type: ignore
        file_index.is_active = True  # type: ignore
        
        self.db.commit()
        return True
    
    def get_recyclebin(self, company_id: int) -> List[FileIndex]:
        """
        获取回收站文件列表（deleted状态的文件）
        """
        return self.db.query(FileIndex).filter(
            FileIndex.company_id == company_id,
            FileIndex.status == 'deleted'
        ).order_by(FileIndex.deleted_at.desc()).all()
    
    def permanent_delete(self, file_id: int) -> bool:
        """
        永久删除文件索引记录（物理删除）
        注意：这不会删除实际文件，只删除索引记录
        """
        file_index = self.db.query(FileIndex).filter(
            FileIndex.id == file_id,
            FileIndex.status == 'deleted'
        ).first()
        
        if not file_index:
            return False
        
        self.db.delete(file_index)
        self.db.commit()
        return True
    
    def cleanup_expired_deleted_files(self, days: int = 30) -> int:
        """
        清理过期的已删除文件（超过N天的deleted文件）
        
        Args:
            days: 保留天数（默认30天）
        
        Returns:
            清理的文件数量
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        expired_files = self.db.query(FileIndex).filter(
            FileIndex.status == 'deleted',
            FileIndex.deleted_at < cutoff_date
        ).all()
        
        count = len(expired_files)
        
        for file in expired_files:
            self.db.delete(file)
        
        self.db.commit()
        return count
    
    def find_orphan_files(self, company_id: int) -> List[FileIndex]:
        """
        查找孤儿文件（没有related_entity_id的文件）
        """
        return self.db.query(FileIndex).filter(
            FileIndex.company_id == company_id,
            FileIndex.related_entity_id.is_(None),  # type: ignore
            FileIndex.status == 'active'
        ).all()
    
    def link_to_entity(
        self,
        file_id: int,
        related_entity_type: str,
        related_entity_id: int
    ) -> bool:
        """
        将文件关联到业务实体
        """
        file_index = self.db.query(FileIndex).filter(FileIndex.id == file_id).first()
        
        if not file_index:
            return False
        
        file_index.related_entity_type = related_entity_type  # type: ignore
        file_index.related_entity_id = related_entity_id  # type: ignore
        
        self.db.commit()
        return True
