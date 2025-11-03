"""
配置版本锁 / Configuration Version Control

功能：
1. 追踪解析规则变更
2. 配置变更需要Architect审查
3. 防止未经审查的配置进入生产环境

Phase 1-8: System Config Versioning
"""

from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session
import json
import hashlib

from .models import SystemConfigVersion, AutoPostingRule, Company
from .db import get_db_session


class ConfigVersionManager:
    """配置版本管理器"""
    
    CONFIG_TYPES = {
        'posting_rule': '过账规则',
        'parsing_template': '解析模板',
        'validation_rule': '验证规则',
        'system_setting': '系统设置'
    }
    
    APPROVAL_STATUS = {
        'pending': {'zh': '待审查', 'en': 'Pending Review', 'color': 'warning'},
        'approved': {'zh': '已批准', 'en': 'Approved', 'color': 'success'},
        'rejected': {'zh': '已拒绝', 'en': 'Rejected', 'color': 'danger'},
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
    
    def create_version(
        self,
        config_type: str,
        config_data: Dict,
        created_by: str,
        change_summary: str,
        company_id: Optional[int] = None,
        reference_id: Optional[int] = None
    ) -> SystemConfigVersion:
        """
        创建配置版本
        
        Args:
            config_type: 配置类型
            config_data: 配置数据（JSON）
            created_by: 创建人
            change_summary: 变更摘要
            company_id: 公司ID（全局配置为None）
            reference_id: 引用ID（如AutoPostingRule的ID）
        
        Returns:
            SystemConfigVersion对象
        """
        config_json = json.dumps(config_data, ensure_ascii=False, sort_keys=True)
        config_hash = hashlib.sha256(config_json.encode('utf-8')).hexdigest()
        
        stmt = select(SystemConfigVersion).where(
            and_(
                SystemConfigVersion.config_type == config_type,
                SystemConfigVersion.company_id == company_id if company_id else SystemConfigVersion.company_id.is_(None)
            )
        ).order_by(desc(SystemConfigVersion.version_number))
        
        result = self.db.execute(stmt)
        latest_version = result.scalar_one_or_none()
        
        version_number = 1
        if latest_version:
            version_number = latest_version.version_number + 1
            
            if latest_version.config_hash == config_hash:
                raise ValueError("配置内容未发生变化 / Configuration unchanged")
        
        version = SystemConfigVersion(
            company_id=company_id,
            config_type=config_type,
            version_number=version_number,
            config_data=config_json,
            config_hash=config_hash,
            change_summary=change_summary,
            created_by=created_by,
            approval_status='pending',
            is_production=False,
            reference_id=reference_id
        )
        
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        
        return version
    
    def approve_version(
        self,
        version_id: int,
        approved_by: str,
        approval_notes: Optional[str] = None,
        promote_to_production: bool = False
    ) -> SystemConfigVersion:
        """
        批准配置版本
        
        Args:
            version_id: 版本ID
            approved_by: 审批人
            approval_notes: 审批备注
            promote_to_production: 是否推广到生产环境
        """
        stmt = select(SystemConfigVersion).where(SystemConfigVersion.id == version_id)
        result = self.db.execute(stmt)
        version = result.scalar_one_or_none()
        
        if not version:
            raise ValueError(f"版本 {version_id} 不存在 / Version not found")
        
        if version.approval_status == 'approved':
            raise ValueError("版本已被批准 / Version already approved")
        
        version.approval_status = 'approved'
        version.approved_by = approved_by
        version.approved_at = datetime.now()
        version.approval_notes = approval_notes
        
        if promote_to_production:
            stmt = select(SystemConfigVersion).where(
                and_(
                    SystemConfigVersion.config_type == version.config_type,
                    SystemConfigVersion.company_id == version.company_id if version.company_id else SystemConfigVersion.company_id.is_(None),
                    SystemConfigVersion.is_production == True
                )
            )
            result = self.db.execute(stmt)
            current_production = result.scalars().all()
            
            for prod_version in current_production:
                prod_version.is_production = False
                prod_version.activated_at = None
            
            version.is_production = True
            version.activated_at = datetime.now()
            version.activated_by = approved_by
        
        self.db.commit()
        self.db.refresh(version)
        
        return version
    
    def reject_version(
        self,
        version_id: int,
        rejected_by: str,
        rejection_reason: str
    ) -> SystemConfigVersion:
        """拒绝配置版本"""
        if not rejection_reason:
            raise ValueError("拒绝原因必填 / Rejection reason required")
        
        stmt = select(SystemConfigVersion).where(SystemConfigVersion.id == version_id)
        result = self.db.execute(stmt)
        version = result.scalar_one_or_none()
        
        if not version:
            raise ValueError(f"版本 {version_id} 不存在 / Version not found")
        
        version.approval_status = 'rejected'
        version.approved_by = rejected_by
        version.approved_at = datetime.now()
        version.approval_notes = f"拒绝原因: {rejection_reason}"
        
        self.db.commit()
        self.db.refresh(version)
        
        return version
    
    def get_production_version(
        self,
        config_type: str,
        company_id: Optional[int] = None
    ) -> Optional[SystemConfigVersion]:
        """获取生产环境配置"""
        stmt = select(SystemConfigVersion).where(
            and_(
                SystemConfigVersion.config_type == config_type,
                SystemConfigVersion.company_id == company_id if company_id else SystemConfigVersion.company_id.is_(None),
                SystemConfigVersion.is_production == True
            )
        )
        
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_all_versions(
        self,
        config_type: Optional[str] = None,
        company_id: Optional[int] = None,
        approval_status: Optional[str] = None,
        is_production: Optional[bool] = None
    ) -> List[Dict]:
        """获取所有版本"""
        conditions = []
        
        if config_type:
            conditions.append(SystemConfigVersion.config_type == config_type)
        
        if company_id is not None:
            conditions.append(SystemConfigVersion.company_id == company_id)
        
        if approval_status:
            conditions.append(SystemConfigVersion.approval_status == approval_status)
        
        if is_production is not None:
            conditions.append(SystemConfigVersion.is_production == is_production)
        
        stmt = select(SystemConfigVersion)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(
            desc(SystemConfigVersion.created_at)
        )
        
        result = self.db.execute(stmt)
        versions = result.scalars().all()
        
        return [self._format_version(v) for v in versions]
    
    def _format_version(self, version: SystemConfigVersion) -> Dict:
        """格式化版本数据"""
        approval_info = self.APPROVAL_STATUS.get(version.approval_status, {
            'zh': version.approval_status,
            'en': version.approval_status,
            'color': 'secondary'
        })
        
        config_data = {}
        if version.config_data:
            try:
                config_data = json.loads(version.config_data)
            except:
                config_data = {}
        
        return {
            'id': version.id,
            'company_id': version.company_id,
            'config_type': version.config_type,
            'config_type_display': self.CONFIG_TYPES.get(version.config_type, version.config_type),
            'version_number': version.version_number,
            'config_data': config_data,
            'config_hash': version.config_hash,
            'change_summary': version.change_summary,
            'approval_status': version.approval_status,
            'approval_status_display': approval_info,
            'is_production': version.is_production,
            'created_by': version.created_by,
            'created_at': version.created_at.isoformat(),
            'approved_by': version.approved_by,
            'approved_at': version.approved_at.isoformat() if version.approved_at else None,
            'approval_notes': version.approval_notes,
            'activated_by': version.activated_by,
            'activated_at': version.activated_at.isoformat() if version.activated_at else None,
            'reference_id': version.reference_id
        }
    
    def compare_versions(
        self,
        version_id_1: int,
        version_id_2: int
    ) -> Dict:
        """对比两个版本"""
        stmt = select(SystemConfigVersion).where(
            SystemConfigVersion.id.in_([version_id_1, version_id_2])
        )
        result = self.db.execute(stmt)
        versions = result.scalars().all()
        
        if len(versions) != 2:
            raise ValueError("无法找到指定的版本 / Versions not found")
        
        v1 = versions[0] if versions[0].id == version_id_1 else versions[1]
        v2 = versions[1] if versions[1].id == version_id_2 else versions[0]
        
        data1 = json.loads(v1.config_data)
        data2 = json.loads(v2.config_data)
        
        differences = self._find_differences(data1, data2)
        
        return {
            'version_1': self._format_version(v1),
            'version_2': self._format_version(v2),
            'differences': differences,
            'is_identical': v1.config_hash == v2.config_hash
        }
    
    def _find_differences(self, data1: Dict, data2: Dict, path: str = "") -> List[Dict]:
        """递归查找差异"""
        differences = []
        
        all_keys = set(data1.keys()) | set(data2.keys())
        
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            
            if key not in data1:
                differences.append({
                    'path': current_path,
                    'type': 'added',
                    'old_value': None,
                    'new_value': data2[key]
                })
            elif key not in data2:
                differences.append({
                    'path': current_path,
                    'type': 'removed',
                    'old_value': data1[key],
                    'new_value': None
                })
            elif data1[key] != data2[key]:
                if isinstance(data1[key], dict) and isinstance(data2[key], dict):
                    differences.extend(self._find_differences(data1[key], data2[key], current_path))
                else:
                    differences.append({
                        'path': current_path,
                        'type': 'modified',
                        'old_value': data1[key],
                        'new_value': data2[key]
                    })
        
        return differences
    
    def rollback_to_version(
        self,
        version_id: int,
        rollback_by: str,
        rollback_reason: str
    ) -> SystemConfigVersion:
        """回滚到指定版本"""
        if not rollback_reason:
            raise ValueError("回滚原因必填 / Rollback reason required")
        
        stmt = select(SystemConfigVersion).where(SystemConfigVersion.id == version_id)
        result = self.db.execute(stmt)
        target_version = result.scalar_one_or_none()
        
        if not target_version:
            raise ValueError(f"版本 {version_id} 不存在 / Version not found")
        
        if target_version.approval_status != 'approved':
            raise ValueError("只能回滚到已批准的版本 / Can only rollback to approved version")
        
        stmt = select(SystemConfigVersion).where(
            and_(
                SystemConfigVersion.config_type == target_version.config_type,
                SystemConfigVersion.company_id == target_version.company_id if target_version.company_id else SystemConfigVersion.company_id.is_(None),
                SystemConfigVersion.is_production == True
            )
        )
        result = self.db.execute(stmt)
        current_production = result.scalars().all()
        
        for prod_version in current_production:
            prod_version.is_production = False
            prod_version.activated_at = None
        
        target_version.is_production = True
        target_version.activated_at = datetime.now()
        target_version.activated_by = rollback_by
        target_version.approval_notes = f"{target_version.approval_notes or ''}\n回滚原因: {rollback_reason}"
        
        self.db.commit()
        self.db.refresh(target_version)
        
        return target_version
    
    def get_pending_approvals(
        self,
        company_id: Optional[int] = None
    ) -> List[Dict]:
        """获取待审批配置"""
        conditions = [SystemConfigVersion.approval_status == 'pending']
        
        if company_id is not None:
            conditions.append(SystemConfigVersion.company_id == company_id)
        
        stmt = select(SystemConfigVersion).where(and_(*conditions)).order_by(
            desc(SystemConfigVersion.created_at)
        )
        
        result = self.db.execute(stmt)
        versions = result.scalars().all()
        
        return [self._format_version(v) for v in versions]


def require_config_approval(config_type: str, config_data: Dict, created_by: str, change_summary: str, company_id: Optional[int] = None) -> SystemConfigVersion:
    """
    装饰器辅助函数：要求配置审批
    
    使用示例：
    version = require_config_approval('posting_rule', rule_data, 'admin@example.com', '添加新的银行对账规则')
    """
    with ConfigVersionManager() as manager:
        return manager.create_version(
            config_type=config_type,
            config_data=config_data,
            created_by=created_by,
            change_summary=change_summary,
            company_id=company_id
        )
