"""
POS日报API路由
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from typing import List, Optional
from datetime import date
import logging

from ..db import get_db
# from ..middleware.multi_tenant import get_current_company
from ..services.pos_processor import create_pos_processor
from ..models import POSReport, POSTransaction, SalesInvoice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pos-reports", tags=["POS Reports"])


@router.post("/upload")
async def upload_pos_report(
    file: UploadFile = File(...),
    company_id: int = Query(1, description="公司ID"),
    auto_generate_invoices: bool = Query(True, description="是否自动生成销售发票"),
    db=Depends(get_db)
):
    """
    上传POS日报
    
    ## 支持的文件格式
    - PDF (自动OCR)
    - Excel/CSV (结构化数据)
    
    ## 自动处理流程
    1. **解析POS数据**：自动识别日期、金额、客户、支付方式
    2. **重复检测**：检查是否已存在相同日期和金额的报表
    3. **客户匹配**：智能匹配客户名称
    4. **生成销售发票**：为匹配到客户的交易自动生成发票
    5. **会计分录**：借：应收账款，贷：销售收入
    6. **AR Aging**：自动更新应收账款账龄
    
    ## 返回数据
    - pos_report_id: POS报表ID
    - report_number: 报表编号
    - total_sales: 总销售额
    - generated_invoices: 生成的发票数量
    - matched_customers: 匹配到客户的交易数
    - unmatched_transactions: 未匹配客户的交易数
    """
    try:
        logger.info(f"收到POS报表上传: company_id={company_id}, file={file.filename}")
        
        # 验证文件类型
        supported_extensions = ('.pdf', '.xlsx', '.xls', '.csv')
        if not file.filename.lower().endswith(supported_extensions):
            raise HTTPException(
                status_code=415, 
                detail=f"不支持的文件类型。支持格式: {', '.join(supported_extensions)}"
            )
        
        # 读取文件内容
        file_content = await file.read()
        
        # 处理POS文件
        processor = create_pos_processor(db)
        result = processor.process_pos_file(
            company_id=company_id,
            file_content=file_content,
            file_name=file.filename,
            auto_generate_invoices=auto_generate_invoices
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "POS文件处理失败")
            )
        
        return {
            "message": "POS报表上传成功",
            **result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POS报表上传失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/")
async def list_pos_reports(
    company_id: int = Query(1, description="公司ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_db)
):
    """
    获取POS报表列表
    
    支持日期范围筛选
    """
    try:
        query = db.query(POSReport).filter(POSReport.company_id == company_id)
        
        if start_date:
            query = query.filter(POSReport.report_date >= start_date)
        
        if end_date:
            query = query.filter(POSReport.report_date <= end_date)
        
        # 按日期倒序
        query = query.order_by(POSReport.report_date.desc())
        
        total = query.count()
        reports = query.offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "reports": [
                {
                    "id": r.id,
                    "report_number": r.report_number,
                    "report_date": r.report_date.isoformat(),
                    "total_sales": float(r.total_sales),
                    "total_transactions": r.total_transactions,
                    "payment_method": r.payment_method,
                    "auto_generated_invoices": r.auto_generated_invoices,
                    "parse_status": r.parse_status,
                    "created_at": r.created_at.isoformat()
                }
                for r in reports
            ]
        }
    
    except Exception as e:
        logger.error(f"获取POS报表列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/{report_id}")
async def get_pos_report_detail(
    report_id: int,
    company_id: int = Query(1, description="公司ID"),
    db=Depends(get_db)
):
    """
    获取POS报表详情
    
    包含所有交易明细
    """
    try:
        # 查询报表
        report = db.query(POSReport).filter(
            POSReport.id == report_id,
            POSReport.company_id == company_id
        ).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="POS报表不存在")
        
        # 查询交易明细
        transactions = db.query(POSTransaction).filter(
            POSTransaction.pos_report_id == report_id
        ).all()
        
        return {
            "id": report.id,
            "report_number": report.report_number,
            "report_date": report.report_date.isoformat(),
            "total_sales": float(report.total_sales),
            "total_transactions": report.total_transactions,
            "payment_method": report.payment_method,
            "auto_generated_invoices": report.auto_generated_invoices,
            "parse_status": report.parse_status,
            "created_at": report.created_at.isoformat(),
            "transactions": [
                {
                    "id": t.id,
                    "transaction_time": t.transaction_time.isoformat(),
                    "transaction_amount": float(t.transaction_amount),
                    "customer_id": t.customer_id,
                    "customer_name_raw": t.customer_name_raw,
                    "payment_method": t.payment_method,
                    "sales_invoice_id": t.sales_invoice_id,
                    "matched": t.matched
                }
                for t in transactions
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取POS报表详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/{report_id}/invoices")
async def get_generated_invoices(
    report_id: int,
    company_id: int = Query(1, description="公司ID"),
    db=Depends(get_db)
):
    """
    获取该POS报表生成的所有销售发票
    """
    try:
        # 验证报表存在
        report = db.query(POSReport).filter(
            POSReport.id == report_id,
            POSReport.company_id == company_id
        ).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="POS报表不存在")
        
        # 查询生成的发票
        transactions = db.query(POSTransaction).filter(
            POSTransaction.pos_report_id == report_id,
            POSTransaction.sales_invoice_id.isnot(None)
        ).all()
        
        invoice_ids = [t.sales_invoice_id for t in transactions]
        
        invoices = db.query(SalesInvoice).filter(
            SalesInvoice.id.in_(invoice_ids)
        ).all()
        
        return {
            "report_id": report_id,
            "report_number": report.report_number,
            "total_invoices": len(invoices),
            "invoices": [
                {
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "customer_id": inv.customer_id,
                    "invoice_date": inv.invoice_date.isoformat(),
                    "due_date": inv.due_date.isoformat(),
                    "total_amount": float(inv.total_amount),
                    "balance_amount": float(inv.balance_amount),
                    "status": inv.status,
                    "auto_generated": inv.auto_generated
                }
                for inv in invoices
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取生成的发票失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/batch-upload")
async def batch_upload_pos_reports(
    files: List[UploadFile] = File(...),
    company_id: int = Query(1, description="公司ID"),
    auto_generate_invoices: bool = Query(True),
    db=Depends(get_db)
):
    """
    批量上传POS报表
    
    最多支持20个文件同时上传
    """
    if len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail="批量上传最多支持20个文件"
        )
    
    results = []
    processor = create_pos_processor(db)
    
    for file in files:
        try:
            logger.info(f"批量上传: {file.filename}")
            
            file_content = await file.read()
            
            result = processor.process_pos_file(
                company_id=company_id,
                file_content=file_content,
                file_name=file.filename,
                auto_generate_invoices=auto_generate_invoices
            )
            
            results.append({
                "filename": file.filename,
                "success": result["success"],
                "data": result if result["success"] else None,
                "error": result.get("error") if not result["success"] else None
            })
        
        except Exception as e:
            logger.error(f"文件 {file.filename} 处理失败: {str(e)}")
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    
    return {
        "total_files": len(files),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }
