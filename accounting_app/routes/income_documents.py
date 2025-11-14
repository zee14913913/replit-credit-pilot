"""
Income Document System - 客户收入证明文件管理
处理工资单、税单、EPF报表、银行流水等收入证明文件
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os
import re
from datetime import datetime

from ..db import get_db
from ..services.file_storage_manager import AccountingFileStorageManager
from ..services.raw_document_service import RawDocumentService
from ..services.unified_file_service import UnifiedFileService
from ..services.pdf_parser import PDFParser
from ..utils.file_hash import calculate_uploaded_file_hash
from ..models import Customer

router = APIRouter(prefix="/api/income-documents", tags=["Income Documents"])


@router.post("/upload")
async def upload_income_document(
    customer_id: int = Form(...),
    document_type: str = Form(...),
    document_month: str = Form(...),
    file: UploadFile = File(...),
    company_id: int = Form(1),
    db: Session = Depends(get_db)
):
    """
    上传客户收入证明文件
    
    Args:
        customer_id: 客户ID
        document_type: 文件类型 (salary_slip/tax_return/epf/bank_inflow)
        document_month: 收入月份 (YYYY-MM)
        file: 上传的文件
        company_id: 公司ID（默认1）
    
    Returns:
        上传结果，包含OCR提取的收入金额
    """
    
    try:
        # 1. 验证客户存在
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail=f"客户ID {customer_id} 不存在")
        
        # 2. 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 3. 计算文件hash
        await file.seek(0)
        file_hash = calculate_uploaded_file_hash(file.file)
        
        # 4. 生成存储路径（收入文件专用目录）
        year, month = document_month.split('-')
        sanitized_filename = AccountingFileStorageManager.sanitize_filename(file.filename)
        
        storage_path = os.path.join(
            AccountingFileStorageManager.BASE_DIR,
            str(company_id),
            'income_documents',
            str(customer_id),
            year,
            month,
            f"{document_type}_{sanitized_filename}"
        )
        storage_path = storage_path.replace('\\', '/')
        
        # 5. 保存文件到磁盘
        AccountingFileStorageManager.ensure_directory(storage_path)
        with open(storage_path, 'wb') as f:
            f.write(file_content)
        
        # 6. 创建RawDocument原件记录
        raw_doc_service = RawDocumentService(db)
        raw_doc = raw_doc_service.create_raw_document(
            company_id=company_id,
            file_name=file.filename,
            storage_path=storage_path,
            file_hash=file_hash,
            file_size=file_size,
            source_engine='fastapi',
            module='income',
            uploaded_by=None
        )
        
        # 7. OCR解析，提取收入金额
        parser = PDFParser(enable_ocr=True, ocr_language='eng+chi_sim')
        parse_result = parser.parse(storage_path)
        
        # 8. 提取收入金额（从OCR结果或文本中）
        extracted_income = 0.0
        confidence = parse_result.confidence
        ocr_method = parse_result.method
        raw_text = parse_result.text_content
        
        if parse_result.success:
            extracted_income = _extract_income_amount(
                parse_result.text_content,
                parse_result.extracted_data,
                document_type
            )
        
        # 9. 注册到file_index统一索引
        file_size_kb = int(file_size / 1024)
        
        file_index = UnifiedFileService.register_file(
            db=db,
            company_id=company_id,
            filename=file.filename,
            file_path=storage_path,
            module='income',
            from_engine='fastapi',
            file_size_kb=file_size_kb,
            validation_status='pending',
            status='active',
            period=document_month,
            raw_document_id=raw_doc.id,
            metadata={
                'customer_id': customer_id,
                'customer_name': customer.name,
                'document_type': document_type,
                'income_detected': extracted_income,
                'ocr_confidence': confidence,
                'ocr_method': ocr_method
            }
        )
        
        # 10. 返回结果
        return {
            "status": "success",
            "message": "收入文件上传成功",
            "file_id": file_index.id,
            "raw_document_id": raw_doc.id,
            "customer_id": customer_id,
            "customer_name": customer.name,
            "document_type": document_type,
            "document_month": document_month,
            "storage_path": storage_path,
            "ocr_result": {
                "income_detected": extracted_income,
                "confidence": confidence,
                "method": ocr_method,
                "text_length": len(raw_text)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"上传失败: {str(e)}"
        )


@router.get("/customer/{customer_id}")
async def get_customer_income_documents(
    customer_id: int,
    company_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    获取客户的所有收入文件
    """
    from ..models import FileIndex
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户ID {customer_id} 不存在")
    
    files = db.query(FileIndex).filter(
        FileIndex.company_id == company_id,
        FileIndex.module == 'income',
        FileIndex.is_active == True
    ).order_by(FileIndex.upload_date.desc()).all()
    
    results = []
    for file in files:
        metadata = file.metadata or {}
        if metadata.get('customer_id') == customer_id:
            results.append({
                "file_id": file.id,
                "filename": file.filename,
                "document_type": metadata.get('document_type', 'unknown'),
                "document_month": file.period,
                "income_detected": metadata.get('income_detected', 0),
                "ocr_confidence": metadata.get('ocr_confidence', 0),
                "uploaded_at": file.upload_date.isoformat() if file.upload_date else None,
                "status": file.status
            })
    
    return {
        "customer_id": customer_id,
        "customer_name": customer.name,
        "total_files": len(results),
        "files": results
    }


def _extract_income_amount(text: str, extracted_data: dict, document_type: str) -> float:
    """
    从OCR文本中提取收入金额
    
    Args:
        text: OCR提取的文本
        extracted_data: PDFParser返回的结构化数据
        document_type: 文件类型
    
    Returns:
        提取的收入金额（RM）
    """
    if not text:
        return 0.0
    
    try:
        if document_type == 'salary_slip':
            patterns = [
                r'(?:Net\s+Salary|Net\s+Pay|Total\s+Salary|净工资|实发工资)[\s:：]*RM?\s*([\d,]+\.?\d*)',
                r'(?:Gross\s+Salary|Gross\s+Pay|总工资)[\s:：]*RM?\s*([\d,]+\.?\d*)',
                r'(?:Basic\s+Salary|基本工资)[\s:：]*RM?\s*([\d,]+\.?\d*)',
            ]
        elif document_type == 'tax_return':
            patterns = [
                r'(?:Total\s+Income|Aggregate\s+Income|总收入)[\s:：]*RM?\s*([\d,]+\.?\d*)',
                r'(?:Statutory\s+Income|应税收入)[\s:：]*RM?\s*([\d,]+\.?\d*)',
            ]
        elif document_type == 'epf':
            patterns = [
                r'(?:Employee\s+Contribution|员工缴纳)[\s:：]*RM?\s*([\d,]+\.?\d*)',
                r'(?:Monthly\s+Wages|月工资)[\s:：]*RM?\s*([\d,]+\.?\d*)',
            ]
        elif document_type == 'bank_inflow':
            patterns = [
                r'(?:Credit|Deposit|存入|入账)[\s:：]*RM?\s*([\d,]+\.?\d*)',
            ]
        else:
            patterns = [
                r'RM\s*([\d,]+\.?\d*)',
                r'([\d,]+\.?\d*)\s*RM',
            ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                amount = float(amount_str)
                if 100 <= amount <= 1000000:
                    return amount
        
        return 0.0
        
    except Exception as e:
        return 0.0
