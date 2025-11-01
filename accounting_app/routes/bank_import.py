"""
银行月结单导入路由
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from datetime import datetime
from decimal import Decimal

from ..db import get_db
from ..models import BankStatement, JournalEntry, JournalEntryLine, ChartOfAccounts
from ..schemas import BankStatementResponse
from ..services.bank_matcher import auto_match_transactions

router = APIRouter()


@router.post("/bank-statement")
async def import_bank_statement(
    company_id: int,
    bank_name: str,
    account_number: str,
    statement_month: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入银行月结单CSV
    
    CSV格式要求:
    Date,Description,Debit,Credit,Balance
    2025-01-01,SALARY PAYMENT,5000.00,0.00,15000.00
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # 读取CSV文件
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    # 保存上传的CSV文件到统一位置
    import os
    from datetime import datetime
    storage_dir = "/home/runner/workspace/accounting_data/statements"
    os.makedirs(storage_dir, exist_ok=True)
    
    # 生成文件名：公司ID_银行_账号_月份_上传时间.csv
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"company{company_id}_{bank_name}_{account_number}_{statement_month}_{timestamp}.csv"
    file_path = os.path.join(storage_dir, safe_filename)
    
    # 保存文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    
    imported_count = 0
    matched_count = 0
    
    for row in csv_reader:
        # 解析CSV行
        try:
            transaction_date = datetime.strptime(row.get('Date', ''), '%Y-%m-%d').date()
            description = row.get('Description', '').strip()
            debit_amount = Decimal(row.get('Debit', '0') or '0')
            credit_amount = Decimal(row.get('Credit', '0') or '0')
            balance = Decimal(row.get('Balance', '0') or '0') if row.get('Balance') else None
            reference = row.get('Reference', '')
            
            # 创建bank_statement记录
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
    
    # 自动匹配交易并生成分录
    matched_count = auto_match_transactions(db, company_id, statement_month)
    
    return {
        "success": True,
        "imported": imported_count,
        "matched": matched_count,
        "file_saved": file_path,
        "message": f"成功导入 {imported_count} 笔银行流水，自动匹配 {matched_count} 笔。文件已保存至: {file_path}"
    }


@router.get("/bank-statements")
def get_bank_statements(
    company_id: int,
    statement_month: str = None,
    matched: bool = None,
    db: Session = Depends(get_db)
) -> List[BankStatementResponse]:
    """
    获取银行流水
    """
    query = db.query(BankStatement).filter(BankStatement.company_id == company_id)
    
    if statement_month:
        query = query.filter(BankStatement.statement_month == statement_month)
    
    if matched is not None:
        query = query.filter(BankStatement.matched == matched)
    
    statements = query.order_by(BankStatement.transaction_date.desc()).all()
    return statements
