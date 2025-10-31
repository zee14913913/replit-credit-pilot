"""
财务报表路由
包括：Suppliers Aging, Customer Ledger, P&L, Balance Sheet, Bank Package
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal

from ..db import get_db
from ..models import *
from ..schemas import (
    SuppliersAgingReport, SupplierAgingDetail,
    CustomerLedgerReport, CustomerTransactionDetail,
    ProfitLossReport, BalanceSheetReport,
    BankPackageReport
)

router = APIRouter()


@router.get("/suppliers-aging", response_model=SuppliersAgingReport)
def get_suppliers_aging(company_id: int, as_of_date: Optional[str] = None, db: Session = Depends(get_db)):
    """
    供应商账龄报表（Suppliers Aging）
    按 0-30, 31-60, 61-90, 90+ 分类
    """
    if not as_of_date:
        as_of_date = date.today()
    else:
        as_of_date = date.fromisoformat(as_of_date)
    
    # 获取所有未付清的采购发票
    invoices = db.query(PurchaseInvoice).join(Supplier).filter(
        PurchaseInvoice.company_id == company_id,
        PurchaseInvoice.balance_amount > 0
    ).all()
    
    # 按供应商分组计算账龄
    supplier_aging = {}
    
    for inv in invoices:
        days_overdue = (as_of_date - inv.due_date).days
        
        if inv.supplier_id not in supplier_aging:
            supplier_aging[inv.supplier_id] = {
                'supplier_id': inv.supplier_id,
                'supplier_code': inv.supplier.supplier_code if inv.supplier else '',
                'supplier_name': inv.supplier.supplier_name if inv.supplier else '',
                'aging_0_30': Decimal(0),
                'aging_31_60': Decimal(0),
                'aging_61_90': Decimal(0),
                'aging_90_plus': Decimal(0),
                'total_outstanding': Decimal(0)
            }
        
        amount = inv.balance_amount
        
        if days_overdue <= 30:
            supplier_aging[inv.supplier_id]['aging_0_30'] += amount
        elif days_overdue <= 60:
            supplier_aging[inv.supplier_id]['aging_31_60'] += amount
        elif days_overdue <= 90:
            supplier_aging[inv.supplier_id]['aging_61_90'] += amount
        else:
            supplier_aging[inv.supplier_id]['aging_90_plus'] += amount
        
        supplier_aging[inv.supplier_id]['total_outstanding'] += amount
    
    # 计算总计
    total_0_30 = sum(s['aging_0_30'] for s in supplier_aging.values())
    total_31_60 = sum(s['aging_31_60'] for s in supplier_aging.values())
    total_61_90 = sum(s['aging_61_90'] for s in supplier_aging.values())
    total_90_plus = sum(s['aging_90_plus'] for s in supplier_aging.values())
    grand_total = total_0_30 + total_31_60 + total_61_90 + total_90_plus
    
    return SuppliersAgingReport(
        company_id=company_id,
        report_date=as_of_date,
        suppliers=[SupplierAgingDetail(**s) for s in supplier_aging.values()],
        total_0_30=total_0_30,
        total_31_60=total_31_60,
        total_61_90=total_61_90,
        total_90_plus=total_90_plus,
        grand_total=grand_total
    )


@router.get("/customer-ledger", response_model=CustomerLedgerReport)
def get_customer_ledger(customer_id: int, db: Session = Depends(get_db)):
    """
    客户应收账款台账（Customer Ledger / AR）
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # 获取所有发票和收款
    invoices = db.query(SalesInvoice).filter(
        SalesInvoice.customer_id == customer_id
    ).order_by(SalesInvoice.invoice_date).all()
    
    receipts = db.query(CustomerReceipt).filter(
        CustomerReceipt.customer_id == customer_id
    ).order_by(CustomerReceipt.receipt_date).all()
    
    # 合并并排序
    transactions = []
    opening_balance = Decimal(0)
    running_balance = opening_balance
    
    for inv in invoices:
        running_balance += inv.total_amount
        transactions.append(CustomerTransactionDetail(
            transaction_date=inv.invoice_date,
            transaction_type='invoice',
            reference_number=inv.invoice_number,
            description=inv.notes or "Sales Invoice",
            debit_amount=inv.total_amount,
            credit_amount=Decimal(0),
            running_balance=running_balance
        ))
    
    for rec in receipts:
        running_balance -= rec.receipt_amount
        transactions.append(CustomerTransactionDetail(
            transaction_date=rec.receipt_date,
            transaction_type='receipt',
            reference_number=rec.receipt_number,
            description=rec.notes or "Payment Received",
            debit_amount=Decimal(0),
            credit_amount=rec.receipt_amount,
            running_balance=running_balance
        ))
    
    # 按日期排序
    transactions.sort(key=lambda x: x.transaction_date)
    
    return CustomerLedgerReport(
        customer_id=customer.id,
        customer_code=customer.customer_code,
        customer_name=customer.customer_name,
        opening_balance=opening_balance,
        transactions=transactions,
        closing_balance=running_balance
    )


@router.get("/pnl")
def get_profit_loss(company_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """
    损益表（P&L / Profit & Loss Statement）
    """
    period = f"{year}-{month:02d}"
    
    # TODO: 实际应从journal_entry_lines + financial_report_mapping生成
    # 这里返回简化版示例
    
    return {
        "company_id": company_id,
        "period": period,
        "revenue": {
            "section_name": "Revenue",
            "line_items": [
                {"account_code": "4000", "account_name": "Sales Revenue", "amount": 50000.00}
            ],
            "section_total": 50000.00
        },
        "operating_expenses": {
            "section_name": "Operating Expenses",
            "line_items": [
                {"account_code": "6000", "account_name": "Salaries", "amount": 15000.00},
                {"account_code": "6100", "account_name": "Rent", "amount": 3000.00}
            ],
            "section_total": 18000.00
        },
        "gross_profit": 50000.00,
        "net_profit": 32000.00,
        "tax_adjustments": [],
        "adjusted_net_profit": 32000.00
    }


@router.get("/balance-sheet")
def get_balance_sheet(company_id: int, as_of_date: str, db: Session = Depends(get_db)):
    """
    资产负债表（Balance Sheet）
    """
    # TODO: 实际应从journal_entry_lines汇总生成
    # 这里返回简化版示例
    
    return {
        "company_id": company_id,
        "as_of_date": as_of_date,
        "assets": {
            "section_name": "Assets",
            "line_items": [
                {"account_code": "1000", "account_name": "Cash & Bank", "amount": 100000.00},
                {"account_code": "1200", "account_name": "Accounts Receivable", "amount": 50000.00}
            ],
            "section_total": 150000.00
        },
        "liabilities": {
            "section_name": "Liabilities",
            "line_items": [
                {"account_code": "2000", "account_name": "Accounts Payable", "amount": 30000.00}
            ],
            "section_total": 30000.00
        },
        "equity": {
            "section_name": "Equity",
            "line_items": [
                {"account_code": "3000", "account_name": "Owner's Capital", "amount": 120000.00}
            ],
            "section_total": 120000.00
        },
        "total_assets": 150000.00,
        "total_liabilities": 30000.00,
        "total_equity": 120000.00
    }


@router.get("/bank-package")
def get_bank_package(company_id: int, db: Session = Depends(get_db)):
    """
    银行贷款资料包
    包含：12个月P&L、最新Balance Sheet、AR/AP Aging、银行流水汇总、税务调整
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # 生成12个月P&L（简化版）
    pnl_12_months = []
    # TODO: 实际应循环生成12个月的P&L
    
    # 获取最新Balance Sheet
    latest_balance_sheet = get_balance_sheet(company_id, date.today().isoformat(), db)
    
    # 获取Suppliers Aging
    suppliers_aging = get_suppliers_aging(company_id, None, db)
    
    # 银行流水汇总
    bank_summary = db.query(
        func.sum(BankStatement.debit_amount).label('total_debit'),
        func.sum(BankStatement.credit_amount).label('total_credit')
    ).filter(BankStatement.company_id == company_id).first()
    
    return {
        "company_id": company_id,
        "company_name": company.company_name,
        "generated_date": datetime.now(),
        "pnl_12_months": pnl_12_months,
        "latest_balance_sheet": latest_balance_sheet,
        "suppliers_aging": suppliers_aging,
        "customer_ledger_summary": [],
        "bank_statement_summary": {
            "total_debit": float(bank_summary[0] or 0),
            "total_credit": float(bank_summary[1] or 0)
        },
        "tax_adjustments_summary": [],
        "notes": "This financial package is prepared for bank loan application purposes"
    }
