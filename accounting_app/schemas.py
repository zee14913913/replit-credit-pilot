"""
Pydantic Schemas - API请求/响应数据验证
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ==================== Company Schemas ====================
class CompanyBase(BaseModel):
    company_code: str
    company_name: str
    registration_number: Optional[str] = None
    tax_number: Optional[str] = None
    business_type: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Bank Statement Schemas ====================
class BankStatementImport(BaseModel):
    bank_name: str
    account_number: str
    statement_month: str  # 2025-01

class BankStatementRow(BaseModel):
    transaction_date: date
    description: str
    reference_number: Optional[str] = None
    debit_amount: Decimal = 0
    credit_amount: Decimal = 0
    balance: Optional[Decimal] = None

class BankStatementResponse(BaseModel):
    id: int
    company_id: int
    bank_name: str
    account_number: str
    transaction_date: date
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    balance: Optional[Decimal]
    matched: bool
    auto_category: Optional[str]
    
    class Config:
        from_attributes = True


# ==================== Chart of Accounts Schemas ====================
class ChartOfAccountsCreate(BaseModel):
    company_id: int
    account_code: str
    account_name: str
    account_type: str  # asset, liability, equity, income, expense
    parent_id: Optional[int] = None
    description: Optional[str] = None

class ChartOfAccountsResponse(BaseModel):
    id: int
    account_code: str
    account_name: str
    account_type: str
    is_active: bool
    
    class Config:
        from_attributes = True


# ==================== Journal Entry Schemas ====================
class JournalEntryLineCreate(BaseModel):
    account_id: int
    description: Optional[str] = None
    debit_amount: Decimal = 0
    credit_amount: Decimal = 0
    line_number: int

class JournalEntryCreate(BaseModel):
    company_id: int
    entry_date: date
    description: str
    entry_type: str = 'manual'
    reference_number: Optional[str] = None
    lines: List[JournalEntryLineCreate]

class JournalEntryResponse(BaseModel):
    id: int
    entry_number: str
    entry_date: date
    description: str
    entry_type: str
    status: str
    
    class Config:
        from_attributes = True


# ==================== Supplier Schemas ====================
class SupplierCreate(BaseModel):
    company_id: int
    supplier_code: str
    supplier_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    payment_terms: int = 30

class SupplierResponse(BaseModel):
    id: int
    supplier_code: str
    supplier_name: str
    payment_terms: int
    status: str
    
    class Config:
        from_attributes = True


# ==================== Suppliers Aging Report Schemas ====================
class AgingBracket(BaseModel):
    bracket_name: str  # 0-30, 31-60, 61-90, 90+
    total_amount: Decimal

class SupplierAgingDetail(BaseModel):
    supplier_id: int
    supplier_code: str
    supplier_name: str
    aging_0_30: Decimal
    aging_31_60: Decimal
    aging_61_90: Decimal
    aging_90_plus: Decimal
    total_outstanding: Decimal

class SuppliersAgingReport(BaseModel):
    company_id: int
    report_date: date
    suppliers: List[SupplierAgingDetail]
    total_0_30: Decimal
    total_31_60: Decimal
    total_61_90: Decimal
    total_90_plus: Decimal
    grand_total: Decimal


# ==================== Customers Aging Report Schemas (AR) ====================
class CustomerAgingDetail(BaseModel):
    customer_id: int
    customer_code: str
    customer_name: str
    aging_0_30: Decimal
    aging_31_60: Decimal
    aging_61_90: Decimal
    aging_90_plus: Decimal
    total_outstanding: Decimal

class CustomersAgingReport(BaseModel):
    company_id: int
    report_date: date
    customers: List[CustomerAgingDetail]
    total_0_30: Decimal
    total_31_60: Decimal
    total_61_90: Decimal
    total_90_plus: Decimal
    grand_total: Decimal


# ==================== Customer Ledger Schemas ====================
class CustomerTransactionDetail(BaseModel):
    transaction_date: date
    transaction_type: str  # invoice, receipt
    reference_number: str
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Decimal

class CustomerLedgerReport(BaseModel):
    customer_id: int
    customer_code: str
    customer_name: str
    opening_balance: Decimal
    transactions: List[CustomerTransactionDetail]
    closing_balance: Decimal


# ==================== P&L Report Schemas ====================
class PNLLineItem(BaseModel):
    account_code: str
    account_name: str
    amount: Decimal

class PNLSection(BaseModel):
    section_name: str
    line_items: List[PNLLineItem]
    section_total: Decimal

class ProfitLossReport(BaseModel):
    company_id: int
    period: str  # 2025-01
    revenue: PNLSection
    cost_of_sales: Optional[PNLSection] = None
    operating_expenses: PNLSection
    gross_profit: Decimal
    net_profit: Decimal
    tax_adjustments: List[dict] = []  # 税务调整
    adjusted_net_profit: Decimal


# ==================== Balance Sheet Schemas ====================
class BalanceSheetSection(BaseModel):
    section_name: str
    line_items: List[PNLLineItem]
    section_total: Decimal

class BalanceSheetReport(BaseModel):
    company_id: int
    as_of_date: date
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal


# ==================== Bank Package Report Schemas ====================
class BankPackageReport(BaseModel):
    company_id: int
    company_name: str
    generated_date: datetime
    pnl_12_months: List[ProfitLossReport]
    latest_balance_sheet: BalanceSheetReport
    suppliers_aging: SuppliersAgingReport
    customer_ledger_summary: List[CustomerLedgerReport]
    bank_statement_summary: dict
    tax_adjustments_summary: List[dict]
    notes: str = "This financial package is prepared for bank loan application purposes"


# ==================== Auto Invoice Schemas ====================
class AutoInvoiceGenerate(BaseModel):
    company_id: int
    customer_id: Optional[int] = None
    month: str  # 2025-01

class AutoInvoiceResult(BaseModel):
    success: bool
    invoices_generated: int
    invoice_numbers: List[str]
    total_amount: Decimal


# ==================== Exception Center Schemas ====================
class ExceptionBase(BaseModel):
    exception_type: str  # pdf_parse, ocr_error, customer_mismatch, supplier_mismatch, posting_error
    severity: str  # low, medium, high, critical
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    error_message: str
    raw_data: Optional[str] = None

class ExceptionCreate(ExceptionBase):
    pass  # company_id通过Depends(get_current_company_id)注入，不接受用户输入

class ExceptionUpdate(BaseModel):
    status: Optional[str] = None  # new, in_progress, resolved, ignored
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None

class ExceptionResponse(BaseModel):
    id: int
    company_id: int
    exception_type: str
    severity: str
    source_type: Optional[str]
    source_id: Optional[int]
    error_message: str
    raw_data: Optional[str]
    status: str
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ExceptionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    exceptions: List[ExceptionResponse]

class ExceptionSummary(BaseModel):
    total: int
    by_type: dict  # {pdf_parse: 5, ocr_error: 3, ...}
    by_severity: dict  # {low: 2, medium: 3, high: 2, critical: 1}
    by_status: dict  # {new: 5, in_progress: 2, resolved: 1}
    critical_count: int
    high_count: int


# ==================== Auto Posting Rules Schemas ====================
class RuleBase(BaseModel):
    rule_name: str
    source_type: str  # bank_import, supplier_invoice, sales_invoice, general
    pattern: str  # 匹配模式（关键字或正则表达式）
    is_regex: bool = False
    priority: int = 100  # 优先级（数字越小优先级越高）
    debit_account_code: str
    credit_account_code: str
    description: Optional[str] = None
    is_active: bool = True

class RuleCreate(RuleBase):
    pass  # company_id通过Depends(get_current_company_id)注入

class RuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    source_type: Optional[str] = None
    pattern: Optional[str] = None
    is_regex: Optional[bool] = None
    priority: Optional[int] = None
    debit_account_code: Optional[str] = None
    credit_account_code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class RuleResponse(RuleBase):
    id: int
    company_id: int
    match_count: int
    last_matched_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RuleListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    rules: List[RuleResponse]

class RuleTestRequest(BaseModel):
    """测试规则匹配请求"""
    description: str  # 要测试的交易描述
    source_type: str = "bank_import"

class RuleTestResponse(BaseModel):
    """测试规则匹配响应"""
    matched: bool
    rule: Optional[RuleResponse] = None
    reason: Optional[str] = None


# ============================================================
# Export Template Schemas (CSV导出模板)
# ============================================================

class TemplateBase(BaseModel):
    """导出模板基础Schema"""
    template_name: str
    software_name: str  # "SQL Account", "AutoCount", "UBS", "QuickBooks", "Xero", "Generic"
    export_type: str  # "general_ledger", "journal_entry", "trial_balance", etc
    column_mappings: dict  # JSONB字段映射配置
    delimiter: str = ","
    date_format: str = "YYYY-MM-DD"
    decimal_places: int = 2
    include_header: bool = True
    encoding: str = "utf-8"
    description: Optional[str] = None

class TemplateCreate(TemplateBase):
    """创建导出模板"""
    pass

class TemplateUpdate(BaseModel):
    """更新导出模板（所有字段可选）"""
    template_name: Optional[str] = None
    software_name: Optional[str] = None
    export_type: Optional[str] = None
    column_mappings: Optional[dict] = None
    delimiter: Optional[str] = None
    date_format: Optional[str] = None
    decimal_places: Optional[int] = None
    include_header: Optional[bool] = None
    encoding: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class TemplateResponse(TemplateBase):
    """导出模板响应"""
    id: int
    company_id: int
    is_default: bool
    is_active: bool
    usage_count: int
    last_used_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TemplateListResponse(BaseModel):
    """导出模板列表响应"""
    total: int
    skip: int
    limit: int
    templates: List[TemplateResponse]

class TemplateTestRequest(BaseModel):
    """测试模板导出请求"""
    template_id: int
    sample_data: List[dict]  # 样本数据
    preview_rows: int = 5  # 预览行数

class TemplateTestResponse(BaseModel):
    """测试模板导出响应"""
    success: bool
    preview_csv: str  # CSV预览内容
    row_count: int
    column_count: int
    errors: Optional[List[str]] = None
