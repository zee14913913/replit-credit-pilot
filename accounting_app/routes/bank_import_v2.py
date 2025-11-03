"""
Phase 1-10: 银行月结单上传接口（V2版本 - 7状态机 + 统一响应格式）

Phase 1-5改进：
- V1: 直接解析CSV并入库
- V2: "先封存，再计算" - 封存原件 → 行数对账 → 验证通过才入库

Phase 1-10改进：
- 统一UploadResponse格式（success & failure都返回）
- 7状态机驱动next_actions
- 扫描版PDF友好消息（bilingual）
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging
from sqlalchemy import and_, or_, text

from ..db import get_db
from ..services.upload_wrapper import BankStatementUploadWrapper
from ..models import FileIndex, RawDocument
from ..schemas.upload_responses import UploadResponse, get_next_actions

router = APIRouter(prefix="/api/v2/import", tags=["Bank Import V2 (Phase 1-10)"])
logger = logging.getLogger(__name__)


@router.post("/bank-statement")
async def import_bank_statement_v2(
    company_id: int,
    bank_name: str,
    account_number: str,
    statement_month: str,
    username: Optional[str] = "system",
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    ## 📋 Phase 1-5: 银行月结单上传（V2版本）
    
    ### 核心改进：
    1. **"先封存，再计算"原则** - 上传文件立即保存到raw_documents
    2. **分块hash计算** - 防止大文件超时
    3. **行数对账验证** - raw_lines行数必须等于解析行数
    4. **部分成功拦截** - 行数不匹配进入异常中心
    
    ### 处理流程（7步骤）：
    1. 封存原件到raw_documents + 计算hash
    2. 写入file_index（强制关联raw_document_id）
    3. 解析CSV内容
    4. 保存逐行记录到raw_lines
    5. 行数对账验证（critical）
    6. 验证通过：创建bank_statement记录
    7. 验证失败：进入异常中心，原件已保护
    
    ### CSV格式要求：
    ```csv
    Date,Description,Debit,Credit,Balance,Reference
    2025-01-01,SALARY PAYMENT,5000.00,0.00,15000.00,REF123
    ```
    
    ### 返回数据：
    - **success=True**: 全部成功，返回imported和matched数量
    - **success=False, partial_success=True**: 文件已封存但行数对账失败
    - **success=False**: 上传或解析失败
    
    ### 示例：
    ```bash
    curl -X POST "http://localhost:8000/api/v2/import/bank-statement" \\
      -F "file=@statement.csv" \\
      -F "company_id=1" \\
      -F "bank_name=Maybank" \\
      -F "account_number=1234567890" \\
      -F "statement_month=2025-01"
    ```
    """
    logger.info(
        f"收到银行月结单上传请求 - "
        f"company_id={company_id}, bank={bank_name}, month={statement_month}"
    )
    
    # Phase 1-10: 验证文件类型 + 扫描版PDF友好消息
    # Critical fix: Return 200 + UploadResponse (not HTTPException) for unified contract
    if not file.filename:
        return UploadResponse(
            success=False,
            status="failed",
            status_reason="文件名为空，请重新选择文件。",
            next_actions=[],
            api_version="v2_phase1-10"
        )
    
    if file.filename.lower().endswith('.pdf'):
        # 扫描版PDF友好提示（bilingual）
        return UploadResponse(
            success=False,
            status="failed",
            status_reason="这是扫描版/图片对账单，请从网银下载 CSV/Excel 再上传。 | This is a scanned/image statement. Please download the CSV/Excel version from e-banking and re-upload.",
            next_actions=[],
            warnings=[
                "系统仅支持文本格式的CSV文件",
                "System only supports text-based CSV files"
            ],
            api_version="v2_phase1-10"
        )
    
    if not file.filename.endswith('.csv'):
        return UploadResponse(
            success=False,
            status="failed",
            status_reason="仅支持CSV文件格式，请转换后重新上传。",
            next_actions=[],
            warnings=["支持格式: .csv"],
            api_version="v2_phase1-10"
        )
    
    # Phase 3: Duplicate检测 - 简化版本（基于FileIndex的字段）
    existing_file = db.query(FileIndex).filter(
        and_(
            FileIndex.company_id == company_id,
            FileIndex.status.in_(['active', 'validated', 'posted']),  # 只检查有效文件
            FileIndex.is_active == True,  # 未删除
            FileIndex.account_number == account_number,  # 使用FileIndex的account_number字段
            FileIndex.period == statement_month,  # 期间字段（YYYY-MM格式）
            FileIndex.module == 'bank'
        )
    ).first()
    
    # 使用Phase 1-5的上传包装器处理
    wrapper = BankStatementUploadWrapper(
        db=db,
        company_id=company_id,
        username=username or "system"
    )
    
    result = await wrapper.process_csv_upload(
        file=file,
        bank_name=bank_name,
        account_number=account_number,
        statement_month=statement_month
    )
    
    # Phase 1-10: 如果检测到重复，修改返回结果并更新FileIndex状态
    if existing_file and result.get("success"):
        # 更新新上传文件的status为duplicate
        new_file = db.query(FileIndex).filter(
            FileIndex.raw_document_id == result.get('raw_document_id')
        ).first()
        
        new_file_id = None
        if new_file:
            new_file.status = 'duplicate'
            new_file.duplicate_warning = f"已存在相同账号和月份的文件（ID: {existing_file.id}）"
            db.commit()
            new_file_id = new_file.id  # Critical fix: Use FileIndex id, not raw_document_id
        
        # 使用UploadResponse格式
        return UploadResponse(
            success=True,
            status="duplicate",
            raw_document_id=result.get("raw_document_id"),
            file_id=new_file_id,  # Critical fix: Use FileIndex id for correct navigation
            company_id=company_id,
            statement_month=statement_month,
            account_number=account_number,
            existing_file_id=existing_file.id,
            duplicate_warning=f"当前公司/账号/月份已有主对账单（文件ID: {existing_file.id}）",
            next_actions=get_next_actions("duplicate"),
            api_version="v2_phase1-10",
            protection_enabled=True
        )
    
    # Phase 1-10: 根据结果返回统一的UploadResponse格式
    if result["success"]:
        return UploadResponse(
            success=True,
            status="active",
            raw_document_id=result.get("raw_document_id"),
            file_id=result.get("raw_document_id"),
            company_id=company_id,
            statement_month=statement_month,
            account_number=account_number,
            message=result.get("message", "✅ 银行月结单上传成功"),
            imported=result.get("imported"),
            matched=result.get("matched"),
            file_path=result.get("file_path"),
            next_actions=get_next_actions("active"),
            api_version="v2_phase1-10",
            protection_enabled=True
        )
    
    elif result.get("partial_success"):
        # 部分成功：文件已封存但验证失败
        raise HTTPException(
            status_code=422,
            detail=UploadResponse(
                success=False,
                status="failed",
                raw_document_id=result.get("raw_document_id"),
                file_id=result.get("raw_document_id"),
                company_id=company_id,
                statement_month=statement_month,
                account_number=account_number,
                status_reason=result.get("error", "CSV字段验证失败，文件已封存但未入账"),
                warnings=["请前往异常中心检查并修复问题"],
                next_actions=get_next_actions("failed"),
                api_version="v2_phase1-10",
                protection_enabled=True
            ).dict()
        )
    
    else:
        # 完全失败
        raise HTTPException(
            status_code=500,
            detail=UploadResponse(
                success=False,
                status="failed",
                raw_document_id=result.get("raw_document_id"),
                status_reason=result.get("error", "上传失败"),
                next_actions=get_next_actions("failed"),
                api_version="v2_phase1-10",
                protection_enabled=True
            ).dict()
        )
