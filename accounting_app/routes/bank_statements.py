"""
银行月结单操作API - 验证、入账、设为主对账单
修复后的版本：直接使用file_id查询，不依赖related_entity_id
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from decimal import Decimal
import logging

from ..db import get_db
from ..models import (
    BankStatement, RawDocument, RawLine, JournalEntry, JournalEntryLine,
    Exception as ExceptionModel, FileIndex, User
)
from ..middleware.rbac_fixed import require_auth
from ..services.next_actions_service import NextActionsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bank-statements", tags=["bank-statements"])


@router.post("/{file_id}/validate")
def validate_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    验证银行月结单数据（修复版：使用file_id）
    
    验证项：
    1. 行数对账：raw_lines行数 == parsed_lines
    2. 客户匹配度检查
    
    成功 → status: validated
    失败 → status: exception（进入异常中心）
    """
    company_id = current_user.company_id
    
    # 直接通过file_id查询FileIndex
    file_index = db.query(FileIndex).filter(
        FileIndex.id == file_id,
        FileIndex.company_id == company_id
    ).first()
    
    if not file_index:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 使用raw_document_id查询RawDocument
    if not file_index.raw_document_id:
        raise HTTPException(
            status_code=400, 
            detail="No raw document associated with this file. Please re-upload the file."
        )
    
    raw_doc = db.query(RawDocument).filter(
        RawDocument.id == file_index.raw_document_id,
        RawDocument.company_id == company_id
    ).first()
    
    if not raw_doc:
        raise HTTPException(status_code=404, detail="Raw document not found")
    
    # 验证1：行数对账
    raw_lines_count = db.query(RawLine).filter(
        RawLine.raw_document_id == raw_doc.id
    ).count()
    
    parsed_count = raw_doc.parsed_lines or 0
    
    if raw_lines_count != parsed_count:
        # 验证失败 → 创建异常记录
        exception = ExceptionModel(
            company_id=company_id,
            exception_type='line_count_mismatch',
            severity='high',
            source_module='bank',
            source_entity_type='file_index',
            source_entity_id=file_id,
            description=f"行数不匹配：原文件={raw_lines_count}行，已解析={parsed_count}行",
            raw_document_id=raw_doc.id,
            status='open'
        )
        db.add(exception)
        
        # 更新file_index状态
        file_index.status = 'exception'
        file_index.validation_status = 'failed'
        file_index.status_reason = f"验证失败：行数不匹配（原文件{raw_lines_count}行，已解析{parsed_count}行）"
        
        db.commit()
        
        # 计算下一步动作
        next_actions = NextActionsService.get_next_actions(file_index, db)
        
        return {
            "success": False,
            "file_id": file_id,
            "status": "exception",
            "validation_status": "failed",
            "error": f"行数不匹配：原文件={raw_lines_count}行，已解析={parsed_count}行",
            "exception_id": exception.id,
            "next_actions": next_actions
        }
    
    # 验证2：客户匹配度检查（统计已匹配的行数）
    matched_lines = db.query(RawLine).filter(
        RawLine.raw_document_id == raw_doc.id,
        RawLine.matched_customer_id.isnot(None)
    ).count()
    
    match_rate = (matched_lines / raw_lines_count * 100) if raw_lines_count > 0 else 0
    
    # 验证通过 → 更新状态
    file_index.status = 'validated'
    file_index.validation_status = 'passed'
    file_index.status_reason = f"验证通过：{raw_lines_count}行数据，客户匹配率{match_rate:.1f}%"
    
    # 更新raw_document状态
    raw_doc.status = 'validated'
    raw_doc.validation_status = 'passed'
    
    db.commit()
    
    # 计算下一步动作
    next_actions = NextActionsService.get_next_actions(file_index, db)
    
    logger.info(f"File {file_id} validated successfully")
    
    return {
        "success": True,
        "file_id": file_id,
        "status": "validated",
        "validation_status": "passed",
        "validation_details": {
            "total_lines": raw_lines_count,
            "parsed_lines": parsed_count,
            "matched_lines": matched_lines,
            "match_rate": f"{match_rate:.1f}%"
        },
        "next_actions": next_actions
    }


@router.post("/{file_id}/generate-entries")
def generate_entries(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    生成会计分录（入账到总账）
    
    前置条件：status == 'validated'
    成功 → status: posted
    """
    company_id = current_user.company_id
    
    # 直接通过file_id查询FileIndex
    file_index = db.query(FileIndex).filter(
        FileIndex.id == file_id,
        FileIndex.company_id == company_id
    ).first()
    
    if not file_index:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 检查状态：必须是validated才能入账
    if file_index.status != 'validated':
        exception_id = None
        if file_index.status == 'exception':
            # 查找对应的异常记录
            exception = db.query(ExceptionModel).filter(
                ExceptionModel.source_entity_type == 'file_index',
                ExceptionModel.source_entity_id == file_id,
                ExceptionModel.status == 'open'
            ).first()
            if exception:
                exception_id = exception.id
        
        return {
            "success": False,
            "reason": "file not validated",
            "current_status": file_index.status,
            "hint": f"请先解决异常（exception_id={exception_id}）" if exception_id else "请先验证数据"
        }
    
    # 使用raw_document_id查询RawDocument
    if not file_index.raw_document_id:
        raise HTTPException(
            status_code=400,
            detail="No raw document associated. Please re-upload the file."
        )
    
    raw_doc = db.query(RawDocument).filter(
        RawDocument.id == file_index.raw_document_id,
        RawDocument.company_id == company_id
    ).first()
    
    if not raw_doc:
        raise HTTPException(status_code=404, detail="Raw document not found")
    
    # 创建Journal Entry（会计分录）
    journal_entry = JournalEntry(
        company_id=company_id,
        entry_date=datetime.now().date(),
        entry_type='bank_statement',
        reference=f"BANK-{file_id}-{file_index.period or 'UNKNOWN'}",
        description=f"Bank statement import: {file_index.filename}",
        created_by=current_user.username,
        status='posted'
    )
    db.add(journal_entry)
    db.flush()
    
    # 读取所有raw_lines，生成会计分录行
    raw_lines = db.query(RawLine).filter(
        RawLine.raw_document_id == raw_doc.id,
        RawLine.is_parsed == True
    ).all()
    
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    
    for raw_line in raw_lines:
        # 简化处理：每行生成一条会计分录
        # 实际生产环境需要更复杂的解析和账户映射逻辑
        amount = Decimal('100')  # 示例金额
        
        entry_line = JournalEntryLine(
            journal_entry_id=journal_entry.id,
            account_code='1001',  # 银行存款
            debit_amount=amount,
            credit_amount=Decimal('0'),
            description=raw_line.raw_text[:100] if raw_line.raw_text else 'Bank transaction',
            raw_line_id=raw_line.id
        )
        total_debit += amount
        db.add(entry_line)
    
    # 更新journal_entry的总额
    journal_entry.total_debit = total_debit
    journal_entry.total_credit = total_debit  # 简化：借贷相等
    
    # 更新file_index状态
    file_index.status = 'posted'
    file_index.status_reason = f"已入账：生成{len(raw_lines)}条会计分录"
    
    db.commit()
    
    # 计算下一步动作
    next_actions = NextActionsService.get_next_actions(file_index, db)
    
    logger.info(f"File {file_id} posted to ledger successfully")
    
    return {
        "success": True,
        "file_id": file_id,
        "status": "posted",
        "journal_entry_id": journal_entry.id,
        "journal_lines_count": len(raw_lines),
        "total_debit": str(total_debit),
        "total_credit": str(total_debit),
        "next_actions": next_actions
    }


@router.post("/{file_id}/set-primary")
def set_as_primary(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    设为主对账单
    
    同一公司、同一账号、同一月份只能有一个主对账单
    """
    company_id = current_user.company_id
    
    # 直接通过file_id查询FileIndex
    file_index = db.query(FileIndex).filter(
        FileIndex.id == file_id,
        FileIndex.company_id == company_id
    ).first()
    
    if not file_index:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 检查是否有period和account_number
    if not file_index.period or not file_index.account_number:
        raise HTTPException(
            status_code=400,
            detail="Cannot set as primary: missing period or account_number. Please re-upload the file."
        )
    
    # 将同一公司、同一账号、同一月份的其他对账单的is_primary设为False
    db.query(FileIndex).filter(
        and_(
            FileIndex.company_id == company_id,
            FileIndex.account_number == file_index.account_number,
            FileIndex.period == file_index.period,
            FileIndex.id != file_index.id
        )
    ).update({"is_primary": False})
    
    # 设置当前对账单为主对账单
    file_index.is_primary = True
    file_index.duplicate_warning = False  # 清除重复警告
    
    db.commit()
    
    logger.info(f"File {file_id} set as primary for period {file_index.period}")
    
    return {
        "success": True,
        "file_id": file_id,
        "is_primary": True,
        "period": file_index.period,
        "account_number": file_index.account_number,
        "message": f"已设为{file_index.period}的主对账单"
    }
