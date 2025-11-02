"""
银行月结单导入路由
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import csv
import io
import hashlib
from datetime import datetime
from decimal import Decimal

from ..db import get_db
from ..models import BankStatement, JournalEntry, JournalEntryLine, ChartOfAccounts, RawDocument, RawLine, Exception as ExceptionModel
from ..schemas import BankStatementResponse
from ..schemas.validators import validate_yyyy_mm
from ..services.bank_matcher import auto_match_transactions
from ..services.statement_analyzer import analyze_csv_content, suggest_customer_match
from ..services.file_storage_manager import AccountingFileStorageManager

router = APIRouter()


@router.post("/bank-statement", 
    summary="导入银行月结单CSV",
    description="""
    导入银行月结单CSV文件，执行严格的数据验证并自动生成会计分录。
    
    **数据完整性保证（1:1原件保护）：**
    - 所有上传文件都会保存到文件系统（包括验证失败的文件）
    - 每行CSV原文保存到raw_lines表，确保100%可追溯
    - 验证失败时完全回滚，不插入任何业务记录（全部或无原则）
    
    **CSV格式要求：**
    ```csv
    Date,Description,Debit,Credit,Balance
    2025-01-01,SALARY PAYMENT,5000.00,0.00,15000.00
    2025-01-02,OFFICE RENT,0.00,2000.00,13000.00
    ```
    
    **必填字段验证规则：**
    - ✅ Date: 必填，格式YYYY-MM-DD（例如：2025-01-15）
    - ✅ Description: 必填，不能为空
    - ⚠️ Debit/Credit: 可选，默认0.00
    - ⚠️ Balance: 可选
    
    **数据验证策略（禁止自动补数据）：**
    - 系统不会自动生成或补充任何缺失的数据
    - 任何一行缺失必填字段，整个文件验证失败
    - 验证失败时，文件已保存但不会创建任何bank_statements记录
    - 验证成功后，自动执行规则匹配并生成会计分录
    
    **响应说明：**
    - HTTP 200: 导入成功，返回导入和匹配数量
    - HTTP 400: 参数错误（月份格式错误或非CSV文件）
    - HTTP 422: 数据验证失败（返回详细错误列表）
    """,
    responses={
        200: {
            "description": "导入成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "imported": 21,
                        "matched": 21,
                        "file_saved": "/path/to/file.csv",
                        "raw_document_id": 1,
                        "message": "成功导入 21 笔银行流水，自动匹配 21 笔"
                    }
                }
            }
        },
        422: {
            "description": "数据验证失败",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": "数据验证失败",
                            "message": "文件已保存但验证失败。共4行，2行有错误。",
                            "file_saved": "/path/to/file.csv",
                            "validation_errors": [
                                "第2行验证失败: 缺失必填字段 'Date'",
                                "第3行验证失败: 缺失必填字段 'Description'"
                            ],
                            "total_errors": 2
                        }
                    }
                }
            }
        }
    }
)
async def import_bank_statement(
    company_id: int = Query(..., description="公司ID", example=1),
    bank_name: str = Query(..., description="银行名称", example="Maybank"),
    account_number: str = Query(..., description="银行账号", example="1234567890"),
    statement_month: str = Query(..., description="月份（格式：YYYY-MM）", example="2025-01"),
    file: UploadFile = File(..., description="银行月结单CSV文件"),
    db: Session = Depends(get_db)
):
    """
    导入银行月结单CSV（严格数据验证，禁止自动补数据）
    """
    # 验证月份格式
    try:
        statement_month = validate_yyyy_mm(statement_month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # 读取CSV文件
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    # 计算文件哈希
    file_hash = hashlib.sha256(content).hexdigest()
    
    # 使用FileStorageManager保存CSV文件（多租户隔离）
    file_path = AccountingFileStorageManager.generate_bank_statement_path(
        company_id=company_id,
        bank_name=bank_name,
        account_number=account_number,
        statement_month=statement_month,
        file_extension='csv'
    )
    
    # 保存文件
    AccountingFileStorageManager.save_text_content(file_path, csv_content)
    
    # Step 1: 创建raw_document记录（原件追踪）
    raw_doc = RawDocument(
        company_id=company_id,
        file_name=file.filename,
        file_hash=file_hash,
        file_size=len(content),
        storage_path=file_path,
        source_engine='fastapi',
        module='bank',
        status='uploaded',
        validation_status='pending'
    )
    db.add(raw_doc)
    db.flush()  # 获取raw_doc.id
    
    # Step 2: 解析CSV并保存每行原文到raw_lines（暂不commit）
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    validation_errors = []
    raw_lines = []
    line_no = 1  # CSV行号（不含header）
    
    for row in csv_reader:
        # 将整行转为字符串保存原文
        raw_text = str(row)
        
        # 创建raw_line记录
        raw_line = RawLine(
            raw_document_id=raw_doc.id,
            line_no=line_no,
            raw_text=raw_text,
            is_parsed=False
        )
        db.add(raw_line)
        db.flush()  # 获取raw_line.id
        raw_lines.append((raw_line, row))
        line_no += 1
    
    # 注意：此处不commit，等验证通过后再commit
    
    # Step 3: 严格验证每行数据（禁止自动补数据）
    # 使用临时列表，验证全部通过后才批量插入（保证全部或无）
    validated_statements = []
    imported_count = 0
    
    for raw_line, row in raw_lines:
        line_errors = []
        
        # 必填字段验证：Date
        date_str = row.get('Date', '').strip()
        if not date_str:
            line_errors.append(f"缺失必填字段 'Date'")
        else:
            try:
                transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                line_errors.append(f"Date格式错误（应为YYYY-MM-DD）: {date_str}")
        
        # 必填字段验证：Description
        description = row.get('Description', '').strip()
        if not description:
            line_errors.append(f"缺失必填字段 'Description'")
        
        # 如果有验证错误，记录并跳过该行
        if line_errors:
            error_msg = f"第{raw_line.line_no}行验证失败: {'; '.join(line_errors)}"
            validation_errors.append(error_msg)
            continue
        
        # 验证通过，解析可选字段（不自动补0）
        try:
            debit_str = row.get('Debit', '').strip()
            credit_str = row.get('Credit', '').strip()
            balance_str = row.get('Balance', '').strip()
            
            debit_amount = Decimal(debit_str) if debit_str else Decimal('0')
            credit_amount = Decimal(credit_str) if credit_str else Decimal('0')
            balance = Decimal(balance_str) if balance_str else None
            reference = row.get('Reference', '').strip()
            
            # 暂存到临时列表（不立即添加到db）
            validated_statements.append({
                'raw_line': raw_line,
                'transaction_date': transaction_date,
                'description': description,
                'debit_amount': debit_amount,
                'credit_amount': credit_amount,
                'balance': balance,
                'reference': reference
            })
            imported_count += 1
            
        except Exception as e:
            validation_errors.append(f"第{raw_line.line_no}行解析失败: {str(e)}")
            continue
    
    # Step 4: 处理验证结果
    if validation_errors:
        # 验证失败：直接更新已flush的raw_document和raw_lines状态（不rollback！）
        # 这确保真正的单一事务，避免rollback+recreate的gap window
        raw_doc.status = 'failed'
        raw_doc.validation_status = 'failed'
        raw_doc.validation_failed_at = datetime.now()
        raw_doc.validation_error_message = "\n".join(validation_errors)
        raw_doc.total_lines = len(raw_lines)
        raw_doc.parsed_lines = 0
        
        # raw_lines已经存在并flush，无需重新创建
        # 它们的is_parsed=False已经正确表示验证失败
        
        # 创建异常记录（直接在当前事务中）
        # exception + raw_document + raw_lines 在同一原子事务中commit
        import json
        exception_record = ExceptionModel(
            company_id=company_id,
            exception_type='pdf_parse',  # CSV验证失败归类为文件解析错误
            severity='high',
            source_type='bank_import',
            source_id=raw_doc.id,
            error_message=f"CSV验证失败：{len(validation_errors)}个错误",
            raw_data=json.dumps({
                'file_name': file.filename,
                'total_lines': len(raw_lines),
                'imported': imported_count,
                'errors': validation_errors
            }, ensure_ascii=False),
            status='new'
        )
        db.add(exception_record)
        
        # 一次性原子commit（raw_document + raw_lines + exception）
        # 真正的单一事务，无gap window，满足1:1原件保护的原子性要求
        db.commit()
        
        raise HTTPException(
            status_code=422,
            detail={
                "error": "数据验证失败",
                "message": f"文件已保存但验证失败。共{len(raw_lines)}行，{len(validation_errors)}行有错误。",
                "file_saved": file_path,
                "validation_errors": validation_errors[:10],  # 只返回前10个错误
                "total_errors": len(validation_errors)
            }
        )
    
    # 验证成功：批量插入bank_statements（全部或无原则）
    for stmt_data in validated_statements:
        bank_stmt = BankStatement(
            company_id=company_id,
            bank_name=bank_name,
            account_number=account_number,
            statement_month=statement_month,
            transaction_date=stmt_data['transaction_date'],
            description=stmt_data['description'],
            reference_number=stmt_data['reference'],
            debit_amount=stmt_data['debit_amount'],
            credit_amount=stmt_data['credit_amount'],
            balance=stmt_data['balance'],
            matched=False,
            raw_line_id=stmt_data['raw_line'].id
        )
        db.add(bank_stmt)
        stmt_data['raw_line'].is_parsed = True
    
    # 更新raw_document状态
    raw_doc.validation_status = 'passed'
    raw_doc.status = 'parsed'
    raw_doc.parsed_lines = imported_count
    db.commit()
    
    # 自动匹配交易并生成分录
    matched_count = auto_match_transactions(db, company_id, statement_month)
    
    return {
        "success": True,
        "imported": imported_count,
        "matched": matched_count,
        "file_saved": file_path,
        "raw_document_id": raw_doc.id,
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
    
    参数:
        statement_month: 月份格式必须为 YYYY-MM，例如 2025-01（可选）
    """
    # 如果提供了statement_month，验证格式
    if statement_month:
        try:
            statement_month = validate_yyyy_mm(statement_month)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    query = db.query(BankStatement).filter(BankStatement.company_id == company_id)
    
    if statement_month:
        query = query.filter(BankStatement.statement_month == statement_month)
    
    if matched is not None:
        query = query.filter(BankStatement.matched == matched)
    
    statements = query.order_by(BankStatement.transaction_date.desc()).all()
    return statements
