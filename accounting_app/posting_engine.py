"""
自动过账规则引擎 / Auto Posting Rules Engine

功能：
1. 表驱动化规则匹配
2. 全局规则 + 公司级规则优先级
3. 智能会计分录生成

Phase 1-5: Rule Engine - 表驱动规则引擎替代硬编码
"""

from typing import Optional, List, Dict, Tuple
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from .models import (
    AutoPostingRule, JournalEntry, JournalEntryLine,
    ChartOfAccounts, BankStatement, PurchaseInvoice, SalesInvoice,
    RawLine
)
from .db import get_db_session
from .data_integrity import DataIntegrityValidator


class PostingRuleEngine:
    """自动过账规则引擎"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or next(get_db_session())
        self._should_close = db is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close and self.db:
            self.db.close()
    
    def find_matching_rule(
        self,
        company_id: int,
        source_type: str,
        transaction_type: str,
        keywords: Optional[List[str]] = None,
        amount: Optional[Decimal] = None
    ) -> Optional[AutoPostingRule]:
        """
        查找匹配的过账规则
        
        优先级：
        1. 公司级规则 > 全局规则
        2. 精确匹配 > 模糊匹配
        3. 启用的规则 > 禁用的规则
        
        Args:
            company_id: 公司ID
            source_type: 来源类型 (bank_statement, purchase_invoice, sales_invoice)
            transaction_type: 交易类型 (deposit, withdrawal, payment, receipt)
            keywords: 关键词列表（用于匹配描述）
            amount: 金额（可用于金额范围匹配）
        
        Returns:
            匹配的规则，如果没有则返回None
        """
        stmt = select(AutoPostingRule).where(
            and_(
                or_(
                    AutoPostingRule.company_id == company_id,
                    AutoPostingRule.company_id.is_(None)
                ),
                AutoPostingRule.source_type == source_type,
                AutoPostingRule.is_active == True
            )
        ).order_by(
            AutoPostingRule.company_id.desc().nullslast(),
            AutoPostingRule.priority.desc(),
            AutoPostingRule.created_at.desc()
        )
        
        result = self.db.execute(stmt)
        all_rules = result.scalars().all()
        
        for rule in all_rules:
            if self._rule_matches(rule, transaction_type, keywords, amount):
                return rule
        
        return None
    
    def _rule_matches(
        self,
        rule: AutoPostingRule,
        transaction_type: str,
        keywords: Optional[List[str]],
        amount: Optional[Decimal]
    ) -> bool:
        """检查规则是否匹配"""
        if rule.transaction_type and rule.transaction_type != transaction_type:
            return False
        
        if rule.match_keywords and keywords:
            rule_keywords = [kw.strip().lower() for kw in rule.match_keywords.split(',')]
            text_to_match = ' '.join(keywords).lower()
            
            if not any(kw in text_to_match for kw in rule_keywords):
                return False
        
        if amount is not None:
            if rule.min_amount is not None and amount < rule.min_amount:
                return False
            if rule.max_amount is not None and amount > rule.max_amount:
                return False
        
        return True
    
    def apply_rule_to_bank_statement(
        self,
        statement: BankStatement,
        rule: AutoPostingRule,
        created_by: str
    ) -> JournalEntry:
        """
        应用规则到银行对账单，生成会计分录
        
        Args:
            statement: 银行对账单
            rule: 过账规则
            created_by: 创建人
        
        Returns:
            生成的会计分录
        """
        is_debit = statement.debit_amount and statement.debit_amount > 0
        amount = statement.debit_amount if is_debit else statement.credit_amount
        
        if not amount or amount <= 0:
            raise ValueError("交易金额无效 / Invalid transaction amount")
        
        entry = JournalEntry(
            company_id=statement.company_id,
            entry_date=statement.transaction_date,
            entry_type='automatic',
            reference_number=f"BS-{statement.id}",
            description=statement.description or rule.description_template,
            total_debit=amount,
            total_credit=amount,
            source_type='bank_statement',
            source_id=statement.id,
            created_by=created_by,
            is_posted=False
        )
        
        self.db.add(entry)
        self.db.flush()
        
        if is_debit:
            debit_line = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=rule.debit_account_id,
                description=statement.description or rule.description_template,
                debit_amount=amount,
                credit_amount=Decimal('0'),
                line_number=1,
                raw_line_id=statement.raw_line_id
            )
            credit_line = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=rule.credit_account_id,
                description=statement.description or rule.description_template,
                debit_amount=Decimal('0'),
                credit_amount=amount,
                line_number=2,
                raw_line_id=statement.raw_line_id
            )
        else:
            debit_line = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=rule.debit_account_id,
                description=statement.description or rule.description_template,
                debit_amount=amount,
                credit_amount=Decimal('0'),
                line_number=1,
                raw_line_id=statement.raw_line_id
            )
            credit_line = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=rule.credit_account_id,
                description=statement.description or rule.description_template,
                debit_amount=Decimal('0'),
                credit_amount=amount,
                line_number=2,
                raw_line_id=statement.raw_line_id
            )
        
        self.db.add(debit_line)
        self.db.add(credit_line)
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    def apply_rule_to_purchase_invoice(
        self,
        invoice: PurchaseInvoice,
        rule: AutoPostingRule,
        created_by: str
    ) -> JournalEntry:
        """应用规则到采购发票"""
        amount = invoice.total_amount
        
        if not amount or amount <= 0:
            raise ValueError("发票金额无效 / Invalid invoice amount")
        
        entry = JournalEntry(
            company_id=invoice.company_id,
            entry_date=invoice.invoice_date,
            entry_type='automatic',
            reference_number=f"PI-{invoice.invoice_number}",
            description=f"采购发票 {invoice.invoice_number} - {invoice.supplier_name}",
            total_debit=amount,
            total_credit=amount,
            source_type='purchase_invoice',
            source_id=invoice.id,
            created_by=created_by,
            is_posted=False
        )
        
        self.db.add(entry)
        self.db.flush()
        
        debit_line = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=rule.debit_account_id,
            description=f"采购 - {invoice.supplier_name}",
            debit_amount=amount,
            credit_amount=Decimal('0'),
            line_number=1,
            raw_line_id=invoice.raw_line_id
        )
        
        credit_line = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=rule.credit_account_id,
            description=f"应付账款 - {invoice.supplier_name}",
            debit_amount=Decimal('0'),
            credit_amount=amount,
            line_number=2,
            raw_line_id=invoice.raw_line_id
        )
        
        self.db.add(debit_line)
        self.db.add(credit_line)
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    def apply_rule_to_sales_invoice(
        self,
        invoice: SalesInvoice,
        rule: AutoPostingRule,
        created_by: str
    ) -> JournalEntry:
        """应用规则到销售发票"""
        amount = invoice.total_amount
        
        if not amount or amount <= 0:
            raise ValueError("发票金额无效 / Invalid invoice amount")
        
        entry = JournalEntry(
            company_id=invoice.company_id,
            entry_date=invoice.invoice_date,
            entry_type='automatic',
            reference_number=f"SI-{invoice.invoice_number}",
            description=f"销售发票 {invoice.invoice_number} - {invoice.customer_name}",
            total_debit=amount,
            total_credit=amount,
            source_type='sales_invoice',
            source_id=invoice.id,
            created_by=created_by,
            is_posted=False
        )
        
        self.db.add(entry)
        self.db.flush()
        
        debit_line = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=rule.debit_account_id,
            description=f"应收账款 - {invoice.customer_name}",
            debit_amount=amount,
            credit_amount=Decimal('0'),
            line_number=1,
            raw_line_id=invoice.raw_line_id
        )
        
        credit_line = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=rule.credit_account_id,
            description=f"销售收入 - {invoice.customer_name}",
            debit_amount=Decimal('0'),
            credit_amount=amount,
            line_number=2,
            raw_line_id=invoice.raw_line_id
        )
        
        self.db.add(debit_line)
        self.db.add(credit_line)
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    def batch_apply_rules(
        self,
        company_id: int,
        source_type: str,
        created_by: str,
        limit: Optional[int] = None
    ) -> Dict:
        """
        批量应用规则
        
        Args:
            company_id: 公司ID
            source_type: 来源类型
            created_by: 创建人
            limit: 最大处理数量
        
        Returns:
            {
                'processed': 处理数量,
                'success': 成功数量,
                'failed': 失败数量,
                'errors': [错误列表]
            }
        """
        processed = 0
        success = 0
        failed = 0
        errors = []
        
        if source_type == 'bank_statement':
            stmt = select(BankStatement).where(
                and_(
                    BankStatement.company_id == company_id,
                    BankStatement.is_posted == False
                )
            )
            if limit:
                stmt = stmt.limit(limit)
            
            result = self.db.execute(stmt)
            records = result.scalars().all()
            
            for record in records:
                processed += 1
                try:
                    keywords = [record.description] if record.description else []
                    amount = record.debit_amount or record.credit_amount
                    transaction_type = 'deposit' if record.debit_amount else 'withdrawal'
                    
                    rule = self.find_matching_rule(
                        company_id,
                        source_type,
                        transaction_type,
                        keywords,
                        amount
                    )
                    
                    if rule:
                        self.apply_rule_to_bank_statement(record, rule, created_by)
                        record.is_posted = True
                        success += 1
                    else:
                        errors.append({
                            'id': record.id,
                            'error': '未找到匹配规则 / No matching rule found'
                        })
                        failed += 1
                except Exception as e:
                    errors.append({
                        'id': record.id,
                        'error': str(e)
                    })
                    failed += 1
            
            self.db.commit()
        
        elif source_type == 'purchase_invoice':
            stmt = select(PurchaseInvoice).where(
                and_(
                    PurchaseInvoice.company_id == company_id,
                    PurchaseInvoice.is_posted == False
                )
            )
            if limit:
                stmt = stmt.limit(limit)
            
            result = self.db.execute(stmt)
            records = result.scalars().all()
            
            for record in records:
                processed += 1
                try:
                    keywords = [record.supplier_name, record.description] if record.description else [record.supplier_name]
                    
                    rule = self.find_matching_rule(
                        company_id,
                        source_type,
                        'purchase',
                        keywords,
                        record.total_amount
                    )
                    
                    if rule:
                        self.apply_rule_to_purchase_invoice(record, rule, created_by)
                        record.is_posted = True
                        success += 1
                    else:
                        errors.append({
                            'id': record.id,
                            'error': '未找到匹配规则 / No matching rule found'
                        })
                        failed += 1
                except Exception as e:
                    errors.append({
                        'id': record.id,
                        'error': str(e)
                    })
                    failed += 1
            
            self.db.commit()
        
        elif source_type == 'sales_invoice':
            stmt = select(SalesInvoice).where(
                and_(
                    SalesInvoice.company_id == company_id,
                    SalesInvoice.is_posted == False
                )
            )
            if limit:
                stmt = stmt.limit(limit)
            
            result = self.db.execute(stmt)
            records = result.scalars().all()
            
            for record in records:
                processed += 1
                try:
                    keywords = [record.customer_name, record.description] if record.description else [record.customer_name]
                    
                    rule = self.find_matching_rule(
                        company_id,
                        source_type,
                        'sales',
                        keywords,
                        record.total_amount
                    )
                    
                    if rule:
                        self.apply_rule_to_sales_invoice(record, rule, created_by)
                        record.is_posted = True
                        success += 1
                    else:
                        errors.append({
                            'id': record.id,
                            'error': '未找到匹配规则 / No matching rule found'
                        })
                        failed += 1
                except Exception as e:
                    errors.append({
                        'id': record.id,
                        'error': str(e)
                    })
                    failed += 1
            
            self.db.commit()
        
        return {
            'processed': processed,
            'success': success,
            'failed': failed,
            'errors': errors
        }
    
    def create_rule(
        self,
        source_type: str,
        transaction_type: str,
        debit_account_id: int,
        credit_account_id: int,
        description_template: str,
        company_id: Optional[int] = None,
        match_keywords: Optional[str] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        priority: int = 0,
        created_by: str = 'system'
    ) -> AutoPostingRule:
        """创建新的过账规则"""
        rule = AutoPostingRule(
            company_id=company_id,
            source_type=source_type,
            transaction_type=transaction_type,
            match_keywords=match_keywords,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            description_template=description_template,
            min_amount=min_amount,
            max_amount=max_amount,
            priority=priority,
            is_active=True,
            created_by=created_by
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        return rule
    
    def get_all_rules(
        self,
        company_id: Optional[int] = None,
        source_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[AutoPostingRule]:
        """获取所有规则"""
        conditions = []
        
        if company_id is not None:
            conditions.append(
                or_(
                    AutoPostingRule.company_id == company_id,
                    AutoPostingRule.company_id.is_(None)
                )
            )
        
        if source_type:
            conditions.append(AutoPostingRule.source_type == source_type)
        
        if is_active is not None:
            conditions.append(AutoPostingRule.is_active == is_active)
        
        stmt = select(AutoPostingRule)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(
            AutoPostingRule.company_id.desc().nullslast(),
            AutoPostingRule.priority.desc(),
            AutoPostingRule.created_at.desc()
        )
        
        result = self.db.execute(stmt)
        return result.scalars().all()
