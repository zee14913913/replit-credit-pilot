"""
供应商发票API路由
上传、解析、查询、Aging报表
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

from ..services.invoice_processor import process_supplier_invoice, InvoiceProcessor
from ..middleware.multi_tenant import get_current_company_id
from ..db import get_db
from ..models import PurchaseInvoice, Supplier
from pydantic import BaseModel

router = APIRouter(
    prefix="/supplier-invoices",
    tags=["Supplier Invoices"]
)

logger = logging.getLogger(__name__)


# ========== Pydantic Schemas ==========

class PurchaseInvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    invoice_date: date
    due_date: date
    total_amount: float
    paid_amount: float
    balance_amount: float
    status: str
    supplier_name: str
    supplier_code: str
    journal_entry_id: Optional[int]
    
    class Config:
        from_attributes = True


class AgingBucketResponse(BaseModel):
    bucket_name: str
    days_range: str
    invoice_count: int
    total_amount: float


# ========== API Endpoints ==========

@router.post("/upload")
async def upload_supplier_invoice(
    file: UploadFile = File(...),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    上传供应商发票
    
    ## 支持的文件格式
    - PDF (文本PDF或扫描件，自动OCR)
    - JPG/PNG (自动OCR)
    
    ## 自动处理流程
    1. **解析发票内容**：自动识别发票号、日期、金额、供应商
    2. **重复检测**：检查是否已存在相同发票号
    3. **自动生成供应商**：如果供应商不存在，自动创建
    4. **生成会计分录**：
       - 借：Purchases (费用科目)
       - 贷：Accounts Payable (应付账款)
    5. **更新Aging状态**：自动计算是否逾期
    
    ## 返回
    - `success`: 是否成功
    - `invoice_id`: 发票ID
    - `journal_entry_id`: 会计分录ID
    - `parsed_data`: 解析出的发票数据
    - `duplicate_check`: 重复检测结果
    
    ## 示例
    ```bash
    curl -X POST "http://localhost:8000/api/supplier-invoices/upload" \\
      -H "company_id: 1" \\
      -F "file=@invoice.pdf"
    ```
    """
    try:
        logger.info(f"收到发票上传: company_id={company_id}, file={file.filename}")
        
        # 验证文件类型
        if not (file.filename.lower().endswith('.pdf') or 
                file.filename.lower().endswith(('.jpg', '.jpeg', '.png'))):
            raise HTTPException(
                status_code=415, 
                detail="不支持的文件类型。仅支持 PDF, JPG, PNG 格式"
            )
        
        # 读取文件内容
        file_content = await file.read()
        
        # 处理发票
        result = process_supplier_invoice(
            db=db,
            company_id=company_id,
            file_content=file_content,
            filename=file.filename
        )
        
        return result
    
    except Exception as e:
        logger.error(f"发票上传失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/list")
def list_supplier_invoices(
    company_id: int = Depends(get_current_company_id),
    status: Optional[str] = Query(None, description="状态过滤：unpaid, partial, paid, overdue"),
    supplier_id: Optional[int] = Query(None, description="供应商ID过滤"),
    from_date: Optional[date] = Query(None, description="开始日期"),
    to_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    列出供应商发票
    
    ## 参数
    - **status**: 状态过滤 (unpaid, partial, paid, overdue)
    - **supplier_id**: 供应商ID
    - **from_date**: 开始日期
    - **to_date**: 结束日期
    
    ## 返回
    发票列表，包含供应商信息
    
    ## 示例
    ```bash
    # 列出所有未支付发票
    GET /api/supplier-invoices/list?status=unpaid&company_id=1
    
    # 列出特定供应商的发票
    GET /api/supplier-invoices/list?supplier_id=5&company_id=1
    
    # 列出特定日期范围的发票
    GET /api/supplier-invoices/list?from_date=2025-08-01&to_date=2025-08-31&company_id=1
    ```
    """
    query = db.query(PurchaseInvoice, Supplier).join(
        Supplier,
        PurchaseInvoice.supplier_id == Supplier.id
    ).filter(
        PurchaseInvoice.company_id == company_id
    )
    
    # 状态过滤
    if status:
        query = query.filter(PurchaseInvoice.status == status)
    
    # 供应商过滤
    if supplier_id:
        query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
    
    # 日期过滤
    if from_date:
        query = query.filter(PurchaseInvoice.invoice_date >= from_date)
    if to_date:
        query = query.filter(PurchaseInvoice.invoice_date <= to_date)
    
    # 执行查询
    results = query.all()
    
    # 格式化输出
    invoices = []
    for invoice, supplier in results:
        invoices.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "total_amount": float(invoice.total_amount),
            "paid_amount": float(invoice.paid_amount),
            "balance_amount": float(invoice.balance_amount),
            "status": invoice.status,
            "supplier_id": supplier.id,
            "supplier_code": supplier.supplier_code,
            "supplier_name": supplier.supplier_name,
            "journal_entry_id": invoice.journal_entry_id,
            "notes": invoice.notes
        })
    
    return invoices


@router.get("/aging-report")
def get_aging_report(
    company_id: int = Depends(get_current_company_id),
    as_of_date: Optional[date] = Query(None, description="截止日期，默认今天"),
    db: Session = Depends(get_db)
):
    """
    生成应付账款账龄报表 (Accounts Payable Aging Report)
    
    ## 账龄分段
    - **Current**: 未到期
    - **1-30 days**: 逾期1-30天
    - **31-60 days**: 逾期31-60天
    - **61-90 days**: 逾期61-90天
    - **Over 90 days**: 逾期超过90天
    
    ## 返回
    - 分段统计（发票数量、总金额）
    - 每个分段的详细发票列表
    - 总计
    
    ## 业务用途
    - 现金流管理
    - 供应商付款优先级排序
    - 财务健康度评估
    
    ## 示例
    ```bash
    GET /api/supplier-invoices/aging-report?company_id=1
    GET /api/supplier-invoices/aging-report?company_id=1&as_of_date=2025-08-31
    ```
    """
    if not as_of_date:
        as_of_date = date.today()
    
    # 获取所有未付清的发票
    invoices = db.query(PurchaseInvoice, Supplier).join(
        Supplier,
        PurchaseInvoice.supplier_id == Supplier.id
    ).filter(
        PurchaseInvoice.company_id == company_id,
        PurchaseInvoice.balance_amount > 0
    ).all()
    
    # 分段统计
    buckets = {
        "current": {"name": "Current", "range": "Not due", "invoices": [], "count": 0, "total": 0},
        "1-30": {"name": "1-30 days", "range": "1-30 days overdue", "invoices": [], "count": 0, "total": 0},
        "31-60": {"name": "31-60 days", "range": "31-60 days overdue", "invoices": [], "count": 0, "total": 0},
        "61-90": {"name": "61-90 days", "range": "61-90 days overdue", "invoices": [], "count": 0, "total": 0},
        "over-90": {"name": "Over 90 days", "range": "Over 90 days overdue", "invoices": [], "count": 0, "total": 0}
    }
    
    for invoice, supplier in invoices:
        # 计算逾期天数
        days_overdue = (as_of_date - invoice.due_date).days
        
        # 分配到对应bucket
        if days_overdue < 0:
            bucket_key = "current"
        elif days_overdue <= 30:
            bucket_key = "1-30"
        elif days_overdue <= 60:
            bucket_key = "31-60"
        elif days_overdue <= 90:
            bucket_key = "61-90"
        else:
            bucket_key = "over-90"
        
        invoice_data = {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "days_overdue": days_overdue,
            "balance_amount": float(invoice.balance_amount),
            "supplier_code": supplier.supplier_code,
            "supplier_name": supplier.supplier_name
        }
        
        buckets[bucket_key]["invoices"].append(invoice_data)
        buckets[bucket_key]["count"] += 1
        buckets[bucket_key]["total"] += float(invoice.balance_amount)
    
    # 计算总计
    total_count = sum(b["count"] for b in buckets.values())
    total_amount = sum(b["total"] for b in buckets.values())
    
    return {
        "company_id": company_id,
        "as_of_date": as_of_date.isoformat(),
        "buckets": buckets,
        "summary": {
            "total_invoices": total_count,
            "total_amount": total_amount
        }
    }


@router.get("/{invoice_id}")
def get_invoice_detail(
    invoice_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    获取发票详情
    
    包含供应商信息、会计分录信息
    """
    invoice = db.query(PurchaseInvoice).filter(
        PurchaseInvoice.id == invoice_id,
        PurchaseInvoice.company_id == company_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    
    supplier = db.query(Supplier).filter(Supplier.id == invoice.supplier_id).first()
    
    return {
        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "total_amount": float(invoice.total_amount),
            "paid_amount": float(invoice.paid_amount),
            "balance_amount": float(invoice.balance_amount),
            "status": invoice.status,
            "journal_entry_id": invoice.journal_entry_id,
            "notes": invoice.notes,
            "created_at": invoice.created_at.isoformat()
        },
        "supplier": {
            "id": supplier.id,
            "supplier_code": supplier.supplier_code,
            "supplier_name": supplier.supplier_name,
            "contact_person": supplier.contact_person,
            "phone": supplier.phone,
            "email": supplier.email,
            "payment_terms": supplier.payment_terms
        } if supplier else None
    }


@router.post("/{invoice_id}/mark-paid")
def mark_invoice_paid(
    invoice_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    标记发票为已支付
    
    更新status为paid，更新paid_amount和balance_amount
    """
    invoice = db.query(PurchaseInvoice).filter(
        PurchaseInvoice.id == invoice_id,
        PurchaseInvoice.company_id == company_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    
    invoice.paid_amount = invoice.total_amount
    invoice.balance_amount = 0
    invoice.status = 'paid'
    
    db.commit()
    
    return {
        "success": True,
        "invoice_id": invoice.id,
        "status": invoice.status,
        "message": f"发票 {invoice.invoice_number} 已标记为已支付"
    }


# ========== 使用示例 ==========

"""
在main.py中注册路由:

from accounting_app.routes import supplier_invoices

app.include_router(supplier_invoices.router, prefix="/api")

然后可以访问:
- POST /api/supplier-invoices/upload - 上传发票
- GET /api/supplier-invoices/list - 列出发票
- GET /api/supplier-invoices/aging-report - 账龄报表
- GET /api/supplier-invoices/{id} - 发票详情
- POST /api/supplier-invoices/{id}/mark-paid - 标记已支付
"""
