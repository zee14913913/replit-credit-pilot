"""
银行交易自动匹配服务
根据描述关键词自动生成会计分录
"""
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

from ..models import BankStatement, JournalEntry, JournalEntryLine, ChartOfAccounts


# 关键词匹配规则（简化版）
MATCHING_RULES = {
    'salary': {'debit': 'salary_expense', 'credit': 'bank'},
    'gaji': {'debit': 'salary_expense', 'credit': 'bank'},
    'epf': {'debit': 'epf_expense', 'credit': 'bank'},
    'socso': {'debit': 'socso_expense', 'credit': 'bank'},
    'rental': {'debit': 'rental_expense', 'credit': 'bank'},
    'rent': {'debit': 'rental_expense', 'credit': 'bank'},
    'transfer': {'category': 'transfer'},  # 内部转账，不生成费用分录
    'deposit': {'debit': 'bank', 'credit': 'owner_capital'},
    'withdrawal': {'debit': 'owner_drawings', 'credit': 'bank'},
}


def auto_match_transactions(db: Session, company_id: int, statement_month: str) -> int:
    """
    自动匹配银行流水并生成会计分录
    
    返回：成功匹配的交易数量
    """
    # 获取未匹配的银行流水
    unmatched = db.query(BankStatement).filter(
        BankStatement.company_id == company_id,
        BankStatement.statement_month == statement_month,
        BankStatement.matched == False
    ).all()
    
    matched_count = 0
    
    for stmt in unmatched:
        description_lower = stmt.description.lower()
        
        # 尝试匹配关键词
        matched_rule = None
        for keyword, rule in MATCHING_RULES.items():
            if keyword in description_lower:
                matched_rule = rule
                stmt.auto_category = keyword
                break
        
        if not matched_rule:
            continue
        
        # 如果是transfer，不生成分录
        if matched_rule.get('category') == 'transfer':
            stmt.matched = True
            stmt.notes = "内部转账，无需会计分录"
            matched_count += 1
            continue
        
        # 生成会计分录
        try:
            create_journal_entry_from_rule(db, stmt, matched_rule)
            stmt.matched = True
            matched_count += 1
        except Exception as e:
            print(f"生成分录失败: {e}")
            continue
    
    db.commit()
    return matched_count


def create_journal_entry_from_rule(db: Session, bank_stmt: BankStatement, rule: dict):
    """
    根据规则创建会计分录
    """
    # 生成分录号
    entry_number = f"JE-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{bank_stmt.id}"
    
    # 创建Journal Entry
    journal_entry = JournalEntry(
        company_id=bank_stmt.company_id,
        entry_number=entry_number,
        entry_date=bank_stmt.transaction_date,
        description=f"Bank Import: {bank_stmt.description}",
        entry_type='bank_import',
        reference_number=bank_stmt.reference_number,
        status='posted'
    )
    db.add(journal_entry)
    db.flush()  # 获取ID
    
    # 获取会计科目（简化版，实际应从chart_of_accounts查询）
    # 这里假设已经有默认会计科目
    debit_account_code = rule.get('debit')
    credit_account_code = rule.get('credit')
    
    # 确定金额
    amount = bank_stmt.debit_amount if bank_stmt.debit_amount > 0 else bank_stmt.credit_amount
    
    # 创建借方分录
    debit_line = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=1,  # TODO: 从chart_of_accounts查询真实account_id
        description=bank_stmt.description,
        debit_amount=amount,
        credit_amount=0,
        line_number=1
    )
    db.add(debit_line)
    
    # 创建贷方分录
    credit_line = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=2,  # TODO: 从chart_of_accounts查询真实account_id
        description=bank_stmt.description,
        debit_amount=0,
        credit_amount=amount,
        line_number=2
    )
    db.add(credit_line)
    
    # 更新bank_statement的matched_journal_id
    bank_stmt.matched_journal_id = journal_entry.id
