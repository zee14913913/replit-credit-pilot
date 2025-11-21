
"""
Phase 1-11: 文件上传确认系统 - Service层
"""
import os
import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from datetime import datetime

from ..models import PendingFile, User, Company
from ..schemas.pending_file_schemas import (
    PendingFileCreate, 
    PendingFileConfirm, 
    PendingFileReject,
    CustomerMatchInfo
)

logger = logging.getLogger(__name__)


class PendingFileService:
    """文件上传确认服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_pending_file(
        self,
        original_filename: str,
        file_path: str,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None,
        extracted_info: Optional[Dict[str, Any]] = None
    ) -> PendingFile:
        """
        创建待确认文件记录
        
        Args:
            original_filename: 原始文件名
            file_path: 文件存储路径
            file_size: 文件大小
            file_hash: 文件哈希
            extracted_info: OCR提取的信息
        """
        pending_file = PendingFile(
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            verification_status='pending'
        )
        
        # 填充OCR提取信息
        if extracted_info:
            pending_file.extracted_customer_name = extracted_info.get('customer_name')
            pending_file.extracted_ic_number = extracted_info.get('ic_number')
            pending_file.extracted_bank = extracted_info.get('bank')
            pending_file.extracted_period = extracted_info.get('period')
            pending_file.extracted_card_last4 = extracted_info.get('card_last4')
            pending_file.extracted_account_number = extracted_info.get('account_number')
            
            # 自动匹配客户
            match_result = self._auto_match_customer(extracted_info)
            if match_result:
                pending_file.matched_customer_id = match_result['customer_id']
                pending_file.matched_company_id = match_result.get('company_id')
                pending_file.match_confidence = match_result['confidence']
                pending_file.match_reason = match_result['reason']
                
                # 高置信度自动确认
                if match_result['confidence'] >= 80:
                    pending_file.verification_status = 'matched'
                else:
                    pending_file.verification_status = 'mismatch'
        
        self.db.add(pending_file)
        self.db.commit()
        self.db.refresh(pending_file)
        
        logger.info(
            f"Created pending file - id={pending_file.id}, "
            f"status={pending_file.verification_status}, "
            f"confidence={pending_file.match_confidence}"
        )
        
        return pending_file
    
    def _auto_match_customer(self, extracted_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        自动匹配客户
        
        匹配规则：
        1. IC号完全匹配 -> 100%
        2. 姓名完全匹配 -> 90%
        3. 姓名模糊匹配 -> 70%
        4. 银行+账号匹配 -> 80%
        """
        customer_name = extracted_info.get('customer_name')
        ic_number = extracted_info.get('ic_number')
        bank = extracted_info.get('bank')
        account_number = extracted_info.get('account_number')
        
        # 规则1: IC号完全匹配
        if ic_number:
            user = self.db.query(User).filter(
                User.ic_number == ic_number
            ).first()
            if user:
                return {
                    'customer_id': user.id,
                    'company_id': user.company_id if hasattr(user, 'company_id') else None,
                    'confidence': 100,
                    'reason': 'IC号完全匹配'
                }
        
        # 规则2: 姓名完全匹配
        if customer_name:
            user = self.db.query(User).filter(
                func.lower(User.name) == func.lower(customer_name)
            ).first()
            if user:
                return {
                    'customer_id': user.id,
                    'company_id': user.company_id if hasattr(user, 'company_id') else None,
                    'confidence': 90,
                    'reason': '姓名完全匹配'
                }
        
        # 规则3: 姓名模糊匹配（使用LIKE）
        if customer_name:
            # 分割姓名，尝试部分匹配
            name_parts = customer_name.upper().split()
            for part in name_parts:
                if len(part) >= 3:  # 至少3个字符
                    users = self.db.query(User).filter(
                        User.name.ilike(f'%{part}%')
                    ).all()
                    
                    if len(users) == 1:  # 唯一匹配
                        return {
                            'customer_id': users[0].id,
                            'company_id': users[0].company_id if hasattr(users[0], 'company_id') else None,
                            'confidence': 70,
                            'reason': f'姓名部分匹配: {part}'
                        }
        
        # 规则4: 银行+账号匹配（需要扩展User表）
        # 暂时跳过，可以后续添加
        
        return None
    
    def get_pending_files(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[PendingFile], int]:
        """
        获取待确认文件列表
        
        Args:
            status: 过滤状态（pending/matched/mismatch/confirmed/rejected）
            limit: 限制数量
            offset: 偏移量
        """
        query = self.db.query(PendingFile)
        
        if status:
            query = query.filter(PendingFile.verification_status == status)
        
        # 未处理的文件优先
        query = query.filter(PendingFile.is_processed == False)
        
        # 按上传时间倒序
        query = query.order_by(desc(PendingFile.uploaded_at))
        
        total = query.count()
        items = query.limit(limit).offset(offset).all()
        
        return items, total
    
    def get_pending_file(self, file_id: int) -> Optional[PendingFile]:
        """获取单个待确认文件"""
        return self.db.query(PendingFile).filter(
            PendingFile.id == file_id
        ).first()
    
    def confirm_file(
        self,
        file_id: int,
        confirmed_by: str,
        matched_customer_id: Optional[int] = None,
        matched_company_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> PendingFile:
        """
        确认文件
        
        Args:
            file_id: 文件ID
            confirmed_by: 确认人
            matched_customer_id: 匹配的客户ID（如果需要修正）
            matched_company_id: 匹配的公司ID
            notes: 备注
        """
        pending_file = self.get_pending_file(file_id)
        if not pending_file:
            raise ValueError(f"Pending file not found: {file_id}")
        
        # 更新匹配信息（如果提供）
        if matched_customer_id:
            pending_file.matched_customer_id = matched_customer_id
        if matched_company_id:
            pending_file.matched_company_id = matched_company_id
        
        # 更新确认信息
        pending_file.verification_status = 'confirmed'
        pending_file.confirmed_by = confirmed_by
        pending_file.confirmed_at = datetime.now()
        pending_file.notes = notes
        
        self.db.commit()
        self.db.refresh(pending_file)
        
        logger.info(
            f"Confirmed pending file - id={file_id}, "
            f"customer_id={pending_file.matched_customer_id}, "
            f"confirmed_by={confirmed_by}"
        )
        
        return pending_file
    
    def reject_file(
        self,
        file_id: int,
        rejected_reason: str,
        rejected_by: str
    ) -> PendingFile:
        """
        拒绝文件
        
        Args:
            file_id: 文件ID
            rejected_reason: 拒绝原因
            rejected_by: 拒绝人
        """
        pending_file = self.get_pending_file(file_id)
        if not pending_file:
            raise ValueError(f"Pending file not found: {file_id}")
        
        pending_file.verification_status = 'rejected'
        pending_file.rejected_reason = rejected_reason
        pending_file.confirmed_by = rejected_by  # 复用字段
        pending_file.confirmed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(pending_file)
        
        logger.info(
            f"Rejected pending file - id={file_id}, "
            f"reason={rejected_reason}, "
            f"rejected_by={rejected_by}"
        )
        
        return pending_file
    
    def mark_as_processed(
        self,
        file_id: int,
        raw_document_id: Optional[int] = None,
        file_index_id: Optional[int] = None,
        error: Optional[str] = None
    ) -> PendingFile:
        """
        标记文件已处理
        
        Args:
            file_id: 文件ID
            raw_document_id: 关联的raw_document ID
            file_index_id: 关联的file_index ID
            error: 处理错误信息
        """
        pending_file = self.get_pending_file(file_id)
        if not pending_file:
            raise ValueError(f"Pending file not found: {file_id}")
        
        pending_file.is_processed = True
        pending_file.processed_at = datetime.now()
        pending_file.raw_document_id = raw_document_id
        pending_file.file_index_id = file_index_id
        pending_file.processing_error = error
        
        self.db.commit()
        self.db.refresh(pending_file)
        
        logger.info(f"Marked pending file as processed - id={file_id}")
        
        return pending_file
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        stats = self.db.query(
            PendingFile.verification_status,
            func.count(PendingFile.id).label('count')
        ).filter(
            PendingFile.is_processed == False
        ).group_by(
            PendingFile.verification_status
        ).all()
        
        result = {
            'total': 0,
            'pending': 0,
            'matched': 0,
            'mismatch': 0,
            'confirmed': 0,
            'rejected': 0
        }
        
        for status, count in stats:
            result[status] = count
            result['total'] += count
        
        return result
    
    def search_customers(
        self,
        extracted_info: Dict[str, Any],
        limit: int = 5
    ) -> List[CustomerMatchInfo]:
        """
        搜索可能匹配的客户
        
        返回Top N个最可能的匹配客户
        """
        customer_name = extracted_info.get('customer_name')
        ic_number = extracted_info.get('ic_number')
        
        candidates = []
        
        # 搜索所有用户
        query = self.db.query(User)
        
        if ic_number:
            # IC号匹配
            ic_match = query.filter(User.ic_number == ic_number).first()
            if ic_match:
                candidates.append({
                    'user': ic_match,
                    'score': 100,
                    'reasons': ['IC号完全匹配']
                })
        
        if customer_name:
            # 姓名完全匹配
            name_exact = query.filter(
                func.lower(User.name) == func.lower(customer_name)
            ).first()
            if name_exact and name_exact not in [c['user'] for c in candidates]:
                candidates.append({
                    'user': name_exact,
                    'score': 90,
                    'reasons': ['姓名完全匹配']
                })
            
            # 姓名模糊匹配
            name_parts = customer_name.upper().split()
            for part in name_parts:
                if len(part) >= 3:
                    fuzzy_matches = query.filter(
                        User.name.ilike(f'%{part}%')
                    ).limit(3).all()
                    
                    for user in fuzzy_matches:
                        if user not in [c['user'] for c in candidates]:
                            candidates.append({
                                'user': user,
                                'score': 70,
                                'reasons': [f'姓名包含: {part}']
                            })
        
        # 排序并限制数量
        candidates.sort(key=lambda x: x['score'], reverse=True)
        candidates = candidates[:limit]
        
        # 转换为CustomerMatchInfo
        result = []
        for candidate in candidates:
            user = candidate['user']
            result.append(CustomerMatchInfo(
                customer_id=user.id,
                customer_name=user.name,
                ic_number=user.ic_number,
                email=user.email,
                match_score=candidate['score'],
                match_reasons=candidate['reasons']
            ))
        
        return result
