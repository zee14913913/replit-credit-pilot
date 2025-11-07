from fastapi import APIRouter, Query
from accounting_app.services.invoice_service import build_invoice_pdf
router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.get("/supplier.pdf")
def supplier_invoice(supplier: str = Query(...), month: str = Query(...)):
    items = [
        {"date":"2025-11-05","desc":"Office Supplies","amount":450.0},
        {"date":"2025-11-12","desc":"A4 Paper","amount":280.0},
        {"date":"2025-11-20","desc":"Ink Cartridge","amount":320.0},
    ]
    return build_invoice_pdf(supplier, month, items)
