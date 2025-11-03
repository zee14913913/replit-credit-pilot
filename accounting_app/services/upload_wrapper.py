"""
Phase 1-5: 上传接口包装器
为现有上传接口提供raw_documents保护层
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from fastapi import UploadFile
import io
import csv

from .upload_handler import UploadHandler
from ..models import BankStatement, RawLine

logger = logging.getLogger(__name__)


class BankStatementUploadWrapper:
    """
    银行月结单上传包装器
    
    Phase 1-5核心改造：
    1. 先用UploadHandler封存原件
    2. 然后解析CSV内容
    3. 保存到raw_lines
    4. 验证行数对账
    5. 部分成功拦截
    """
    
    def __init__(self, db: Session, company_id: int, username: str = "system"):
        self.db = db
        self.company_id = company_id
        self.username = username
        self.upload_handler = UploadHandler(db, company_id, username)
    
    async def process_csv_upload(
        self,
        file: UploadFile,
        bank_name: str,
        account_number: str,
        statement_month: str
    ) -> Dict[str, Any]:
        """
        处理银行月结单CSV上传（Phase 1-5改造版）
        
        流程：
        1. 封存原件（raw_documents + file_index）
        2. 解析CSV
        3. 保存raw_lines
        4. 行数对账
        5. 如果验证通过，创建bank_statement记录
        6. 如果验证失败，进入异常中心
        """
        # Step 1: 封存原件
        upload_result = await self.upload_handler.handle_upload(
            file=file,
            file_category='bank_statement',
            related_entity_type='bank_statement',
            period=statement_month,
            description=f"{bank_name} - {account_number} - {statement_month}",
            module='bank',
            account_number=account_number  # Phase 3: duplicate检测所需
        )
        
        if not upload_result["success"]:
            return upload_result
        
        raw_document_id = upload_result["raw_document_id"]
        file_path = upload_result["file_path"]
        
        logger.info(
            f"✅ Step 1: 原件已封存 - "
            f"raw_document_id={raw_document_id}, path={file_path}"
        )
        
        # Step 2: 解析CSV内容 + 字段完整性验证
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            csv_lines = list(csv_reader)
            
            # Phase 1-5: 字段完整性验证（必需字段）
            required_fields = {'Date', 'Description', 'Debit', 'Credit', 'Balance', 'Reference'}
            if csv_lines and csv_reader.fieldnames:
                actual_fields = set(csv_reader.fieldnames)
                missing_fields = required_fields - actual_fields
                
                if missing_fields:
                    error_msg = f"CSV字段不完整，缺少必需字段: {', '.join(missing_fields)}"
                    logger.error(f"❌ {error_msg}")
                    
                    # 进入异常中心
                    self.upload_handler.handle_partial_success(
                        raw_document_id=raw_document_id,
                        raw_line_count=0,
                        parsed_count=0,
                        file_category='bank_statement',
                        context={
                            'error': error_msg,
                            'missing_fields': list(missing_fields),
                            'actual_fields': list(actual_fields)
                        }
                    )
                    
                    return {
                        "success": False,
                        "partial_success": True,
                        "error_code": "INGEST_VALIDATION_FAILED",
                        "error": error_msg,
                        "raw_document_id": raw_document_id,
                        "file_path": file_path,
                        "message": "CSV字段验证失败，文件已封存但未入账"
                    }
            
            logger.info(f"✅ Step 2: CSV解析完成 - total_lines={len(csv_lines)}")
            
        except Exception as e:
            logger.error(f"❌ CSV解析失败: {e}")
            return {
                "success": False,
                "error": f"CSV解析失败: {e}",
                "raw_document_id": raw_document_id
            }
        
        # Step 3: 保存raw_lines
        try:
            raw_line_records = []
            for line_num, row in enumerate(csv_lines, start=1):
                # 将CSV行转为文本
                line_text = ", ".join([f"{k}={v}" for k, v in row.items()])
                raw_line_records.append(line_text)
            
            # Phase 1-5修复：parser_version替代metadata
            raw_lines = self.upload_handler.save_raw_lines(
                raw_document_id=raw_document_id,
                lines=raw_line_records,
                parser_version='csv_parser_v1.0'
            )
            
            logger.info(
                f"✅ Step 3: raw_lines已保存 - "
                f"raw_document_id={raw_document_id}, count={len(raw_lines)}"
            )
            
        except Exception as e:
            logger.error(f"❌ raw_lines保存失败: {e}")
            return {
                "success": False,
                "error": f"raw_lines保存失败: {e}",
                "raw_document_id": raw_document_id
            }
        
        # Step 4: 解析业务数据
        bank_statements = []
        parsed_count = 0
        
        for row in csv_lines:
            try:
                from datetime import datetime
                from decimal import Decimal
                
                transaction_date = datetime.strptime(row.get('Date', ''), '%Y-%m-%d').date()
                description = row.get('Description', '').strip()
                debit_amount = Decimal(row.get('Debit', '0') or '0')
                credit_amount = Decimal(row.get('Credit', '0') or '0')
                balance = Decimal(row.get('Balance', '0') or '0') if row.get('Balance') else None
                reference = row.get('Reference', '')
                
                # 注意：这里不立即commit，等行数验证通过后再commit
                bank_stmt = BankStatement(
                    company_id=self.company_id,
                    bank_name=bank_name,
                    account_number=account_number,
                    statement_month=statement_month,
                    transaction_date=transaction_date,
                    description=description,
                    reference_number=reference,
                    debit_amount=debit_amount,
                    credit_amount=credit_amount,
                    balance=balance,
                    matched=False,
                    raw_line_id=raw_lines[parsed_count].id if parsed_count < len(raw_lines) else None
                )
                
                bank_statements.append(bank_stmt)
                parsed_count += 1
                
            except Exception as e:
                logger.warning(f"跳过无效CSV行: {row}, 错误: {e}")
                continue
        
        logger.info(f"✅ Step 4: 业务数据解析完成 - parsed_count={parsed_count}")
        
        # Step 5: Phase 1-5关键验证 - 行数对账
        is_valid, error_msg = self.upload_handler.verify_line_count(
            raw_document_id=raw_document_id,
            parsed_record_count=parsed_count,
            file_category='bank_statement'
        )
        
        if not is_valid:
            # 部分成功拦截：进入异常中心
            self.upload_handler.handle_partial_success(
                raw_document_id=raw_document_id,
                raw_line_count=len(raw_lines),
                parsed_count=parsed_count,
                file_category='bank_statement',
                context={
                    'bank_name': bank_name,
                    'account_number': account_number,
                    'statement_month': statement_month,
                    'error': error_msg
                }
            )
            
            logger.warning(
                f"⚠️ 部分成功拦截 - "
                f"文件已封存但未入账，已进入异常中心"
            )
            
            return {
                "success": False,
                "partial_success": True,
                "error_code": "INGEST_VALIDATION_FAILED",
                "error": error_msg,
                "raw_document_id": raw_document_id,
                "file_path": file_path,
                "raw_line_count": len(raw_lines),
                "parsed_count": parsed_count,
                "message": "行数对账失败，文件已封存但未入账，请检查异常中心"
            }
        
        # Step 6: 行数验证通过，提交bank_statement记录
        try:
            for stmt in bank_statements:
                self.db.add(stmt)
            
            self.db.commit()
            
            logger.info(
                f"✅ Step 6: bank_statement记录已提交 - "
                f"count={len(bank_statements)}"
            )
            
            # Step 7: 自动匹配交易（原有逻辑）
            from ..services.bank_matcher import auto_match_transactions
            matched_count = auto_match_transactions(self.db, self.company_id, statement_month)
            
            logger.info(f"✅ Step 7: 自动匹配完成 - matched_count={matched_count}")
            
            return {
                "success": True,
                "raw_document_id": raw_document_id,
                "file_path": file_path,
                "imported": len(bank_statements),
                "matched": matched_count,
                "message": f"✅ 成功导入 {len(bank_statements)} 笔银行流水，自动匹配 {matched_count} 笔"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ bank_statement记录提交失败: {e}", exc_info=True)
            
            return {
                "success": False,
                "error": f"记录提交失败: {e}",
                "raw_document_id": raw_document_id,
                "message": "文件已封存但记录创建失败"
            }


class SupplierInvoiceUploadWrapper:
    """
    供应商发票上传包装器（预留）
    Phase 1-5: 后续实现
    """
    pass


class POSReportUploadWrapper:
    """
    POS报表上传包装器（预留）
    Phase 1-5: 后续实现
    """
    pass
