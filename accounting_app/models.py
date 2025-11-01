"""
SQLAlchemy ORM 模型
对应init_db.sql中的核心表 + Phase 1-1新增的1:1原件保护表
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, DateTime, ForeignKey, Text, CheckConstraint, JSON, BigInteger
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
    raw_line_id = Column(Integer, ForeignKey('raw_lines.id', ondelete='SET NULL'), index=True)  # Phase 1-2: 防虚构交易
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
    raw_line_id = Column(Integer, ForeignKey('raw_lines.id', ondelete='SET NULL'), index=True)  # Phase 1-2: 防虚构交易
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
    raw_line_id = Column(Integer, ForeignKey('raw_lines.id', ondelete='SET NULL'), index=True)  # Phase 1-2: 防虚构交易
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
    raw_line_id = Column(Integer, ForeignKey('raw_lines.id', ondelete='SET NULL'), index=True)  # Phase 1-2: 防虚构交易
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


class ExportTemplate(Base):
    """
    CSV导出模板表 - 表驱动化配置
    支持不同会计软件的导出格式（SQL Account, AutoCount, UBS等）
    """
    __tablename__ = "export_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    template_name = Column(String(200), nullable=False)  # "SQL Account - General Ledger"
    software_name = Column(String(100), nullable=False, index=True)  # "SQL Account", "AutoCount", "UBS"
    export_type = Column(String(50), nullable=False, index=True)  # "general_ledger", "journal_entry", "trial_balance"
    column_mappings = Column(JSON, nullable=False)  # JSONB字段映射配置
    delimiter = Column(String(10), default=',')  # CSV分隔符
    date_format = Column(String(50), default='YYYY-MM-DD')  # 日期格式
    decimal_places = Column(Integer, default=2)  # 小数位数
    include_header = Column(Boolean, default=True)  # 是否包含列标题
    encoding = Column(String(20), default='utf-8')  # 文件编码
    description = Column(Text)  # 模板说明
    is_default = Column(Boolean, default=False, index=True)  # 是否为默认模板
    is_active = Column(Boolean, default=True, index=True)  # 是否启用
    usage_count = Column(Integer, default=0)  # 使用次数统计
    last_used_at = Column(DateTime(timezone=True))  # 最后使用时间
    created_by = Column(String(100))  # 创建人
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("export_type IN ('general_ledger', 'journal_entry', 'trial_balance', 'chart_of_accounts', 'customer_list', 'supplier_list')"),
        CheckConstraint("software_name IN ('SQL Account', 'AutoCount', 'UBS', 'QuickBooks', 'Xero', 'Generic')"),
    )


class RawDocument(Base):
    """
    Phase 1-1: 原件必存表
    所有上传文件的元数据，不管能否解析都要写入
    用途：确保1:1原件保护，防止数据丢失
    """
    __tablename__ = "raw_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    file_name = Column(Text, nullable=False)
    file_hash = Column(Text, nullable=False, index=True)  # 分块SHA256，避免大文件超时
    file_size = Column(BigInteger, nullable=False)  # 文件大小（字节）
    storage_path = Column(Text, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    uploaded_by = Column(Integer)  # 预留：关联users表
    source_engine = Column(String(20), nullable=False)  # flask | fastapi
    module = Column(String(50), nullable=False, index=True)  # credit-card | bank | savings | pos | supplier | reports
    status = Column(String(20), nullable=False, default='uploaded', index=True)  # uploaded | parsed | failed | reconciled
    total_lines = Column(Integer)  # PDF/CSV总行数（用于对账）
    parsed_lines = Column(Integer)  # 成功解析行数（用于对账）
    reconciliation_status = Column(String(20))  # match | mismatch | pending
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("source_engine IN ('flask', 'fastapi')"),
        CheckConstraint("module IN ('credit-card', 'bank', 'savings', 'pos', 'supplier', 'reports', 'management', 'temp')"),
        CheckConstraint("status IN ('uploaded', 'parsed', 'failed', 'reconciled')"),
        CheckConstraint("reconciliation_status IN ('match', 'mismatch', 'pending')"),
    )


class RawLine(Base):
    """
    Phase 1-1: 逐行原文表
    PDF/CSV的每一行原始内容，用于防虚构交易
    规则：业务表记录必须关联raw_line_id，否则进异常中心
    """
    __tablename__ = "raw_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_document_id = Column(Integer, ForeignKey('raw_documents.id', ondelete='CASCADE'), nullable=False, index=True)
    line_no = Column(Integer, nullable=False)  # 行号（1-based）
    page_no = Column(Integer)  # 页码（PDF专用）
    raw_text = Column(Text, nullable=False)  # 原始文本内容
    parser_version = Column(String(50))  # 解析器版本号
    is_parsed = Column(Boolean, default=False)  # 是否已解析成业务记录
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MigrationLog(Base):
    """
    Phase 1-1: 文件迁移日志表
    记录旧路径到新路径的迁移过程，支持分批回滚
    """
    __tablename__ = "migration_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='SET NULL'))
    src_path = Column(Text, nullable=False)  # 原路径
    dest_path = Column(Text)  # 目标路径
    module = Column(String(50))  # credit-card | bank | savings | pos | supplier
    batch_id = Column(String(50), index=True)  # 批次ID，格式：COMPANY-{company_id}-{YYYYMM}
    run_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    run_by = Column(String(100))  # 执行人
    status = Column(String(20), nullable=False, index=True)  # success | failed | skipped
    error_message = Column(Text)
    file_hash = Column(Text)  # 迁移前后hash校验
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('success', 'failed', 'skipped')"),
        CheckConstraint("module IN ('credit-card', 'bank', 'savings', 'pos', 'supplier', 'reports', 'management', 'temp')"),
    )


class FileIndex(Base):
    """
    Phase 1-3: 统一文件索引表
    Flask和FastAPI共用一套文件索引，支持软删除和回收站
    """
    __tablename__ = "file_index"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    file_category = Column(String, nullable=False)  # bank_statement, invoice, receipt, report
    file_type = Column(String, nullable=False)  # original | generated
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size_kb = Column(Integer)
    file_extension = Column(String)
    mime_type = Column(String)
    related_entity_type = Column(String)  # bank_statement_id, invoice_id, pos_report_id, credit_card_statement_id
    related_entity_id = Column(Integer)  # 关联业务记录ID
    period = Column(String)  # YYYY-MM
    transaction_date = Column(Date)
    upload_by = Column(String)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(Text)
    tags = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    module = Column(String)  # credit-card | bank | savings | pos | supplier | reports
    original_filename = Column(String)
    deleted_at = Column(DateTime(timezone=True))  # Phase 1-3: 软删除时间戳
    status = Column(String(20), default='active', index=True)  # Phase 1-3: active | archived | deleted
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived', 'deleted')"),
        CheckConstraint("file_type IN ('original', 'generated')"),
    )
