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
