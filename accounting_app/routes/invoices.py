"""
自动发票生成路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from decimal import Decimal

from ..db import get_db
from ..models import AutoInvoiceRule, SalesInvoice, Customer, JournalEntry, JournalEntryLine
from ..schemas import AutoInvoiceGenerate, AutoInvoiceResult

router = APIRouter()


@router.post("/auto-generate", response_model=AutoInvoiceResult)
def auto_generate_invoices(
    request: AutoInvoiceGenerate,
    db: Session = Depends(get_db)
):
    """
    根据自动发票规则生成当月发票
    
    场景：固定每月对客户开一张管理费/咨询费发票
    """
    # 获取有效的自动发票规则
    query = db.query(AutoInvoiceRule).filter(
        AutoInvoiceRule.company_id == request.company_id,
        AutoInvoiceRule.is_active == True
    )
    
    if request.customer_id:
        query = query.filter(AutoInvoiceRule.customer_id == request.customer_id)
    
    rules = query.all()
    
    if not rules:
        return AutoInvoiceResult(
            success=True,
            invoices_generated=0,
            invoice_numbers=[],
            total_amount=Decimal(0)
        )
    
    # 解析月份
    try:
        year, month = map(int, request.month.split('-'))
        invoice_date = date(year, month, 1)
        due_date = invoice_date + timedelta(days=30)
    except:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
    
    generated_invoices = []
    total_amount = Decimal(0)
    
    for rule in rules:
        # 检查是否在规则生效期内
        if rule.start_date > invoice_date:
            continue
        if rule.end_date and rule.end_date < invoice_date:
            continue
        
        # 检查是否已经生成过
        existing = db.query(SalesInvoice).filter(
            SalesInvoice.company_id == request.company_id,
            SalesInvoice.customer_id == rule.customer_id,
            SalesInvoice.invoice_date == invoice_date,
            SalesInvoice.auto_generated == True
        ).first()
        
        if existing:
            continue
        
        # 生成发票号
        invoice_number = f"INV-{request.month}-{rule.customer_id:04d}"
        
        # 创建销售发票
        invoice = SalesInvoice(
            company_id=request.company_id,
            customer_id=rule.customer_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            total_amount=rule.amount,
            received_amount=Decimal(0),
            balance_amount=rule.amount,
            status='unpaid',
            auto_generated=True,
            notes=rule.invoice_description
        )
        db.add(invoice)
        db.flush()
        
        # 生成会计分录
        entry_number = f"JE-INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        journal_entry = JournalEntry(
            company_id=request.company_id,
            entry_number=entry_number,
            entry_date=invoice_date,
            description=f"Auto Invoice: {invoice_number}",
            entry_type='invoice',
            reference_number=invoice_number,
            status='posted'
        )
        db.add(journal_entry)
        db.flush()
        
        # 借：应收账款  贷：收入
        debit_line = JournalEntryLine(
            journal_entry_id=journal_entry.id,
            account_id=1,  # TODO: 应收账款科目
            description=rule.invoice_description,
            debit_amount=rule.amount,
            credit_amount=Decimal(0),
            line_number=1
        )
        credit_line = JournalEntryLine(
            journal_entry_id=journal_entry.id,
            account_id=2,  # TODO: 收入科目
            description=rule.invoice_description,
            debit_amount=Decimal(0),
            credit_amount=rule.amount,
            line_number=2
        )
        db.add(debit_line)
        db.add(credit_line)
        
        invoice.journal_entry_id = journal_entry.id
        
        generated_invoices.append(invoice_number)
        total_amount += rule.amount
    
    db.commit()
    
    return AutoInvoiceResult(
        success=True,
        invoices_generated=len(generated_invoices),
        invoice_numbers=generated_invoices,
        total_amount=total_amount
    )
