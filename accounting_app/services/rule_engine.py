"""
Rule Engine - 规则引擎服务
表驱动化的自动记账规则匹配和应用系统
"""
import re
import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from ..models import AutoPostingRule, ChartOfAccounts, BankStatement, JournalEntry, JournalEntryLine
from ..services.exception_manager import ExceptionManager

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    规则引擎 - 核心匹配逻辑
    
    职责：
    1. 根据交易描述匹配最合适的记账规则
    2. 验证规则中的会计科目是否存在
    3. 应用规则生成会计分录
    4. 统计规则匹配次数
    """
    
    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
        # 修复缓存bug：使用字典缓存，key为source_type
        self._rules_cache: dict[Optional[str], List[AutoPostingRule]] = {}
    
    def clear_cache(self, source_type: Optional[str] = None):
        """
        清除缓存
        
        Args:
            source_type: 指定source_type清除，None则清除全部缓存
        """
        if source_type is None:
            # 清除所有缓存
            self._rules_cache.clear()
            logger.debug(f"✅ 清除所有规则缓存 (Company: {self.company_id})")
        elif source_type in self._rules_cache:
            # 清除指定source_type的缓存
            del self._rules_cache[source_type]
            logger.debug(f"✅ 清除规则缓存: {source_type} (Company: {self.company_id})")
    
    def get_all_rules(self, source_type: Optional[str] = None, force_refresh: bool = False) -> List[AutoPostingRule]:
        """
        获取所有启用的规则（按优先级排序）
        
        Args:
            source_type: 过滤source_type (bank_import, supplier_invoice, sales_invoice)
            force_refresh: 强制刷新缓存
        
        Returns:
            规则列表（按priority升序）
        
        ⚠️ 修复：缓存现在基于source_type隔离，防止跨类型规则混淆
        """
        cache_key = source_type  # None也是合法的cache key
        
        if cache_key not in self._rules_cache or force_refresh:
            query = self.db.query(AutoPostingRule).filter(
                AutoPostingRule.company_id == self.company_id,
                AutoPostingRule.is_active == True
            )
            
            if source_type:
                query = query.filter(AutoPostingRule.source_type == source_type)
            
            # 按优先级排序（数字越小优先级越高）
            self._rules_cache[cache_key] = query.order_by(AutoPostingRule.priority.asc()).all()
        
        return self._rules_cache[cache_key]
    
    def match_transaction(self, description: str, source_type: str = "bank_import") -> Optional[AutoPostingRule]:
        """
        根据交易描述匹配规则
        
        Args:
            description: 交易描述
            source_type: 来源类型
        
        Returns:
            匹配的规则，如果没有匹配返回None
        """
        rules = self.get_all_rules(source_type=source_type)
        
        for rule in rules:
            if self._test_pattern(description, rule.pattern, rule.is_regex):
                logger.info(f"✅ 规则匹配成功: '{rule.rule_name}' (ID: {rule.id}) | 描述: {description[:50]}")
                return rule
        
        logger.warning(f"❌ 无匹配规则: {description[:50]}")
        return None
    
    def _test_pattern(self, text: str, pattern: str, is_regex: bool) -> bool:
        """
        测试模式是否匹配
        
        Args:
            text: 要测试的文本
            pattern: 匹配模式
            is_regex: 是否为正则表达式
        
        Returns:
            是否匹配
        """
        if is_regex:
            try:
                return bool(re.search(pattern, text, re.IGNORECASE))
            except re.error as e:
                logger.error(f"正则表达式错误: {pattern} | 错误: {str(e)}")
                return False
        else:
            # 关键字匹配（大小写不敏感）
            return pattern.lower() in text.lower()
    
    def validate_rule_accounts(self, rule: AutoPostingRule) -> Tuple[bool, Optional[str]]:
        """
        验证规则中的会计科目是否存在
        
        Returns:
            (是否有效, 错误消息)
        """
        # 检查借方科目
        debit_account = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.company_id == self.company_id,
            ChartOfAccounts.account_code == rule.debit_account_code,
            ChartOfAccounts.is_active == True
        ).first()
        
        if not debit_account:
            return False, f"借方科目不存在: {rule.debit_account_code}"
        
        # 检查贷方科目
        credit_account = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.company_id == self.company_id,
            ChartOfAccounts.account_code == rule.credit_account_code,
            ChartOfAccounts.is_active == True
        ).first()
        
        if not credit_account:
            return False, f"贷方科目不存在: {rule.credit_account_code}"
        
        return True, None
    
    def apply_rule_to_bank_statement(
        self,
        bank_stmt: BankStatement,
        rule: AutoPostingRule
    ) -> Optional[JournalEntry]:
        """
        将规则应用到银行交易，生成会计分录
        
        Args:
            bank_stmt: 银行交易记录
            rule: 匹配的规则
        
        Returns:
            生成的会计分录，失败返回None
        """
        # 验证会计科目
        is_valid, error_msg = self.validate_rule_accounts(rule)
        if not is_valid:
            logger.error(f"规则验证失败: {error_msg}")
            ExceptionManager.record_posting_error(
                db=self.db,
                company_id=self.company_id,
                error_message=f"规则'{rule.rule_name}': {error_msg}",
                source_type='bank_import',
                source_id=bank_stmt.id,
                context={'description': bank_stmt.description, 'rule_id': rule.id}
            )
            return None
        
        # 获取会计科目
        debit_account = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.company_id == self.company_id,
            ChartOfAccounts.account_code == rule.debit_account_code
        ).first()
        
        credit_account = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.company_id == self.company_id,
            ChartOfAccounts.account_code == rule.credit_account_code
        ).first()
        
        # 确定金额
        amount = bank_stmt.debit_amount if bank_stmt.debit_amount > 0 else bank_stmt.credit_amount
        
        # 生成分录号
        entry_number = f"JE-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{bank_stmt.id}"
        
        try:
            # 创建Journal Entry
            journal_entry = JournalEntry(
                company_id=self.company_id,
                entry_number=entry_number,
                entry_date=bank_stmt.transaction_date,
                description=f"[规则: {rule.rule_name}] {bank_stmt.description}",
                entry_type='bank_import',
                reference_number=bank_stmt.reference_number,
                status='posted'
            )
            self.db.add(journal_entry)
            self.db.flush()
            
            # 创建借方分录
            debit_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                account_id=debit_account.id,
                description=bank_stmt.description,
                debit_amount=amount,
                credit_amount=Decimal('0.00'),
                line_number=1
            )
            self.db.add(debit_line)
            
            # 创建贷方分录
            credit_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                account_id=credit_account.id,
                description=bank_stmt.description,
                debit_amount=Decimal('0.00'),
                credit_amount=amount,
                line_number=2
            )
            self.db.add(credit_line)
            
            # 更新bank_statement的matched状态
            bank_stmt.matched = True
            bank_stmt.matched_journal_id = journal_entry.id
            bank_stmt.auto_category = rule.rule_name
            
            # 更新规则统计
            self.update_match_stats(rule)
            
            self.db.flush()
            self.db.refresh(journal_entry)
            
            logger.info(f"✅ 分录生成成功: {entry_number} | 金额: {amount} | 规则: {rule.rule_name}")
            
            return journal_entry
            
        except Exception as e:
            logger.error(f"生成分录失败: {str(e)}")
            ExceptionManager.record_posting_error(
                db=self.db,
                company_id=self.company_id,
                error_message=f"应用规则'{rule.rule_name}'时失败: {str(e)}",
                source_type='bank_import',
                source_id=bank_stmt.id,
                context={'description': bank_stmt.description, 'rule_id': rule.id, 'error': str(e)}
            )
            return None
    
    def update_match_stats(self, rule: AutoPostingRule):
        """
        更新规则匹配统计
        
        Args:
            rule: 匹配的规则
        """
        rule.match_count += 1
        rule.last_matched_at = datetime.now()
        self.db.add(rule)
    
    def test_rule_pattern(self, pattern: str, is_regex: bool, test_text: str) -> Tuple[bool, Optional[str]]:
        """
        测试规则模式是否有效
        
        Returns:
            (是否匹配, 错误消息)
        """
        try:
            matched = self._test_pattern(test_text, pattern, is_regex)
            return matched, None
        except Exception as e:
            return False, str(e)
