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
from ..services.statement_analyzer import analyze_csv_content, analyze_pdf_content
from ..services.file_storage_manager import AccountingFileStorageManager
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
    支持CSV和PDF格式
    自动识别银行、账号、月份等信息
    """
    # 检查文件格式
    if not (file.filename.endswith('.csv') or file.filename.endswith('.pdf')):
        raise HTTPException(status_code=400, detail="只支持CSV和PDF文件")
    
    # 读取文件内容
    content = await file.read()
    
    # 根据文件类型选择解析方式
    is_pdf = file.filename.endswith('.pdf')
    csv_content = None  # 用于后续导入
    
    if is_pdf:
        # PDF文件 - 保存后解析
        temp_dir = "/tmp/pdf_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # 智能分析PDF内容
        analysis = analyze_pdf_content(temp_path)
        
        # 如果PDF解析成功，获取交易数据
        if analysis.get("transactions"):
            # 将PDF交易转换为CSV格式字符串（用于后续统一处理）
            csv_content = _convert_pdf_transactions_to_csv(analysis["transactions"])
        
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
    else:
        # CSV文件
        from ..services.statement_analyzer import clean_csv_excel_format
        raw_csv = content.decode('utf-8')
        # 清理Excel公式格式（="value" -> value）
        csv_content = clean_csv_excel_format(raw_csv)
        # 智能分析CSV内容
        analysis = analyze_csv_content(csv_content)
    
    if analysis["confidence"] < 0.2:  # 降低阈值从0.3到0.2
        return {
            "success": False,
            "message": "无法识别文件信息，置信度过低",
            "analysis": analysis,
            "suggestion": "请使用手动上传功能，指定公司ID、银行名称、账号和月份"
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
    
    # 检查csv_content是否有效
    if not csv_content:
        raise HTTPException(status_code=400, detail="文件解析失败，无有效数据")
    
    # 保存清理后的CSV文件
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
    
    # 导入辅助函数
    def parse_flexible_date(date_str: str):
        """支持多种日期格式的灵活解析"""
        if not date_str:
            return None
        
        date_formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        return None
    
    for row in csv_reader:
        try:
            # 使用灵活日期解析
            date_str = row.get('Date', '').strip()
            transaction_date = parse_flexible_date(date_str)
            
            if not transaction_date:
                print(f"跳过无效日期行: {date_str}")
                continue
            
            # 支持多种列名
            description = (
                row.get('Description', '') or 
                row.get('Transaction Description', '') or 
                row.get('Particulars', '')
            ).strip()
            
            if not description:
                print(f"跳过无描述行: {row}")
                continue
            
            # 支持Debit/Credit或Withdrawal/Deposit
            debit_str = row.get('Debit', '') or row.get('Withdrawal', '') or '0'
            credit_str = row.get('Credit', '') or row.get('Deposit', '') or '0'
            
            debit_amount = Decimal(debit_str or '0')
            credit_amount = Decimal(credit_str or '0')
            balance = Decimal(row.get('Balance', '0') or '0') if row.get('Balance') else None
            reference = row.get('Reference', '') or row.get('Ref. No.', '')
            
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


def _convert_pdf_transactions_to_csv(transactions: list) -> str:
    """将PDF提取的交易转换为CSV格式字符串"""
    import io
    import csv as csv_module
    
    output = io.StringIO()
    writer = csv_module.DictWriter(output, fieldnames=['Date', 'Description', 'Debit', 'Credit', 'Balance', 'Reference'])
    writer.writeheader()
    
    for txn in transactions:
        writer.writerow({
            'Date': txn.get('date', ''),
            'Description': txn.get('description', ''),
            'Debit': txn.get('debit', 0),
            'Credit': txn.get('credit', 0),
            'Balance': txn.get('balance', ''),
            'Reference': txn.get('reference', '')
        })
    
    return output.getvalue()
