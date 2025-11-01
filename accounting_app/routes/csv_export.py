"""
CSV导出API路由
支持多种会计软件格式
"""
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from typing import Literal, Optional
import logging

from ..services.csv_exporter import export_to_csv, CSVExporter
from ..middleware.multi_tenant import get_current_company_id
from ..db import get_db

router = APIRouter(
    prefix="/export",
    tags=["CSV Export"]
)

logger = logging.getLogger(__name__)


@router.get("/journal/csv")
def export_journal_entries_csv(
    period: str = Query(..., description="期间，格式：YYYY-MM (例如: 2025-08)"),
    template_id: Optional[int] = Query(None, description="模板ID（优先使用数据库模板）"),
    template: Optional[Literal['generic_v1', 'sqlacc_v1', 'autocount_v1']] = Query(
        default='generic_v1',
        description="导出模板：generic_v1(通用), sqlacc_v1(SQL Account), autocount_v1(AutoCount) - fallback"
    ),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    导出会计分录为CSV文件
    
    ## 参数
    - **period**: 期间，格式YYYY-MM (例如: 2025-08)
    - **template**: 导出模板
      - `generic_v1`: 通用CSV格式
      - `sqlacc_v1`: SQL Account兼容格式 (Date, Account, Description, Debit, Credit, Ref)
      - `autocount_v1`: AutoCount兼容格式 (DocDate, AccNo, Description, DrAmt, CrAmt, DocNo)
    
    ## 返回
    CSV文件下载
    
    ## 模板说明
    
    ### generic_v1 (通用格式)
    ```
    date,account_code,description,debit,credit,reference
    2025-08-01,1100,Bank receipt,5000.00,0.00,REF001
    2025-08-01,4000,Sales income,0.00,5000.00,REF001
    ```
    
    ### sqlacc_v1 (SQL Account格式)
    ```
    Date,Account,Description,Debit,Credit,Ref
    01/08/2025,1100,Bank receipt,5000.00,,REF001
    01/08/2025,4000,Sales income,,5000.00,REF001
    ```
    注意：金额为0时显示空字符串，日期格式DD/MM/YYYY
    
    ### autocount_v1 (AutoCount格式)
    ```
    DocDate,AccNo,Description,DrAmt,CrAmt,DocNo
    01/08/2025,1100,Bank receipt,5000.00,,REF001
    01/08/2025,4000,Sales income,,5000.00,REF001
    ```
    注意：金额为0时显示空字符串，日期格式DD/MM/YYYY
    
    ## 使用场景
    - 将Replit系统的分录导入到SQL Account等会计软件
    - 备份月度分录数据
    - 与外部会计师共享数据
    
    ## 示例
    ```bash
    # 导出通用格式
    GET /export/journal/csv?period=2025-08&template=generic_v1
    
    # 导出SQL Account格式
    GET /export/journal/csv?period=2025-08&template=sqlacc_v1
    
    # 导出AutoCount格式
    GET /export/journal/csv?period=2025-08&template=autocount_v1
    ```
    """
    try:
        logger.info(f"导出会计分录CSV: company_id={company_id}, period={period}, template={template}")
        
        # 导出CSV（支持template_id优先）
        csv_data = export_to_csv(
            db=db,
            company_id=company_id,
            period=period,
            template_id=template_id,
            template_name=template or 'generic_v1',
            export_type='journal'
        )
        
        # 确定文件名
        filename = f"journal_entries_{period}_{'template' + str(template_id) if template_id else template}.csv"
        
        # 返回CSV文件
        return Response(
            content=csv_data,
            media_type='text/csv; charset=utf-8',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
    
    except ValueError as e:
        logger.error(f"导出CSV失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"导出CSV异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")


@router.get("/bank-statements/csv")
def export_bank_statements_csv(
    period: str = Query(..., description="期间，格式：YYYY-MM"),
    bank_name: Optional[str] = Query(None, description="银行名称（可选）"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    导出银行流水为CSV文件
    
    ## 参数
    - **period**: 期间，格式YYYY-MM
    - **bank_name**: 银行名称（可选，不指定则导出所有银行）
    
    ## 返回
    CSV文件，包含所有银行流水记录
    
    ## 字段说明
    - date: 交易日期
    - bank: 银行名称
    - account: 账号
    - description: 交易描述
    - reference: 参考号
    - debit: 借方金额
    - credit: 贷方金额
    - balance: 余额
    - matched: 是否已匹配 (Yes/No)
    - category: 自动分类
    
    ## 使用场景
    - 备份银行流水原始数据
    - 与银行对账
    - 提供给会计师核对
    
    ## 示例
    ```bash
    # 导出所有银行流水
    GET /export/bank-statements/csv?period=2025-08
    
    # 只导出Maybank流水
    GET /export/bank-statements/csv?period=2025-08&bank_name=Maybank
    ```
    """
    try:
        logger.info(f"导出银行流水CSV: company_id={company_id}, period={period}, bank={bank_name}")
        
        exporter = CSVExporter(db, company_id)
        csv_data = exporter.export_bank_statements(
            period=period,
            bank_name=bank_name
        )
        
        # 文件名
        if bank_name:
            filename = f"bank_statements_{period}_{bank_name}.csv"
        else:
            filename = f"bank_statements_{period}_all_banks.csv"
        
        return Response(
            content=csv_data,
            media_type='text/csv; charset=utf-8',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
    
    except Exception as e:
        logger.error(f"导出银行流水CSV异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
def list_export_templates(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    列出所有可用的CSV导出模板
    
    ## 返回
    模板列表，包含每个模板的详细信息
    
    ## 示例
    ```bash
    GET /export/templates
    ```
    """
    # TODO: 从export_templates表中查询
    # 目前返回内置模板
    
    templates = [
        {
            "template_name": "generic_v1",
            "description": "Generic CSV format for journal entries",
            "target_system": "Generic",
            "columns": ["date", "account_code", "description", "debit", "credit", "reference"],
            "date_format": "YYYY-MM-DD",
            "sample_row": "2025-08-01,1100,Bank receipt,5000.00,0.00,REF001"
        },
        {
            "template_name": "sqlacc_v1",
            "description": "SQL Account compatible format",
            "target_system": "SQL Account",
            "columns": ["Date", "Account", "Description", "Debit", "Credit", "Ref"],
            "date_format": "DD/MM/YYYY",
            "sample_row": "01/08/2025,1100,Bank receipt,5000.00,,REF001"
        },
        {
            "template_name": "autocount_v1",
            "description": "AutoCount compatible format",
            "target_system": "AutoCount",
            "columns": ["DocDate", "AccNo", "Description", "DrAmt", "CrAmt", "DocNo"],
            "date_format": "DD/MM/YYYY",
            "sample_row": "01/08/2025,1100,Bank receipt,5000.00,,REF001"
        }
    ]
    
    return {
        "company_id": company_id,
        "templates": templates,
        "total_count": len(templates)
    }


# ========== 使用示例 ==========

"""
在main.py中注册路由:

from accounting_app.routes import csv_export

app.include_router(csv_export.router, prefix="/api")

然后可以访问:
- GET /api/export/journal/csv?period=2025-08&template=generic_v1
- GET /api/export/journal/csv?period=2025-08&template=sqlacc_v1
- GET /api/export/bank-statements/csv?period=2025-08
- GET /api/export/templates
"""
