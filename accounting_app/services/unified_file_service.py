"""
统一文件管理服务
处理Flask和FastAPI双引擎的文件上传、索引、查询
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
from ..models import FileIndex, Company
from ..services.file_storage_manager import AccountingFileStorageManager
import logging

logger = logging.getLogger(__name__)


class UnifiedFileService:
    """统一文件管理服务"""
    
    @staticmethod
    def register_file(
        db: Session,
        company_id: int,
        filename: str,
        file_path: str,
        module: str,
        from_engine: str = 'flask',
        uploaded_by: str = None,
        file_size_kb: int = None,
        validation_status: str = 'pending',
        status: str = 'processing',
        metadata: Dict = None
    ) -> FileIndex:
        """
        注册文件到统一索引表
        所有上传（Flask和FastAPI）都要调用这个方法
        """
        try:
            # 提取文件信息
            file_extension = os.path.splitext(filename)[1].lower()
            original_filename = filename
            
            # 从路径推断period (YYYY-MM)
            period = None
            if '/202' in file_path:
                parts = file_path.split('/')
                for i, part in enumerate(parts):
                    if part.startswith('202') and len(part) == 4 and i + 1 < len(parts):
                        year = part
                        month = parts[i + 1]
                        if month.isdigit() and 1 <= int(month) <= 12:
                            period = f"{year}-{month.zfill(2)}"
                            break
            
            # 创建文件索引
            file_record = FileIndex(
                company_id=company_id,
                file_category=module,  # 使用module作为category
                file_type='original',  # ✅ 修复：使用有效的枚举值
                filename=filename,
                file_path=file_path,
                file_size_kb=file_size_kb,
                file_extension=file_extension,
                module=module,
                status=status,
                from_engine=from_engine,
                validation_status=validation_status,
                upload_by=uploaded_by,
                upload_date=datetime.utcnow(),
                original_filename=original_filename,
                period=period,
                is_active=True
            )
            
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            logger.info(f"File registered: {filename} (ID: {file_record.id}, company: {company_id}, module: {module})")
            return file_record
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to register file: {str(e)}")
            raise
    
    @staticmethod
    def get_recent_files(
        db: Session,
        company_id: int,
        limit: int = 10,
        module: Optional[str] = None
    ) -> List[Dict]:
        """
        获取最近上传的文件
        前端首页只用这个接口
        """
        query = db.query(FileIndex).filter(
            FileIndex.company_id == company_id,
            FileIndex.is_active == True
        )
        
        if module:
            query = query.filter(FileIndex.module == module)
        
        files = query.order_by(desc(FileIndex.upload_date)).limit(limit).all()
        
        results = []
        for file in files:
            # 判断是否是10分钟内的新文件
            is_new = (datetime.utcnow() - file.upload_date) < timedelta(minutes=10)
            
            results.append({
                "file_id": file.id,
                "file_name": file.filename,
                "module": file.module,
                "storage_path": file.file_path,
                "status": file.status,
                "uploaded_at": file.upload_date.isoformat(),
                "uploaded_by": file.upload_by or "system",
                "from_engine": file.from_engine,
                "validation_status": file.validation_status,
                "is_new": is_new,
                "file_size_kb": file.file_size_kb,
                "period": file.period
            })
        
        return results
    
    @staticmethod
    def get_file_with_fallback(
        db: Session,
        file_id: int,
        company_id: int
    ) -> Dict:
        """
        文件详情降级策略
        1. 按新目录找
        2. 按旧目录找
        3. 返回缺失提示
        """
        file_record = db.query(FileIndex).filter(
            FileIndex.id == file_id,
            FileIndex.company_id == company_id
        ).first()
        
        if not file_record:
            return {
                "status": "not_found",
                "message": "文件记录不存在",
                "can_reupload": False
            }
        
        # Step 1: 检查新目录
        new_path = file_record.file_path
        if os.path.exists(new_path):
            return {
                "status": "found",
                "file": {
                    "file_id": file_record.id,
                    "file_name": file_record.filename,
                    "file_path": new_path,
                    "module": file_record.module,
                    "uploaded_at": file_record.upload_date.isoformat(),
                    "uploaded_by": file_record.upload_by,
                    "validation_status": file_record.validation_status,
                    "file_status": file_record.status,
                    "legacy_path": False
                }
            }
        
        # Step 2: 检查旧目录
        legacy_paths = [
            f"static/uploads/{file_record.filename}",
            f"static/uploads/customers/{file_record.filename}",
            f"static/uploads/company_{company_id}/{file_record.filename}"
        ]
        
        for legacy_path in legacy_paths:
            if os.path.exists(legacy_path):
                logger.warning(f"File found in legacy path: {legacy_path}")
                return {
                    "status": "found",
                    "file": {
                        "file_id": file_record.id,
                        "file_name": file_record.filename,
                        "file_path": legacy_path,
                        "module": file_record.module,
                        "uploaded_at": file_record.upload_date.isoformat(),
                        "uploaded_by": file_record.upload_by,
                        "validation_status": file_record.validation_status,
                        "file_status": file_record.status,
                        "legacy_path": True
                    }
                }
        
        # Step 3: 文件实体不存在
        logger.error(f"File missing: ID={file_id}, path={new_path}")
        return {
            "status": "missing",
            "message": "这是历史记录，文件实体已不存在，请重新上传。",
            "file_id": file_id,
            "file_name": file_record.filename,
            "module": file_record.module,
            "can_reupload": True
        }
    
    @staticmethod
    def update_file_status(
        db: Session,
        file_id: int,
        status: str = None,
        validation_status: str = None
    ):
        """更新文件状态"""
        file_record = db.query(FileIndex).filter(FileIndex.id == file_id).first()
        if not file_record:
            return False
        
        if status:
            file_record.status = status
        if validation_status:
            file_record.validation_status = validation_status
        
        db.commit()
        return True
