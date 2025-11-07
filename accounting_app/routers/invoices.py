# -*- coding: utf-8 -*-
from fastapi import APIRouter, Response, Query
from datetime import datetime
from accounting_app.services.invoice_service import build_invoice_pdf

router = APIRouter(prefix="/invoices", tags=["invoices"])

DEMO_COMPANY = {
    "name": "INFINITE GZ SDN. BHD.",
    "address": "No. 28, Jalan Ipoh, 51200 Kuala Lumpur, Malaysia",
    "contact": "Tel: +60-12-345-6789  •  finance@infinitegz.com",
}

@router.get("/preview.pdf")
def preview(layout: str = Query("service", regex="^(service|debit|itemised)$")):
    if layout == "service":
        payload = {
            "company": DEMO_COMPANY,
            "title": "INVOICE",
            "bill_to": {"name":"VK Premium Auto Detailing", "address":"Seri Kembangan, Selangor", "email":"billing@vk.com"},
            "meta": {"number":"INV-2025-0001", "date": datetime.today().strftime("%Y-%m-%d"), "terms":"14 days"},
            "items": [
                {"desc":"Statutory Audit Services", "qty":1, "unit_price":12000},
                {"desc":"Corporate Tax Submission (YA2025)", "qty":1, "unit_price":6000},
            ],
            "tax_rate": 0.06,
            "payment":"Bank: HLB 160-0000-9191 • Payable to INFINITE GZ SDN BHD",
            "notes":[
                "Please settle within 14 days from invoice date.",
                "10% p.a. interest may be charged for overdue balances."
            ]
        }
    elif layout == "debit":
        payload = {
            "company": DEMO_COMPANY,
            "bill_to": {"name":"VK Premium Auto Detailing", "address":"Seri Kembangan", "email":"billing@vk.com"},
            "meta": {"number":"DN-2504001", "date":"2025-04-01", "terms":"CASH"},
            "items": [{"desc":"Late Payment Interest - March 2025 (08.03–21.03)", "amount":28.00}],
        }
    else:
        payload = {
            "company": DEMO_COMPANY,
            "title": "TAX INVOICE",
            "meta": {"number":"TI-0001", "date":"2025-03-18"},
            "st_rate": 0.06,
            "sections": [
                {"title":"FARE", "rows":[["No.","Description","Total Excl. ST","ST @ 6%"],
                                          ["1","1x Guest (IPH–SIN)","85.00","0.00"],
                                          ["2","1x Fuel Surcharge","40.00","0.00"],
                                          ["3","1x Malaysia Departure Levy","8.00","0.00"],
                                          ["4","1x Passenger Service Charge","35.00","0.00"],
                                          ["5","1x Regulatory Service Charge","1.00","0.00"]]},
                {"title":"FEES", "rows":[["No.","Description","MYR","MYR"],
                                         ["1","1x Checked baggage 20kg","70.00","0.00"],
                                         ["2","1x Xpress baggage","14.00","0.00"],
                                         ["3","1x Seat add-on","46.00","0.00"]]},
            ],
            "grand_total": 299.00,
        }
    pdf = build_invoice_pdf(layout, payload)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="preview_{layout}.pdf"'})

@router.post("/make")
def make(layout: str, number: str, bill_to_name: str, amount: float):
    """极简造一张单：/invoices/make?layout=debit&number=DN-1&bill_to_name=Ken&amount=28"""
    if layout not in ("service","debit","itemised"):
        layout = "service"
    payload = {
        "company": DEMO_COMPANY,
        "bill_to": {"name": bill_to_name},
        "meta": {"number": number, "date": datetime.today().strftime("%Y-%m-%d")},
        "items": [{"desc":"Custom item", "qty":1, "unit_price": amount}] if layout=="service" else
                 [{"desc":"Custom item", "amount": amount}],
        "tax_rate": 0.00
    }
    pdf = build_invoice_pdf(layout, payload)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{number}.pdf"'})

@router.get("/supplier.pdf")
def supplier_invoice(supplier: str = Query(...), month: str = Query(...)):
    """保留旧端点兼容性，使用service布局"""
    items = [
        {"date":"2025-11-05","desc":"Office Supplies","amount":450.0},
        {"date":"2025-11-12","desc":"A4 Paper","amount":280.0},
        {"date":"2025-11-20","desc":"Ink Cartridge","amount":320.0},
    ]
    total = sum(i["amount"] for i in items)
    payload = {
        "company": DEMO_COMPANY,
        "title": "INVOICE",
        "bill_to": {"name": supplier, "address": "Kuala Lumpur"},
        "meta": {"number": f"INV-{month}-{supplier[:3].upper()}", "date": datetime.today().strftime("%Y-%m-%d"), "terms":"14 days"},
        "items": [{"desc": i["desc"], "qty": 1, "unit_price": i["amount"]} for i in items],
        "tax_rate": 0.01,
        "payment":"Bank: HLB 160-0000-9191 • Payable to INFINITE GZ SDN BHD",
        "notes":["Service fee applies as per agreement."]
    }
    pdf = build_invoice_pdf("service", payload)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="supplier_{supplier}_{month}.pdf"'})
