"""
报表版本化系统 / Report Versioning System

功能：
1. 自动生成报表快照（防篡改）
2. 版本对比功能
3. 历史追溯查询

Phase 1-4: 报表重跑版本追溯
"""

from datetime import datetime, date
from typing import Optional, Dict, List, Tuple
import json
import hashlib
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session

from .models import (
    ReportSnapshot, PeriodClosing, Company, BankStatement,
    PurchaseInvoice, SalesInvoice, JournalEntry
)
from .db import get_db_session


class ReportVersionManager:
    """报表版本管理器"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or next(get_db_session())
        self._should_close = db is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close and self.db:
            self.db.close()
    
    def generate_snapshot(
        self,
        company_id: int,
        report_type: str,
        period_start: date,
        period_end: date,
        report_data: Dict,
        generated_by: str,
        description: Optional[str] = None
    ) -> ReportSnapshot:
        """
        生成报表快照
        
        Args:
            company_id: 公司ID
            report_type: 报表类型 (balance_sheet, income_statement, cash_flow, etc.)
            period_start: 期间开始日期
            period_end: 期间结束日期
            report_data: 报表数据（JSON格式）
            generated_by: 生成人
            description: 描述
        
        Returns:
            ReportSnapshot对象
        """
        snapshot_data = json.dumps(report_data, ensure_ascii=False, sort_keys=True)
        data_hash = hashlib.sha256(snapshot_data.encode('utf-8')).hexdigest()
        
        stmt = select(ReportSnapshot).where(
            and_(
                ReportSnapshot.company_id == company_id,
                ReportSnapshot.report_type == report_type,
                ReportSnapshot.period_start == period_start,
                ReportSnapshot.period_end == period_end
            )
        ).order_by(desc(ReportSnapshot.version_number))
        
        result = self.db.execute(stmt)
        latest_snapshot = result.scalar_one_or_none()
        
        version_number = 1
        if latest_snapshot:
            version_number = latest_snapshot.version_number + 1
        
        snapshot = ReportSnapshot(
            company_id=company_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            version_number=version_number,
            snapshot_data=snapshot_data,
            data_hash=data_hash,
            generated_by=generated_by,
            description=description or f"自动生成版本 {version_number}"
        )
        
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        return snapshot
    
    def get_latest_snapshot(
        self,
        company_id: int,
        report_type: str,
        period_start: date,
        period_end: date
    ) -> Optional[ReportSnapshot]:
        """获取最新快照"""
        stmt = select(ReportSnapshot).where(
            and_(
                ReportSnapshot.company_id == company_id,
                ReportSnapshot.report_type == report_type,
                ReportSnapshot.period_start == period_start,
                ReportSnapshot.period_end == period_end
            )
        ).order_by(desc(ReportSnapshot.version_number)).limit(1)
        
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_all_versions(
        self,
        company_id: int,
        report_type: str,
        period_start: date,
        period_end: date
    ) -> List[ReportSnapshot]:
        """获取所有版本"""
        stmt = select(ReportSnapshot).where(
            and_(
                ReportSnapshot.company_id == company_id,
                ReportSnapshot.report_type == report_type,
                ReportSnapshot.period_start == period_start,
                ReportSnapshot.period_end == period_end
            )
        ).order_by(desc(ReportSnapshot.version_number))
        
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    def compare_versions(
        self,
        snapshot_id_1: int,
        snapshot_id_2: int
    ) -> Dict:
        """
        对比两个版本的差异
        
        Returns:
            {
                'version_1': {...},
                'version_2': {...},
                'differences': [...]
            }
        """
        stmt = select(ReportSnapshot).where(ReportSnapshot.id.in_([snapshot_id_1, snapshot_id_2]))
        result = self.db.execute(stmt)
        snapshots = result.scalars().all()
        
        if len(snapshots) != 2:
            raise ValueError("无法找到指定的快照版本")
        
        snap1 = snapshots[0] if snapshots[0].id == snapshot_id_1 else snapshots[1]
        snap2 = snapshots[1] if snapshots[1].id == snapshot_id_2 else snapshots[0]
        
        data1 = json.loads(snap1.snapshot_data)
        data2 = json.loads(snap2.snapshot_data)
        
        differences = self._find_differences(data1, data2)
        
        return {
            'version_1': {
                'id': snap1.id,
                'version_number': snap1.version_number,
                'generated_at': snap1.generated_at.isoformat(),
                'generated_by': snap1.generated_by,
                'data_hash': snap1.data_hash
            },
            'version_2': {
                'id': snap2.id,
                'version_number': snap2.version_number,
                'generated_at': snap2.generated_at.isoformat(),
                'generated_by': snap2.generated_by,
                'data_hash': snap2.data_hash
            },
            'differences': differences,
            'is_identical': snap1.data_hash == snap2.data_hash
        }
    
    def _find_differences(self, data1: Dict, data2: Dict, path: str = "") -> List[Dict]:
        """递归查找两个字典的差异"""
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


class PeriodLockManager:
    """期间锁定管理器 / Period Lock Manager"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or next(get_db_session())
        self._should_close = db is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close and self.db:
            self.db.close()
    
    def close_period(
        self,
        company_id: int,
        period_year: int,
        period_month: int,
        closed_by: str,
        closing_notes: Optional[str] = None
    ) -> PeriodClosing:
        """
        关闭期间（防止修改）
        
        Args:
            company_id: 公司ID
            period_year: 年份
            period_month: 月份
            closed_by: 关账人
            closing_notes: 关账备注
        
        Returns:
            PeriodClosing对象
        """
        stmt = select(PeriodClosing).where(
            and_(
                PeriodClosing.company_id == company_id,
                PeriodClosing.period_year == period_year,
                PeriodClosing.period_month == period_month
            )
        )
        result = self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing and existing.is_locked:
            raise ValueError(f"期间 {period_year}-{period_month:02d} 已被锁定 / Period already locked")
        
        stats = self._calculate_period_stats(company_id, period_year, period_month)
        
        if existing:
            existing.is_locked = True
            existing.locked_at = datetime.now()
            existing.locked_by = closed_by
            existing.closing_notes = closing_notes
            existing.total_transactions = stats['total_transactions']
            existing.total_debit = stats['total_debit']
            existing.total_credit = stats['total_credit']
            period_closing = existing
        else:
            period_closing = PeriodClosing(
                company_id=company_id,
                period_year=period_year,
                period_month=period_month,
                is_locked=True,
                locked_at=datetime.now(),
                locked_by=closed_by,
                closing_notes=closing_notes,
                total_transactions=stats['total_transactions'],
                total_debit=stats['total_debit'],
                total_credit=stats['total_credit']
            )
            self.db.add(period_closing)
        
        self.db.commit()
        self.db.refresh(period_closing)
        
        return period_closing
    
    def unlock_period(
        self,
        company_id: int,
        period_year: int,
        period_month: int,
        unlocked_by: str,
        unlock_reason: str
    ) -> PeriodClosing:
        """
        解锁期间（需要特殊权限）
        
        Args:
            company_id: 公司ID
            period_year: 年份
            period_month: 月份
            unlocked_by: 解锁人
            unlock_reason: 解锁原因（必填）
        
        Returns:
            PeriodClosing对象
        """
        if not unlock_reason:
            raise ValueError("解锁原因必填 / Unlock reason is required")
        
        stmt = select(PeriodClosing).where(
            and_(
                PeriodClosing.company_id == company_id,
                PeriodClosing.period_year == period_year,
                PeriodClosing.period_month == period_month
            )
        )
        result = self.db.execute(stmt)
        period_closing = result.scalar_one_or_none()
        
        if not period_closing or not period_closing.is_locked:
            raise ValueError(f"期间 {period_year}-{period_month:02d} 未被锁定 / Period is not locked")
        
        period_closing.is_locked = False
        period_closing.unlocked_at = datetime.now()
        period_closing.unlocked_by = unlocked_by
        period_closing.unlock_reason = unlock_reason
        
        self.db.commit()
        self.db.refresh(period_closing)
        
        return period_closing
    
    def is_period_locked(
        self,
        company_id: int,
        transaction_date: date
    ) -> Tuple[bool, Optional[str]]:
        """
        检查指定日期是否属于已锁定期间
        
        Returns:
            (is_locked, lock_message)
        """
        period_year = transaction_date.year
        period_month = transaction_date.month
        
        stmt = select(PeriodClosing).where(
            and_(
                PeriodClosing.company_id == company_id,
                PeriodClosing.period_year == period_year,
                PeriodClosing.period_month == period_month,
                PeriodClosing.is_locked == True
            )
        )
        result = self.db.execute(stmt)
        period_closing = result.scalar_one_or_none()
        
        if period_closing:
            msg = f"期间 {period_year}-{period_month:02d} 已关账，不允许修改 / Period {period_year}-{period_month:02d} is locked"
            return True, msg
        
        return False, None
    
    def _calculate_period_stats(
        self,
        company_id: int,
        period_year: int,
        period_month: int
    ) -> Dict:
        """计算期间统计数据"""
        from calendar import monthrange
        from decimal import Decimal
        
        _, last_day = monthrange(period_year, period_month)
        period_start = date(period_year, period_month, 1)
        period_end = date(period_year, period_month, last_day)
        
        stmt = select(JournalEntry).where(
            and_(
                JournalEntry.company_id == company_id,
                JournalEntry.entry_date >= period_start,
                JournalEntry.entry_date <= period_end
            )
        )
        result = self.db.execute(stmt)
        entries = result.scalars().all()
        
        total_transactions = len(entries)
        total_debit = Decimal('0')
        total_credit = Decimal('0')
        
        for entry in entries:
            if entry.total_debit:
                total_debit += entry.total_debit
            if entry.total_credit:
                total_credit += entry.total_credit
        
        return {
            'total_transactions': total_transactions,
            'total_debit': float(total_debit),
            'total_credit': float(total_credit)
        }
    
    def get_locked_periods(self, company_id: int) -> List[PeriodClosing]:
        """获取所有已锁定期间"""
        stmt = select(PeriodClosing).where(
            and_(
                PeriodClosing.company_id == company_id,
                PeriodClosing.is_locked == True
            )
        ).order_by(
            desc(PeriodClosing.period_year),
            desc(PeriodClosing.period_month)
        )
        
        result = self.db.execute(stmt)
        return result.scalars().all()


def enforce_period_lock(company_id: int, transaction_date: date) -> None:
    """
    强制执行期间锁定检查（装饰器辅助函数）
    
    Raises:
        ValueError: 如果期间已锁定
    """
    with PeriodLockManager() as manager:
        is_locked, message = manager.is_period_locked(company_id, transaction_date)
        if is_locked:
            raise ValueError(message)
