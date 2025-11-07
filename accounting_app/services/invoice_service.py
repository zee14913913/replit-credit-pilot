from io import BytesIO

def render_supplier_invoices_pdf(suppliers: list, month: str) -> bytes:
    """
    占位：返回极简 PDF；未来用 reportlab/WeasyPrint 生成正式版
    """
    bio = BytesIO()
    bio.write(b"%PDF-1.4\n% Supplier Invoices Demo\n")
    return bio.getvalue()
