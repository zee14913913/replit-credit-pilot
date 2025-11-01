"""
银行交易自动匹配服务
根据描述关键词自动生成会计分录

✨ 升级为Rule Engine驱动（表驱动化）
- 优先使用RuleEngine.match_transaction()从数据库匹配规则
- 保留MATCHING_RULES作为向后兼容fallback
"""
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
import logging

from ..models import BankStatement, JournalEntry, JournalEntryLine, ChartOfAccounts
from .rule_engine import RuleEngine
from .exception_manager import ExceptionManager

logger = logging.getLogger(__name__)


# 关键词匹配规则（与种子数据的account_code对应）
# 注意：顺序很重要！优先级高的规则应放在前面
MATCHING_RULES = {
    # 工资支付（优先级最高）
    'payout': {'debit': 'salary_expense', 'credit': 'bank'},
    'infinite.gz': {'debit': 'salary_expense', 'credit': 'bank'},
    'salary': {'debit': 'salary_expense', 'credit': 'bank'},
    'gaji': {'debit': 'salary_expense', 'credit': 'bank'},
    
    # 法定缴纳
    'kumpulan wang simpanan pekerja': {'debit': 'epf_payable', 'credit': 'bank'},
    'kwsp': {'debit': 'epf_payable', 'credit': 'bank'},
    'epf': {'debit': 'epf_payable', 'credit': 'bank'},
    'pertubuhan keselamatan sosial': {'debit': 'socso_payable', 'credit': 'bank'},
    'perkeso': {'debit': 'socso_payable', 'credit': 'bank'},
    'socso': {'debit': 'socso_payable', 'credit': 'bank'},
    
    # 支出类
    'rental': {'debit': 'rent_expense', 'credit': 'bank'},
    'rent': {'debit': 'rent_expense', 'credit': 'bank'},
    'utilities': {'debit': 'utilities_expense', 'credit': 'bank'},
    'util': {'debit': 'utilities_expense', 'credit': 'bank'},
    'supplier': {'debit': 'purchase_expense', 'credit': 'bank'},
    'payment': {'debit': 'purchase_expense', 'credit': 'bank'},
    'stock': {'debit': 'purchase_expense', 'credit': 'bank'},
    
    # 收入类
    'service': {'debit': 'bank', 'credit': 'service_income'},
    'deposit': {'debit': 'bank', 'credit': 'deposit_income'},
    
    # 其他
    'fee': {'debit': 'bank_charges', 'credit': 'bank'},
    'transfer': {'category': 'transfer'},  # 内部转账，优先级最低
}


def auto_match_transactions(db: Session, company_id: int, statement_month: str) -> int:
    """
    自动匹配银行流水并生成会计分录
    
    ✨ 升级说明：
    1. 优先使用RuleEngine从数据库匹配规则（表驱动）
    2. 如果数据库无匹配，fallback到硬编码MATCHING_RULES（向后兼容）
    3. 匹配失败记录Exception Center
    
    返回：成功匹配的交易数量
    """
    # 获取未匹配的银行流水
    unmatched = db.query(BankStatement).filter(
        BankStatement.company_id == company_id,
        BankStatement.statement_month == statement_month,
        BankStatement.matched == False
    ).all()
    
    matched_count = 0
    engine = RuleEngine(db, company_id)
    exception_mgr = ExceptionManager(db, company_id)
    
    for stmt in unmatched:
        description_lower = stmt.description.lower()
        
        # ✅ 优先使用Rule Engine匹配
        matched_rule_obj = engine.match_transaction(
            description=stmt.description,
            source_type='bank_import'
        )
        
        if matched_rule_obj:
            # ✅ 使用数据库规则生成分录
            logger.info(f"✅ RuleEngine匹配成功: {matched_rule_obj.rule_name} | 交易: {stmt.description[:50]}")
            try:
                # 使用RuleEngine生成会计分录
                journal_entry = engine.apply_rule_to_bank_statement(matched_rule_obj, stmt)
                stmt.matched = True
                stmt.matched_journal_id = journal_entry.id
                stmt.auto_category = matched_rule_obj.rule_name
                matched_count += 1
                
                # 更新规则匹配统计
                engine.update_match_stats(matched_rule_obj.id)
                
                logger.info(f"✅ 会计分录已生成: {journal_entry.entry_number}")
                continue
                
            except Exception as e:
                logger.error(f"❌ RuleEngine生成分录失败: {e}")
                exception_mgr.record_posting_error(
                    source_type='bank_import',
                    source_id=stmt.id,
                    error_message=str(e),
                    context={'description': stmt.description, 'rule_id': matched_rule_obj.id}
                )
                continue
        
        # ⚠️ Fallback：使用硬编码规则（向后兼容）
        matched_legacy_rule = None
        for keyword, rule in MATCHING_RULES.items():
            if keyword in description_lower:
                matched_legacy_rule = rule
                stmt.auto_category = keyword
                logger.warning(f"⚠️ 使用硬编码规则匹配: {keyword} | 交易: {stmt.description[:50]}")
                break
        
        if not matched_legacy_rule:
            # 完全无法匹配
            logger.debug(f"⏭️ 无匹配规则，跳过: {stmt.description[:50]}")
            continue
        
        # 如果是transfer，不生成分录
        if matched_legacy_rule.get('category') == 'transfer':
            stmt.matched = True
            stmt.notes = "内部转账，无需会计分录"
            matched_count += 1
            continue
        
        # 生成会计分录（使用旧方法）
        try:
            create_journal_entry_from_rule(db, stmt, matched_legacy_rule)
            stmt.matched = True
            matched_count += 1
            logger.info(f"✅ 使用legacy规则生成分录: {stmt.description[:50]}")
        except Exception as e:
            logger.error(f"❌ 生成分录失败: {e}")
            exception_mgr.record_posting_error(
                source_type='bank_import',
                source_id=stmt.id,
                error_message=str(e),
                context={'description': stmt.description, 'legacy_rule': matched_legacy_rule}
            )
            continue
    
    db.commit()
    logger.info(f"📊 自动匹配完成: {matched_count}/{len(unmatched)} 笔交易")
    return matched_count


def create_journal_entry_from_rule(db: Session, bank_stmt: BankStatement, rule: dict):
    """
    根据规则创建会计分录 - 使用真实的chart_of_accounts
    """
    # 获取会计科目account_code
    debit_account_code = rule.get('debit')
    credit_account_code = rule.get('credit')
    
    if not debit_account_code or not credit_account_code:
        raise ValueError(f"规则缺少借方或贷方科目: {rule}")
    
    # 从数据库查询真实的account_id
    debit_account = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.company_id == bank_stmt.company_id,
        ChartOfAccounts.account_code == debit_account_code,
        ChartOfAccounts.is_active == True
    ).first()
    
    credit_account = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.company_id == bank_stmt.company_id,
        ChartOfAccounts.account_code == credit_account_code,
        ChartOfAccounts.is_active == True
    ).first()
    
    if not debit_account or not credit_account:
        raise ValueError(
            f"会计科目不存在。需要: {debit_account_code}, {credit_account_code}。"
            f"找到: debit={debit_account}, credit={credit_account}"
        )
    
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
    
    # 确定金额
    amount = bank_stmt.debit_amount if bank_stmt.debit_amount > 0 else bank_stmt.credit_amount
    
    # 创建借方分录
    debit_line = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=debit_account.id,
        description=bank_stmt.description,
        debit_amount=amount,
        credit_amount=0,
        line_number=1
    )
    db.add(debit_line)
    
    # 创建贷方分录
    credit_line = JournalEntryLine(
        journal_entry_id=journal_entry.id,
        account_id=credit_account.id,
        description=bank_stmt.description,
        debit_amount=0,
        credit_amount=amount,
        line_number=2
    )
    db.add(credit_line)
    
    # 更新bank_statement的matched_journal_id
    bank_stmt.matched_journal_id = journal_entry.id
