"""
SQLAlchemy ORM 模型
对应init_db.sql中的18个核心表
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    company_code = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    registration_number = Column(String(100))
    tax_number = Column(String(100))
    business_type = Column(String(100))
    address = Column(Text)
    contact_person = Column(String(100))
    contact_phone = Column(String(50))
    contact_email = Column(String(100))
    bank_name = Column(String(100))
    bank_account_number = Column(String(100))
    fiscal_year_end = Column(String(10), default='12-31')
    status = Column(String(20), default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChartOfAccounts(Base):
    __tablename__ = "chart_of_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    account_code = Column(String(50), nullable=False)
    account_name = Column(String(200), nullable=False)
    account_type = Column(String(50), nullable=False)  # asset, liability, equity, income, expense
    parent_id = Column(Integer, ForeignKey('chart_of_accounts.id'))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("account_type IN ('asset', 'liability', 'equity', 'income', 'expense')"),
    )


class BankStatement(Base):
    __tablename__ = "bank_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    bank_name = Column(String(100), nullable=False)
    account_number = Column(String(100), nullable=False)
    statement_month = Column(String(7), nullable=False, index=True)  # 2025-01
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=False)
    reference_number = Column(String(100))
    debit_amount = Column(Numeric(15,2), default=0)
    credit_amount = Column(Numeric(15,2), default=0)
    balance = Column(Numeric(15,2))
    matched = Column(Boolean, default=False, index=True)
    matched_journal_id = Column(Integer)
    auto_category = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    entry_number = Column(String(50), unique=True, nullable=False)
    entry_date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=False)
    entry_type = Column(String(50), default='manual')  # manual, auto, bank_import, invoice, payment, payroll, tax_adjustment
    reference_number = Column(String(100))
    created_by = Column(String(100))
    status = Column(String(20), default='posted')  # draft, posted, reversed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("entry_type IN ('manual', 'auto', 'bank_import', 'invoice', 'payment', 'payroll', 'tax_adjustment')"),
        CheckConstraint("status IN ('draft', 'posted', 'reversed')"),
    )


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, ForeignKey('chart_of_accounts.id'), nullable=False)
    description = Column(Text)
    debit_amount = Column(Numeric(15,2), default=0)
    credit_amount = Column(Numeric(15,2), default=0)
    line_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    supplier_code = Column(String(50), nullable=False)
    supplier_name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)
    payment_terms = Column(Integer, default=30)
    status = Column(String(20), default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15,2), nullable=False)
    paid_amount = Column(Numeric(15,2), default=0)
    balance_amount = Column(Numeric(15,2), nullable=False)
    status = Column(String(20), default='unpaid')  # unpaid, partial, paid, overdue
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    payment_number = Column(String(100), nullable=False)
    payment_date = Column(Date, nullable=False, index=True)
    payment_amount = Column(Numeric(15,2), nullable=False)
    payment_method = Column(String(50))
    reference_number = Column(String(100))
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey('supplier_payments.id', ondelete='CASCADE'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('purchase_invoices.id'), nullable=False)
    allocated_amount = Column(Numeric(15,2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    customer_code = Column(String(50), nullable=False)
    customer_name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)
    credit_limit = Column(Numeric(15,2), default=0)
    payment_terms = Column(Integer, default=30)
    status = Column(String(20), default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SalesInvoice(Base):
    __tablename__ = "sales_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15,2), nullable=False)
    received_amount = Column(Numeric(15,2), default=0)
    balance_amount = Column(Numeric(15,2), nullable=False)
    status = Column(String(20), default='unpaid')  # unpaid, partial, paid, overdue
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'))
    auto_generated = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class POSReport(Base):
    __tablename__ = "pos_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    report_number = Column(String(100), nullable=False)
    report_date = Column(Date, nullable=False, index=True)
    total_sales = Column(Numeric(15,2), nullable=False)
    total_transactions = Column(Integer, default=0)
    payment_method = Column(String(50))  # cash, card, online, mixed
    reference_number = Column(String(100))
    file_path = Column(String(500))
    parse_status = Column(String(20), default='parsed')  # parsed, pending, failed
    auto_generated_invoices = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class POSTransaction(Base):
    __tablename__ = "pos_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    pos_report_id = Column(Integer, ForeignKey('pos_reports.id', ondelete='CASCADE'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)  # 可空，待匹配
    transaction_time = Column(DateTime, nullable=False)
    transaction_amount = Column(Numeric(15,2), nullable=False)
    payment_method = Column(String(50))
    customer_name_raw = Column(String(200))  # 原始客户名（用于匹配）
    reference_number = Column(String(100))
    sales_invoice_id = Column(Integer, ForeignKey('sales_invoices.id'))  # 生成的发票ID
    matched = Column(Boolean, default=False, index=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CustomerReceipt(Base):
    __tablename__ = "customer_receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    receipt_number = Column(String(100), nullable=False)
    receipt_date = Column(Date, nullable=False, index=True)
    receipt_amount = Column(Numeric(15,2), nullable=False)
    payment_method = Column(String(50))
    reference_number = Column(String(100))
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReceiptAllocation(Base):
    __tablename__ = "receipt_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey('customer_receipts.id', ondelete='CASCADE'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('sales_invoices.id'), nullable=False)
    allocated_amount = Column(Numeric(15,2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinancialReportMapping(Base):
    __tablename__ = "financial_report_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, ForeignKey('chart_of_accounts.id'), nullable=False)
    report_type = Column(String(50), nullable=False)  # pnl, balance_sheet
    report_section = Column(String(100), nullable=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    employee_code = Column(String(50), nullable=False)
    employee_name = Column(String(200), nullable=False)
    position = Column(String(100))
    department = Column(String(100))
    ic_number = Column(String(50))
    epf_number = Column(String(50))
    socso_number = Column(String(50))
    basic_salary = Column(Numeric(15,2), default=0)
    hire_date = Column(Date)
    status = Column(String(20), default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PayrollRun(Base):
    __tablename__ = "payroll_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    payroll_number = Column(String(100), nullable=False)
    payroll_month = Column(String(7), nullable=False, index=True)
    payment_date = Column(Date, nullable=False)
    total_gross = Column(Numeric(15,2), default=0)
    total_epf_employer = Column(Numeric(15,2), default=0)
    total_epf_employee = Column(Numeric(15,2), default=0)
    total_socso = Column(Numeric(15,2), default=0)
    total_net = Column(Numeric(15,2), default=0)
    status = Column(String(20), default='draft')  # draft, posted, paid
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PayrollItem(Base):
    __tablename__ = "payroll_items"
    
    id = Column(Integer, primary_key=True, index=True)
    payroll_run_id = Column(Integer, ForeignKey('payroll_runs.id', ondelete='CASCADE'), nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    basic_salary = Column(Numeric(15,2), nullable=False)
    allowances = Column(Numeric(15,2), default=0)
    overtime = Column(Numeric(15,2), default=0)
    gross_salary = Column(Numeric(15,2), nullable=False)
    epf_employee = Column(Numeric(15,2), default=0)
    epf_employer = Column(Numeric(15,2), default=0)
    socso = Column(Numeric(15,2), default=0)
    income_tax = Column(Numeric(15,2), default=0)
    other_deductions = Column(Numeric(15,2), default=0)
    net_salary = Column(Numeric(15,2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TaxAdjustment(Base):
    __tablename__ = "tax_adjustments"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    adjustment_period = Column(String(7), nullable=False, index=True)  # 2025-01
    account_id = Column(Integer, ForeignKey('chart_of_accounts.id'))
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15,2), nullable=False)
    direction = Column(String(10), nullable=False)  # add, deduct
    category = Column(String(100))
    reason = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("direction IN ('add', 'deduct')"),
    )


class AutoInvoiceRule(Base):
    __tablename__ = "auto_invoice_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    rule_name = Column(String(200), nullable=False)
    invoice_description = Column(Text, nullable=False)
    amount = Column(Numeric(15,2), nullable=False)
    frequency = Column(String(20), default='monthly')  # monthly, quarterly, yearly
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("frequency IN ('monthly', 'quarterly', 'yearly')"),
    )


class Exception(Base):
    __tablename__ = "exceptions"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    exception_type = Column(String(50), nullable=False, index=True)  # pdf_parse, ocr_error, customer_mismatch, supplier_mismatch, posting_error
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    source_type = Column(String(50))  # bank_statement, pos_report, sales_invoice, purchase_invoice, journal_entry
    source_id = Column(Integer)  # 来源记录ID
    error_message = Column(Text, nullable=False)
    raw_data = Column(Text)  # JSON格式的原始数据
    status = Column(String(20), default='new', index=True)  # new, in_progress, resolved, ignored
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("exception_type IN ('pdf_parse', 'ocr_error', 'customer_mismatch', 'supplier_mismatch', 'posting_error')"),
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')"),
        CheckConstraint("status IN ('new', 'in_progress', 'resolved', 'ignored')"),
    )


class AutoPostingRule(Base):
    """
    自动记账规则表 - 表驱动化配置
    替代硬编码的MATCHING_RULES，支持用户自定义规则
    """
    __tablename__ = "auto_posting_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    rule_name = Column(String(200), nullable=False)  # 规则名称（便于识别）
    source_type = Column(String(50), nullable=False, index=True)  # bank_import, supplier_invoice, sales_invoice
    pattern = Column(Text, nullable=False)  # 匹配模式（关键字或正则表达式）
    is_regex = Column(Boolean, default=False)  # 是否为正则表达式
    priority = Column(Integer, default=100, index=True)  # 优先级（数字越小优先级越高）
    debit_account_code = Column(String(50), nullable=False)  # 借方科目代码
    credit_account_code = Column(String(50), nullable=False)  # 贷方科目代码
    description = Column(Text)  # 规则说明
    is_active = Column(Boolean, default=True, index=True)  # 是否启用
    match_count = Column(Integer, default=0)  # 匹配次数统计
    last_matched_at = Column(DateTime(timezone=True))  # 最后匹配时间
    created_by = Column(String(100))  # 创建人
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("source_type IN ('bank_import', 'supplier_invoice', 'sales_invoice', 'general')"),
    )
