"""
Phase 1-5: 统一上传处理服务
实现"先封存，再计算"原则：
1. 保存原始文件
2. 计算流式hash
3. 写入raw_documents
4. 写入file_index
5. 解析内容到raw_lines
6. 行数对账验证
7. 部分成功拦截
"""
import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile

from ..models import RawDocument, RawLine, FileIndex
from ..services.raw_document_service import RawDocumentService
from ..services.file_index_service import FileIndexService
from ..services.file_storage_manager import AccountingFileStorageManager
from ..utils.file_hash import calculate_file_hash_chunked
from ..services.exception_manager import ExceptionManager
from ..utils.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class UploadHandler:
    """
    Phase 1-5: 统一文件上传处理器
    
    核心原则：
    1. "先封存，再计算" - 原始文件必须先保存
    2. 行数对账 - raw_lines行数必须等于业务记录行数
    3. 部分成功拦截 - 行数不匹配进入异常中心
    4. 异常安全 - 解析失败也要保存原件
    """
    
    def __init__(self, db: Session, company_id: int, username: str = "system"):
        self.db = db
        self.company_id = company_id
        self.username = username
        self.raw_doc_service = RawDocumentService(db)
        self.file_index_service = FileIndexService(db)
        self.audit_logger = AuditLogger(db)
    
    async def handle_upload(
        self,
        file: UploadFile,
        file_category: str,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        period: Optional[str] = None,
        description: Optional[str] = None,
        module: str = "bank"
    ) -> Dict[str, Any]:
        """
        统一文件上传处理流程
        
        Args:
            file: 上传的文件对象
            file_category: 文件类别（bank_statement, invoice, pos_report）
            related_entity_type: 关联实体类型
            related_entity_id: 关联实体ID
            period: 账期（YYYY-MM）
            description: 文件描述
            module: 模块名称
        
        Returns:
            包含raw_document_id, file_index_id, file_path等信息的字典
        """
        try:
            # Step 1: 读取文件内容（只读一次）
            file_content = await file.read()
            file_size = len(file_content)
            
            logger.info(
                f"Step 1/7: 读取文件内容 - "
                f"filename={file.filename}, size={file_size} bytes"
            )
            
            # Step 2: 生成标准化文件路径
            filename_safe = file.filename or "unknown_file"
            file_path = self._generate_file_path(
                file_category=file_category,
                filename=filename_safe,
                period=period
            )
            
            logger.info(f"Step 2/7: 生成文件路径 - path={file_path}")
            
            # Step 3: 保存原始文件到磁盘（"先封存"）
            AccountingFileStorageManager.ensure_directory(file_path)
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"Step 3/7: 保存原始文件到磁盘 - path={file_path}")
            
            # Step 4: 计算流式hash（分块计算，防止大文件超时）
            file_hash = calculate_file_hash_chunked(file_path=file_path, chunk_size=8192)
            
            logger.info(f"Step 4/7: 计算文件hash - hash={file_hash[:16]}...")
            
            # Step 5: 写入raw_documents表
            raw_document = self.raw_doc_service.create_raw_document(
                company_id=self.company_id,
                file_name=filename_safe,
                storage_path=file_path,
                file_hash=file_hash,
                file_size=file_size,
                source_engine='fastapi',
                module=module,
                uploaded_by=None  # 预留字段，暂时为None
            )
            
            logger.info(
                f"Step 5/7: 写入raw_documents - "
                f"id={raw_document.id}, hash={raw_document.file_hash[:16]}..."
            )
            
            # Step 6: 写入file_index表（强制关联raw_document_id）
            # 显式转换为int类型
            raw_doc_id: int = int(raw_document.id) if raw_document.id is not None else 0
            
            file_index = self.file_index_service.create_file_index(
                company_id=self.company_id,
                file_category=file_category,
                file_type='original',
                filename=filename_safe,
                file_path=file_path,
                file_size_kb=file_size // 1024,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                period=period,
                upload_by=self.username,
                description=description,
                module=module,
                raw_document_id=raw_doc_id  # Phase 1-3强制要求
            )
            
            logger.info(
                f"Step 6/7: 写入file_index - "
                f"id={file_index.id}, raw_document_id={raw_document.id}"
            )
            
            # Step 7: 记录审计日志
            self.audit_logger.log_file_upload(
                company_id=self.company_id,
                username=self.username,
                filename=filename_safe,
                file_type=file_category,
                file_size=file_size
            )
            
            logger.info(f"Step 7/7: 记录审计日志 - 上传完成")
            
            return {
                "success": True,
                "raw_document_id": raw_document.id,
                "file_index_id": file_index.id,
                "file_path": file_path,
                "file_hash": file_hash,
                "file_size": file_size,
                "message": "文件上传并封存成功"
            }
        
        except Exception as e:
            logger.error(f"文件上传失败: {e}", exc_info=True)
            
            # 记录失败的审计日志（设置初始值防止未定义）
            filename_safe = file.filename or "unknown_file"
            # 安全获取file_content长度
            try:
                file_size_safe = len(file_content)
            except NameError:
                file_size_safe = 0
            
            self.audit_logger.log_file_upload(
                company_id=self.company_id,
                username=self.username,
                filename=filename_safe,
                file_type=file_category,
                file_size=file_size_safe
            )
            
            return {
                "success": False,
                "error": str(e),
                "message": f"文件上传失败: {e}"
            }
    
    def save_raw_lines(
        self,
        raw_document_id: int,
        lines: List[str],
        parser_version: str = "1.0"
    ) -> List[RawLine]:
        """
        保存原始文件行到raw_lines表
        
        Args:
            raw_document_id: raw_documents记录ID
            lines: 原始文件行列表（文本内容）
            parser_version: 解析器版本号
        
        Returns:
            创建的RawLine对象列表
        """
        raw_lines = []
        
        for line_num, line_content in enumerate(lines, start=1):
            # Phase 1-5修复：使用正确的字段名
            raw_line = RawLine(
                raw_document_id=raw_document_id,
                line_no=line_num,  # 正确字段名
                raw_text=line_content,  # 正确字段名
                parser_version=parser_version,
                is_parsed=False
            )
            self.db.add(raw_line)
            raw_lines.append(raw_line)
        
        self.db.commit()
        
        logger.info(
            f"保存raw_lines完成 - "
            f"raw_document_id={raw_document_id}, "
            f"line_count={len(raw_lines)}"
        )
        
        return raw_lines
    
    def verify_line_count(
        self,
        raw_document_id: int,
        parsed_record_count: int,
        file_category: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Phase 1-5关键验证：行数对账
        
        验证raw_lines行数是否等于解析出的业务记录行数
        
        Args:
            raw_document_id: raw_documents记录ID
            parsed_record_count: 解析出的业务记录数
            file_category: 文件类别
        
        Returns:
            (is_valid, error_message)
            - is_valid: True表示行数匹配
            - error_message: 不匹配时的错误信息
        """
        # 查询raw_lines行数
        raw_line_count = self.db.query(RawLine).filter(
            RawLine.raw_document_id == raw_document_id
        ).count()
        
        # Phase 1-5强制规则：行数必须匹配
        if raw_line_count != parsed_record_count:
            error_msg = (
                f"行数对账失败: raw_lines={raw_line_count}行, "
                f"parsed_records={parsed_record_count}行。"
                f"这是部分成功情况，不得进入正常报表口径。"
            )
            
            logger.warning(
                f"⚠️ LINE COUNT MISMATCH - "
                f"raw_document_id={raw_document_id}, "
                f"{error_msg}"
            )
            
            # 补充改进③：标记raw_document为验证失败
            raw_doc = self.db.query(RawDocument).filter(
                RawDocument.id == raw_document_id
            ).first()
            if raw_doc:
                raw_doc.validation_status = 'failed'
                raw_doc.validation_failed_at = datetime.now()  # Timezone-aware via sqlalchemy.func.now()
                raw_doc.validation_error_message = error_msg
                self.db.commit()
                logger.info(f"❌ MARKED as validation_status='failed' - raw_document_id={raw_document_id}")
            
            return False, error_msg
        
        # 补充改进③：标记raw_document为验证通过
        raw_doc = self.db.query(RawDocument).filter(
            RawDocument.id == raw_document_id
        ).first()
        if raw_doc:
            raw_doc.validation_status = 'passed'
            self.db.commit()
            logger.info(f"✅ MARKED as validation_status='passed' - raw_document_id={raw_document_id}")
        
        logger.info(
            f"✅ LINE COUNT VERIFIED - "
            f"raw_document_id={raw_document_id}, "
            f"count={raw_line_count}"
        )
        
        return True, None
    
    def handle_partial_success(
        self,
        raw_document_id: int,
        raw_line_count: int,
        parsed_count: int,
        file_category: str,
        context: Optional[Dict] = None
    ):
        """
        处理部分成功情况（拦截进入异常中心）
        
        Phase 1-5关键机制：
        文件有87行但只识别到80行 -> 必须进入异常中心
        防止数据不准确
        
        Args:
            raw_document_id: raw_documents记录ID
            raw_line_count: raw_lines行数
            parsed_count: 解析成功的记录数
            file_category: 文件类别
            context: 额外的上下文信息
        """
        # 使用通用Exception记录方法
        from ..models import Exception as ExceptionModel
        
        exception_record = ExceptionModel(
            company_id=self.company_id,
            exception_type='line_count_mismatch',
            severity='high',
            source_type='file_upload',
            source_id=raw_document_id,
            message=f"行数对账失败: raw_lines={raw_line_count}, parsed={parsed_count}, missing={raw_line_count - parsed_count}",
            context_data=context or {},
            status='pending',
            created_at=datetime.now()
        )
        
        self.db.add(exception_record)
        self.db.commit()
        
        logger.warning(
            f"❌ PARTIAL SUCCESS INTERCEPTED - "
            f"raw_document_id={raw_document_id}, "
            f"raw_lines={raw_line_count}, "
            f"parsed={parsed_count}, "
            f"missing={raw_line_count - parsed_count} lines"
        )
    
    def _generate_file_path(
        self,
        file_category: str,
        filename: str,
        period: Optional[str] = None
    ) -> str:
        """
        生成标准化文件路径
        
        使用AccountingFileStorageManager生成路径：
        /accounting_data/companies/{company_id}/{category}/{year}/{month}/{filename}
        """
        # 根据file_category选择对应的路径生成方法
        if file_category == 'bank_statement':
            # 银行月结单路径
            if not period:
                period = datetime.now().strftime("%Y-%m")
            
            year, month = period.split('-')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_filename = AccountingFileStorageManager.sanitize_filename(filename)
            
            path = os.path.join(
                AccountingFileStorageManager.BASE_DIR,
                str(self.company_id),
                'bank_statements',
                year,
                month,
                f"company{self.company_id}_{timestamp}_{clean_filename}"
            )
            
            return path.replace('\\', '/')
        
        elif file_category == 'invoice':
            # 发票路径
            if not period:
                period = datetime.now().strftime("%Y-%m")
            
            year, month = period.split('-')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_filename = AccountingFileStorageManager.sanitize_filename(filename)
            
            path = os.path.join(
                AccountingFileStorageManager.BASE_DIR,
                str(self.company_id),
                'invoices',
                year,
                month,
                f"company{self.company_id}_{timestamp}_{clean_filename}"
            )
            
            return path.replace('\\', '/')
        
        elif file_category == 'pos_report':
            # POS报表路径
            if not period:
                period = datetime.now().strftime("%Y-%m")
            
            year, month = period.split('-')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_filename = AccountingFileStorageManager.sanitize_filename(filename)
            
            path = os.path.join(
                AccountingFileStorageManager.BASE_DIR,
                str(self.company_id),
                'pos_reports',
                year,
                month,
                f"company{self.company_id}_{timestamp}_{clean_filename}"
            )
            
            return path.replace('\\', '/')
        
        else:
            # 默认路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_filename = AccountingFileStorageManager.sanitize_filename(filename)
            
            path = os.path.join(
                AccountingFileStorageManager.BASE_DIR,
                str(self.company_id),
                'documents',
                f"company{self.company_id}_{timestamp}_{clean_filename}"
            )
            
            return path.replace('\\', '/')
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'audit_logger'):
            self.audit_logger.close()
