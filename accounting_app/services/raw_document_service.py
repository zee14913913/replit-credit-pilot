"""
Phase 1-1: 原件保护服务
核心规则：
1. 所有上传必须先写raw_documents + 计算分块hash
2. 解析成功后逐行写入raw_lines
3. raw_lines行数 ≠ 解析行数时，标记为不可入账，进异常中心
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..models import RawDocument, RawLine, Exception as ExceptionModel
from ..utils.file_hash import calculate_file_hash_chunked, calculate_uploaded_file_hash


class RawDocumentService:
    """
    原件保护服务
    负责：1:1原件保存、行数对账、异常标记
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_raw_document(
        self,
        company_id: int,
        file_name: str,
        storage_path: str,
        file_hash: str,
        file_size: int,
        source_engine: str,  # 'flask' | 'fastapi'
        module: str,  # 'credit-card' | 'bank' | 'savings' | 'pos' | 'supplier'
        uploaded_by: Optional[int] = None
    ) -> RawDocument:
        """
        创建原件记录（上传时立即调用）
        
        Args:
            company_id: 公司ID
            file_name: 文件名
            storage_path: 存储路径
            file_hash: 分块SHA256哈希值
            file_size: 文件大小（字节）
            source_engine: 来源引擎（flask/fastapi）
            module: 模块分类
            uploaded_by: 上传人ID（可选）
        
        Returns:
            RawDocument对象
        """
        raw_doc = RawDocument(
            company_id=company_id,
            file_name=file_name,
            storage_path=storage_path,
            file_hash=file_hash,
            file_size=file_size,
            source_engine=source_engine,
            module=module,
            uploaded_by=uploaded_by,
            status='uploaded',
            uploaded_at=datetime.now()
        )
        
        self.db.add(raw_doc)
        self.db.commit()
        self.db.refresh(raw_doc)
        
        return raw_doc
    
    def save_raw_lines(
        self,
        raw_document_id: int,
        lines: List[Dict[str, Any]],
        parser_version: str = "1.0"
    ) -> int:
        """
        保存原始文本逐行记录
        
        Args:
            raw_document_id: 原件记录ID
            lines: 行数据列表，格式：[
                {'line_no': 1, 'page_no': 1, 'raw_text': '...'},
                {'line_no': 2, 'page_no': 1, 'raw_text': '...'},
            ]
            parser_version: 解析器版本号
        
        Returns:
            保存的行数
        """
        raw_line_objects = []
        
        for line_data in lines:
            raw_line = RawLine(
                raw_document_id=raw_document_id,
                line_no=line_data['line_no'],
                page_no=line_data.get('page_no'),
                raw_text=line_data['raw_text'],
                parser_version=parser_version,
                is_parsed=False
            )
            raw_line_objects.append(raw_line)
        
        self.db.bulk_save_objects(raw_line_objects)
        self.db.commit()
        
        return len(raw_line_objects)
    
    def reconcile_document(
        self,
        raw_document_id: int,
        total_lines: int,
        parsed_lines: int
    ) -> dict:
        """
        核心规则：行数对账检查
        
        规则：
        - total_lines（PDF/CSV总行数）必须 == raw_lines表中的记录数
        - parsed_lines（成功解析行数）必须 == total_lines
        - 任何不匹配都标记为 mismatch，不允许入账
        
        Args:
            raw_document_id: 原件ID
            total_lines: 文件总行数
            parsed_lines: 成功解析行数
        
        Returns:
            dict: {
                'status': 'match' | 'mismatch',
                'can_post': bool,
                'reason': str
            }
        """
        # 1. 查询raw_document
        raw_doc = self.db.query(RawDocument).filter(
            RawDocument.id == raw_document_id
        ).first()
        
        if not raw_doc:
            raise ValueError(f"RawDocument {raw_document_id} 不存在")
        
        # 2. 统计raw_lines实际行数
        actual_raw_lines = self.db.query(RawLine).filter(
            RawLine.raw_document_id == raw_document_id
        ).count()
        
        # 3. 对账逻辑
        result = {
            'status': 'match',
            'can_post': False,
            'reason': '',
            'total_lines': total_lines,
            'parsed_lines': parsed_lines,
            'actual_raw_lines': actual_raw_lines
        }
        
        # 规则1：raw_lines行数 必须等于 total_lines
        if actual_raw_lines != total_lines:
            result['status'] = 'mismatch'
            result['reason'] = f"RAW_LINES_MISMATCH: 文件声称{total_lines}行，但raw_lines表只有{actual_raw_lines}行"
        
        # 规则2：parsed_lines 必须等于 total_lines
        elif parsed_lines < total_lines:
            result['status'] = 'mismatch'
            result['reason'] = f"PARTIAL_PARSE: 文件有{total_lines}行，只解析了{parsed_lines}行"
        
        # 规则3：全部匹配
        elif actual_raw_lines == total_lines == parsed_lines:
            result['status'] = 'match'
            result['can_post'] = True
            result['reason'] = "FULL_MATCH: 所有行数一致，可以入账"
        
        # 4. 更新raw_document状态
        raw_doc.total_lines = total_lines  # type: ignore
        raw_doc.parsed_lines = parsed_lines  # type: ignore
        raw_doc.reconciliation_status = result['status']  # type: ignore
        
        if result['status'] == 'match':
            raw_doc.status = 'reconciled'  # type: ignore
        else:
            raw_doc.status = 'failed'  # type: ignore
        
        self.db.commit()
        
        # 5. 如果不匹配，写入异常中心
        if result['status'] == 'mismatch':
            self._create_reconciliation_exception(raw_doc, result['reason'])
        
        return result
    
    def _create_reconciliation_exception(self, raw_doc: RawDocument, reason: str):
        """
        创建对账异常记录（行数不匹配时）
        """
        exception = ExceptionModel(
            company_id=raw_doc.company_id,
            exception_type='RECONCILIATION_FAILED',
            severity='high',
            source_type=raw_doc.module,
            source_id=raw_doc.id,
            error_message=reason,
            details=f"文件: {raw_doc.file_name}, total_lines: {raw_doc.total_lines}, parsed_lines: {raw_doc.parsed_lines}",
            status='open'
        )
        
        self.db.add(exception)
        self.db.commit()
    
    def mark_line_as_parsed(self, raw_line_id: int):
        """
        标记某行已被解析成业务记录
        """
        raw_line = self.db.query(RawLine).filter(RawLine.id == raw_line_id).first()
        if raw_line:
            raw_line.is_parsed = True  # type: ignore
            self.db.commit()
    
    def get_document_by_hash(self, file_hash: str) -> Optional[RawDocument]:
        """
        根据hash查找文件（防重复上传）
        """
        return self.db.query(RawDocument).filter(
            RawDocument.file_hash == file_hash
        ).first()
    
    def get_raw_lines(self, raw_document_id: int) -> List[RawLine]:
        """
        获取某文件的所有原始行
        """
        return self.db.query(RawLine).filter(
            RawLine.raw_document_id == raw_document_id
        ).order_by(RawLine.line_no).all()
