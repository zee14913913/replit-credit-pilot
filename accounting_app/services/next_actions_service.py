"""
Next Actions Service
计算文件当前状态下的下一步可执行动作
实现"状态→动作"引导系统
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import FileIndex


class NextActionsService:
    """
    下一步动作计算服务
    根据文件状态、验证状态、重复情况等，返回用户可执行的动作列表
    """
    
    @staticmethod
    def get_next_actions(
        file_record: FileIndex,
        db: Session
    ) -> List[Dict]:
        """
        计算单个文件的下一步动作列表
        
        Args:
            file_record: 文件记录
            db: 数据库会话
        
        Returns:
            动作列表，每个动作包含：
            - code: 动作代码
            - label: 显示文案
            - endpoint: API端点
            - method: HTTP方法
            - priority: 优先级 (1-5, 1最高)
            - icon: 图标
        """
        actions = []
        
        # 检测同月多份对账单
        has_duplicates = False
        if file_record.module == 'bank' and file_record.period and file_record.account_number:
            duplicate_count = db.query(FileIndex).filter(
                and_(
                    FileIndex.company_id == file_record.company_id,
                    FileIndex.module == 'bank',
                    FileIndex.period == file_record.period,
                    FileIndex.account_number == file_record.account_number,
                    FileIndex.status.in_(['uploaded', 'active', 'validated']),
                    FileIndex.is_active == True,
                    FileIndex.id != file_record.id  # 排除当前文件
                )
            ).count()
            has_duplicates = duplicate_count > 0
        
        # 根据状态返回相应动作
        status = file_record.status
        validation_status = file_record.validation_status
        
        # ========== uploaded / active 状态 ==========
        if status in ['uploaded', 'active']:
            # 如果存在重复，优先处理
            if has_duplicates:
                actions.append({
                    "code": "set_primary",
                    "label": "⚠️ 设为本月主对账单（本月有多份）",
                    "endpoint": f"/files/{file_record.id}/set-primary",
                    "method": "POST",
                    "priority": 1,
                    "icon": "⚠️",
                    "description": "本月存在多份对账单，请选择要使用的主对账单"
                })
                actions.append({
                    "code": "merge_duplicates",
                    "label": "🔀 合并同月对账单",
                    "endpoint": f"/files/{file_record.id}/merge-duplicates",
                    "method": "POST",
                    "priority": 2,
                    "icon": "🔀",
                    "description": "将同月的多份对账单合并成一份"
                })
            
            # 主要动作：验证数据
            actions.append({
                "code": "validate_statement",
                "label": "👉 验证数据（行数/客户/供应商）",
                "endpoint": f"/files/{file_record.id}/validate",
                "method": "POST",
                "priority": 1 if not has_duplicates else 3,
                "icon": "✅",
                "description": "验证文件数据的完整性和准确性"
            })
            
            # 次要动作：查看异常
            actions.append({
                "code": "view_exceptions",
                "label": "🔍 查看异常中心",
                "endpoint": f"/api/exceptions?source=bank_statement&file_id={file_record.id}",
                "method": "GET",
                "priority": 4,
                "icon": "🔍",
                "description": "查看数据验证中发现的异常"
            })
        
        # ========== validated 状态 ==========
        elif status == 'validated':
            # 主要动作：生成会计分录
            actions.append({
                "code": "generate_entries",
                "label": "👉 生成会计分录",
                "endpoint": f"/files/{file_record.id}/generate-entries",
                "method": "POST",
                "priority": 1,
                "icon": "📝",
                "description": "根据对账单生成会计分录并入账"
            })
            
            # 次要动作：查看明细
            actions.append({
                "code": "view_details",
                "label": "📊 查看明细数据",
                "endpoint": f"/files/{file_record.id}/details",
                "method": "GET",
                "priority": 3,
                "icon": "📊",
                "description": "查看已验证的交易明细"
            })
        
        # ========== posted 状态 ==========
        elif status == 'posted':
            # 主要动作：查看报表
            actions.append({
                "code": "view_report",
                "label": "✅ 查看财务报表",
                "endpoint": f"/api/reports/pnl?month={file_record.period}",
                "method": "GET",
                "priority": 1,
                "icon": "📈",
                "description": "查看本月的损益表和财务报表"
            })
            
            actions.append({
                "code": "view_journal_entries",
                "label": "📒 查看会计分录",
                "endpoint": f"/api/journal-entries?file_id={file_record.id}",
                "method": "GET",
                "priority": 2,
                "icon": "📒",
                "description": "查看由此对账单生成的会计分录"
            })
            
            # 次要动作：归档
            actions.append({
                "code": "archive",
                "label": "📦 归档文件",
                "endpoint": f"/files/{file_record.id}/archive",
                "method": "POST",
                "priority": 4,
                "icon": "📦",
                "description": "将文件标记为已归档（只读）"
            })
        
        # ========== exception 状态 ==========
        elif status == 'exception':
            # 主要动作：处理异常
            actions.append({
                "code": "fix_exceptions",
                "label": "⚠️ 去异常中心处理",
                "endpoint": f"/api/exceptions?file_id={file_record.id}",
                "method": "GET",
                "priority": 1,
                "icon": "⚠️",
                "description": "查看并修复数据异常"
            })
            
            # 次要动作：重新验证
            actions.append({
                "code": "revalidate",
                "label": "🔄 重新验证",
                "endpoint": f"/files/{file_record.id}/validate",
                "method": "POST",
                "priority": 2,
                "icon": "🔄",
                "description": "修复异常后重新验证数据"
            })
        
        # ========== processing 状态 ==========
        elif status == 'processing':
            actions.append({
                "code": "view_progress",
                "label": "⏳ 查看处理进度",
                "endpoint": f"/files/{file_record.id}/progress",
                "method": "GET",
                "priority": 1,
                "icon": "⏳",
                "description": "查看文件处理进度"
            })
        
        # ========== failed 状态 ==========
        elif status == 'failed':
            actions.append({
                "code": "view_error",
                "label": "❌ 查看错误详情",
                "endpoint": f"/files/{file_record.id}/error-log",
                "method": "GET",
                "priority": 1,
                "icon": "❌",
                "description": "查看处理失败的原因"
            })
            
            actions.append({
                "code": "retry",
                "label": "🔄 重试处理",
                "endpoint": f"/files/{file_record.id}/retry",
                "method": "POST",
                "priority": 2,
                "icon": "🔄",
                "description": "重新尝试处理文件"
            })
        
        # ========== archived 状态 ==========
        elif status == 'archived':
            actions.append({
                "code": "restore",
                "label": "↩️ 恢复到Active",
                "endpoint": f"/files/{file_record.id}/restore",
                "method": "POST",
                "priority": 1,
                "icon": "↩️",
                "description": "将归档文件恢复为活动状态"
            })
        
        # 按优先级排序
        actions.sort(key=lambda x: x['priority'])
        
        return actions
    
    @staticmethod
    def get_status_reason(file_record: FileIndex, db: Session) -> str:
        """
        生成状态说明：解释"为什么还是这个状态"
        
        Args:
            file_record: 文件记录
            db: 数据库会话
        
        Returns:
            状态说明文案
        """
        status = file_record.status
        validation_status = file_record.validation_status
        
        # 检测重复上传
        has_duplicates = False
        if file_record.module == 'bank' and file_record.period and file_record.account_number:
            duplicate_count = db.query(FileIndex).filter(
                and_(
                    FileIndex.company_id == file_record.company_id,
                    FileIndex.module == 'bank',
                    FileIndex.period == file_record.period,
                    FileIndex.account_number == file_record.account_number,
                    FileIndex.status.in_(['uploaded', 'active', 'validated']),
                    FileIndex.is_active == True,
                    FileIndex.id != file_record.id
                )
            ).count()
            has_duplicates = duplicate_count > 0
        
        # 根据状态返回说明
        if status in ['uploaded', 'active']:
            if has_duplicates:
                return f"⚠️ 重复上传：本月已有其他对账单，请选择主对账单"
            elif validation_status == 'pending':
                return "未验证：还没做数据验证"
            elif validation_status == 'failed':
                return "验证失败：存在数据异常，请先处理"
            else:
                return "等待入账：数据已验证，等待生成会计分录"
        
        elif status == 'validated':
            return "未入账：数据已验证，等待生成会计分录"
        
        elif status == 'posted':
            return "✅ 已完成：会计分录已生成并入账"
        
        elif status == 'exception':
            return "⚠️ 有异常：请到异常中心处理数据问题"
        
        elif status == 'processing':
            return "⏳ 处理中：系统正在处理文件"
        
        elif status == 'failed':
            return "❌ 处理失败：请查看错误日志"
        
        elif status == 'archived':
            return "📦 已归档：文件为只读状态"
        
        return "未知状态"
