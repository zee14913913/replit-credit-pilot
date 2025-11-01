"""
PDF财务报表API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..db import get_db
from ..services.pdf_report_generator import create_pdf_generator
from ..services.management_report_generator import ManagementReportGenerator
from ..services.file_storage_manager import AccountingFileStorageManager
from ..models import Company
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports/pdf", tags=["PDF Reports"])


@router.get("/balance-sheet")
async def get_balance_sheet_pdf(
    company_id: int = Query(1, description="公司ID"),
    period: str = Query(..., description="期间（YYYY-MM-DD），例如：2025-11-30"),
    db: Session = Depends(get_db)
):
    """
    生成资产负债表PDF
    
    ## 参数
    - company_id: 公司ID
    - period: 报表截止日期（例如：2025-11-30）
    
    ## 返回
    - PDF文件（application/pdf）
    """
    try:
        logger.info(f"生成Balance Sheet PDF: company_id={company_id}, period={period}")
        
        # 获取公司信息
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="公司不存在")
        
        # 生成报表数据
        report_generator = ManagementReportGenerator(db, company_id)
        
        # 将YYYY-MM-DD转换为YYYY-MM
        period_str = period[:7]  # 取前7位
        report_data = report_generator.generate_monthly_report(period_str, include_details=False)
        
        # 生成PDF
        pdf_generator = create_pdf_generator(
            company_name=company.company_name,
            company_code=company.company_code
        )
        
        pdf_bytes = pdf_generator.generate_balance_sheet(
            bs_data=report_data['balance_sheet_summary'],
            period=period
        )
        
        # 自动保存PDF到FileStorageManager（归档）
        as_of_date = datetime.strptime(period, '%Y-%m-%d').date()
        pdf_path = AccountingFileStorageManager.generate_balance_sheet_path(
            company_id=company_id,
            as_of_date=as_of_date,
            file_extension='pdf'
        )
        AccountingFileStorageManager.save_file_content(pdf_path, pdf_bytes)
        logger.info(f"Balance Sheet PDF已保存到: {pdf_path}")
        
        # 返回PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Balance_Sheet_{company.company_code}_{period}.pdf"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成Balance Sheet PDF失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/profit-loss")
async def get_profit_loss_pdf(
    company_id: int = Query(1, description="公司ID"),
    period: str = Query(..., description="期间（YYYY-MM），例如：2025-11"),
    db: Session = Depends(get_db)
):
    """
    生成损益表PDF
    
    ## 参数
    - company_id: 公司ID
    - period: 报表期间（例如：2025-11）
    
    ## 返回
    - PDF文件（application/pdf）
    """
    try:
        logger.info(f"生成P&L PDF: company_id={company_id}, period={period}")
        
        # 获取公司信息
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="公司不存在")
        
        # 生成报表数据
        report_generator = ManagementReportGenerator(db, company_id)
        report_data = report_generator.generate_monthly_report(period, include_details=False)
        
        # 生成PDF
        pdf_generator = create_pdf_generator(
            company_name=company.company_name,
            company_code=company.company_code
        )
        
        pdf_bytes = pdf_generator.generate_profit_loss(
            pnl_data=report_data['pnl_summary'],
            period=period
        )
        
        # 自动保存PDF到FileStorageManager（归档）
        from datetime import date as date_class
        year, month = period.split('-')
        period_start = date_class(int(year), int(month), 1)
        # 使用月末作为period_end
        import calendar
        last_day = calendar.monthrange(int(year), int(month))[1]
        period_end = date_class(int(year), int(month), last_day)
        
        pdf_path = AccountingFileStorageManager.generate_profit_loss_path(
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            file_extension='pdf'
        )
        AccountingFileStorageManager.save_file_content(pdf_path, pdf_bytes)
        logger.info(f"P&L PDF已保存到: {pdf_path}")
        
        # 返回PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Profit_Loss_{company.company_code}_{period}.pdf"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成P&L PDF失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/bank-package")
async def get_bank_package_pdf(
    company_id: int = Query(1, description="公司ID"),
    period: str = Query(..., description="期间（YYYY-MM），例如：2025-11"),
    db: Session = Depends(get_db)
):
    """
    生成完整银行贷款包PDF
    
    包含：
    1. 封面
    2. Balance Sheet
    3. P&L Statement
    4. Aging Report Summary
    5. Bank Account Balances
    6. Data Quality Metrics
    
    ## 参数
    - company_id: 公司ID
    - period: 报表期间（例如：2025-11）
    
    ## 返回
    - PDF文件（application/pdf）
    """
    try:
        logger.info(f"生成Bank Package PDF: company_id={company_id}, period={period}")
        
        # 获取公司信息
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="公司不存在")
        
        # 生成完整报表数据
        report_generator = ManagementReportGenerator(db, company_id)
        report_data = report_generator.generate_monthly_report(period, include_details=True)
        
        # 生成PDF
        pdf_generator = create_pdf_generator(
            company_name=company.company_name,
            company_code=company.company_code
        )
        
        pdf_bytes = pdf_generator.generate_bank_package(
            report_data=report_data,
            period=period
        )
        
        # 自动保存PDF到FileStorageManager（归档）
        from datetime import date as date_class
        year, month = period.split('-')
        import calendar
        last_day = calendar.monthrange(int(year), int(month))[1]
        package_date = date_class(int(year), int(month), last_day)
        
        pdf_path = AccountingFileStorageManager.generate_bank_package_path(
            company_id=company_id,
            package_date=package_date,
            file_extension='pdf'
        )
        AccountingFileStorageManager.save_file_content(pdf_path, pdf_bytes)
        logger.info(f"Bank Package PDF已保存到: {pdf_path}")
        
        # 返回PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Bank_Package_{company.company_code}_{period}.pdf"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成Bank Package PDF失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/preview/{report_type}")
async def preview_report_structure(
    report_type: str,
    company_id: int = Query(1, description="公司ID"),
    period: str = Query("2025-11", description="期间"),
    db: Session = Depends(get_db)
):
    """
    预览报表数据结构（JSON格式）
    
    用于调试和验证报表数据
    
    ## 参数
    - report_type: 报表类型（balance_sheet / profit_loss / full）
    - company_id: 公司ID
    - period: 报表期间
    
    ## 返回
    - JSON数据结构
    """
    try:
        # 获取公司信息
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="公司不存在")
        
        # 生成报表数据
        report_generator = ManagementReportGenerator(db, company_id)
        report_data = report_generator.generate_monthly_report(period, include_details=True)
        
        # 根据类型返回
        if report_type == "balance_sheet":
            return {
                "company": {
                    "name": company.company_name,
                    "code": company.company_code
                },
                "period": period,
                "data": report_data['balance_sheet_summary']
            }
        elif report_type == "profit_loss":
            return {
                "company": {
                    "name": company.company_name,
                    "code": company.company_code
                },
                "period": period,
                "data": report_data['pnl_summary']
            }
        elif report_type == "full":
            return {
                "company": {
                    "name": company.company_name,
                    "code": company.company_code
                },
                "period": period,
                "data": report_data
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="无效的报表类型。支持: balance_sheet, profit_loss, full"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览报表数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
