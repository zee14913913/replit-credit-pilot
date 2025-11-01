"""
智能导入路由 - 自动识别CSV文件信息
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
import csv
import io
from datetime import datetime
from decimal import Decimal

from ..db import get_db
from ..models import BankStatement, Company
from ..services.bank_matcher import auto_match_transactions
from ..services.statement_analyzer import analyze_csv_content
import os

router = APIRouter()


@router.post("/smart-upload")
async def smart_upload_statement(
    file: UploadFile = File(...),
    company_id: int = None,
    db: Session = Depends(get_db)
):
    """
    智能上传银行月结单
    自动识别银行、账号、月份等信息
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")
    
    # 读取文件内容
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    # 智能分析CSV内容
    analysis = analyze_csv_content(csv_content)
    
    if analysis["confidence"] < 0.3:
        return {
            "success": False,
            "message": "无法识别文件信息，置信度过低",
            "analysis": analysis,
            "suggestion": "请手动指定公司ID、银行名称、账号和月份"
        }
    
    # 如果没有指定company_id，使用默认公司
    if not company_id:
        default_company = db.query(Company).filter(Company.company_code == 'DEFAULT').first()
        if default_company:
            company_id = default_company.id
        else:
            raise HTTPException(status_code=400, detail="未找到默认公司，请指定company_id")
    
    # 提取识别的信息
    bank_name = analysis.get("bank_name") or "Unknown Bank"
    account_number = analysis.get("account_number") or "Unknown"
    statement_month = analysis.get("statement_month")
    
    if not statement_month:
        raise HTTPException(status_code=400, detail="无法识别月份，请确保CSV包含日期列")
    
    # 保存原始CSV文件
    storage_dir = "/home/runner/workspace/accounting_data/statements"
    os.makedirs(storage_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"company{company_id}_{bank_name}_{account_number}_{statement_month}_{timestamp}.csv"
    file_path = os.path.join(storage_dir, safe_filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    # 导入到数据库
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    imported_count = 0
    
    for row in csv_reader:
        try:
            transaction_date = datetime.strptime(row.get('Date', ''), '%Y-%m-%d').date()
            description = row.get('Description', '').strip()
            debit_amount = Decimal(row.get('Debit', '0') or '0')
            credit_amount = Decimal(row.get('Credit', '0') or '0')
            balance = Decimal(row.get('Balance', '0') or '0') if row.get('Balance') else None
            reference = row.get('Reference', '')
            
            bank_stmt = BankStatement(
                company_id=company_id,
                bank_name=bank_name,
                account_number=account_number,
                statement_month=statement_month,
                transaction_date=transaction_date,
                description=description,
                reference_number=reference,
                debit_amount=debit_amount,
                credit_amount=credit_amount,
                balance=balance,
                matched=False
            )
            
            db.add(bank_stmt)
            imported_count += 1
            
        except Exception as e:
            print(f"跳过无效行: {row}, 错误: {e}")
            continue
    
    db.commit()
    
    # 自动匹配交易
    matched_count = auto_match_transactions(db, company_id, statement_month)
    
    return {
        "success": True,
        "message": f"智能识别成功！导入 {imported_count} 笔交易，自动匹配 {matched_count} 笔",
        "analysis": analysis,
        "imported": imported_count,
        "matched": matched_count,
        "file_saved": file_path,
        "identified_info": {
            "company_id": company_id,
            "bank_name": bank_name,
            "account_number": account_number,
            "statement_month": statement_month
        }
    }
