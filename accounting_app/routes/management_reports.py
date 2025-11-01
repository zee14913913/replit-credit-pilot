"""
Management Report API路由
提供月度管理报表查询和导出功能
Phase 2-2: 添加导出分级控制（Export-Level Permissions）
"""
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from typing import Literal, Optional
import logging

from ..services.management_report_generator import generate_management_report
from ..utils.report_renderer import render_report
from ..middleware.multi_tenant import get_current_company_id
from ..middleware.rbac_fixed import require_permission
from ..models import User, AuditLog
from ..db import get_db

router = APIRouter(
    prefix="/reports/management",
    tags=["Management Reports"]
)

logger = logging.getLogger(__name__)


@router.get("/{period}")
def get_management_report(
    period: str,
    format: Literal['json', 'pdf'] = Query(default='json', description="输出格式：json或pdf"),
    include_details: bool = Query(default=True, description="是否包含详细数据"),
    company_id: int = Depends(get_current_company_id),
    current_user: User = Depends(require_permission('export:management_reports', 'read')),
    db: Session = Depends(get_db)
):
    """
    获取月度Management Report
    
    ## 参数
    - **period**: 报表期间，格式：YYYY-MM (例如: 2025-08)
    - **format**: 输出格式
      - `json`: JSON数据（给前端渲染）
      - `pdf`: PDF文件（给下载导出）
    - **include_details**: 是否包含未匹配项目详细列表
    
    ## 返回内容
    ### JSON格式包含：
    - **pnl_summary**: P&L摘要（收入、费用、净利润）
    - **balance_sheet_summary**: Balance Sheet摘要（资产、负债、权益）
    - **aging_summary**: AR/AP账龄摘要
    - **bank_balances**: 银行账户余额
    - **data_quality**: 数据质量指标（重要！）
      - data_freshness: 数据新鲜度
      - unreconciled_count: 未匹配项数量
      - confidence_score: 置信度评分
      - source_modules: 数据来源模块
      - estimated_revenue_gap: 估算收入缺口
    - **unreconciled_details**: 未匹配项目详细列表
    
    ### PDF格式：
    - 完整的Management Report PDF文档
    - 包含数据质量段落
    - 包含未匹配项目列表
    
    ## 示例
    ```bash
    # 获取JSON格式
    GET /reports/management/2025-08?format=json
    
    # 下载PDF
    GET /reports/management/2025-08?format=pdf
    
    # 仅摘要（不含详细列表）
    GET /reports/management/2025-08?include_details=false
    ```
    """
    try:
        # 验证period格式
        if not _validate_period_format(period):
            raise HTTPException(
                status_code=400,
                detail="期间格式错误，应为YYYY-MM格式（例如：2025-08）"
            )
        
        logger.info(f"生成Management Report: company_id={company_id}, period={period}, format={format}")
        
        # 1. 生成报表数据
        report_data = generate_management_report(
            db=db,
            company_id=company_id,
            period=period,
            save_to_db=True  # 自动保存到数据库
        )
        
        # 如果不需要详细列表，移除该字段
        if not include_details:
            report_data['unreconciled_details'] = []
        
        # 2. 渲染输出
        if format == 'pdf':
            pdf_bytes = render_report(
                data=report_data,
                report_type='management',
                format='pdf',
                company_name=f"Company {company_id}"  # TODO: 从数据库获取真实公司名
            )
            
            # 写入审计日志（防御性）
            try:
                audit_log = AuditLog(
                    company_id=company_id,
                    user_id=current_user.id,
                    username=current_user.username,
                    action_type='export',
                    entity_type='report',
                    description=f"导出管理报表PDF: period={period}",
                    new_value={'period': period, 'report_type': 'management', 'format': 'pdf', 'include_details': include_details},
                    success=True
                )
                db.add(audit_log)
                db.commit()
            except Exception as e:
                logger.error(f"审计日志写入失败（导出管理报表PDF）：{e}")
                db.rollback()
            
            # 返回PDF文件
            return Response(
                content=pdf_bytes,
                media_type='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="Management_Report_{period}.pdf"'
                }
            )
        else:
            # JSON格式不记录审计日志（查看操作，非导出）
            # 返回JSON数据
            return report_data
    
    except ValueError as e:
        logger.error(f"生成报表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"生成报表异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")


@router.get("/")
def list_management_reports(
    start_period: Optional[str] = Query(None, description="开始期间 (YYYY-MM)"),
    end_period: Optional[str] = Query(None, description="结束期间 (YYYY-MM)"),
    limit: int = Query(default=12, le=100, description="返回记录数"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    列出历史Management Reports
    
    ## 参数
    - **start_period**: 开始期间（例如：2025-01）
    - **end_period**: 结束期间（例如：2025-08）
    - **limit**: 最多返回记录数（默认12个月）
    
    ## 返回
    报表列表，包含每个报表的元数据
    
    ## 示例
    ```bash
    # 获取最近12个月的报表
    GET /reports/management/
    
    # 获取指定期间的报表
    GET /reports/management/?start_period=2025-01&end_period=2025-08
    ```
    """
    # TODO: 从management_reports表中查询
    
    # 模拟返回
    return {
        "company_id": company_id,
        "reports": [
            {
                "period": "2025-08",
                "generated_at": "2025-09-01T10:00:00",
                "status": "completed",
                "unreconciled_count": 0,
                "confidence_score": 1.0
            },
            {
                "period": "2025-07",
                "generated_at": "2025-08-01T10:00:00",
                "status": "completed",
                "unreconciled_count": 2,
                "confidence_score": 0.96
            }
        ],
        "total_count": 2
    }


@router.get("/data-quality/{period}")
def get_data_quality_metrics(
    period: str,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    获取指定期间的数据质量指标
    
    单独接口，方便前端快速检查数据质量
    
    ## 返回
    - data_freshness: 数据新鲜度
    - unreconciled_count: 未匹配项数量
    - confidence_score: 置信度评分
    - source_modules: 数据来源
    - estimated_revenue_gap: 估算收入缺口
    
    ## 示例
    ```bash
    GET /reports/management/data-quality/2025-08
    ```
    """
    try:
        # 生成完整报表（但不保存）
        report_data = generate_management_report(
            db=db,
            company_id=company_id,
            period=period,
            save_to_db=False
        )
        
        # 只返回数据质量部分
        return report_data['data_quality']
    
    except Exception as e:
        logger.error(f"获取数据质量指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unreconciled/{period}")
def get_unreconciled_items(
    period: str,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    获取未匹配项目详细列表
    
    ## 返回
    未匹配项目的详细列表，包含：
    - file_name: 文件名
    - file_type: 文件类型
    - upload_date: 上传日期
    - failure_stage: 失败阶段
    - description: 描述
    - estimated_amount: 估算金额
    
    ## 示例
    ```bash
    GET /reports/management/unreconciled/2025-08
    ```
    """
    try:
        # 生成完整报表（但不保存）
        report_data = generate_management_report(
            db=db,
            company_id=company_id,
            period=period,
            save_to_db=False
        )
        
        return {
            "period": period,
            "unreconciled_count": report_data['data_quality']['unreconciled_count'],
            "items": report_data['unreconciled_details']
        }
    
    except Exception as e:
        logger.error(f"获取未匹配项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _validate_period_format(period: str) -> bool:
    """验证期间格式是否为YYYY-MM"""
    try:
        parts = period.split('-')
        if len(parts) != 2:
            return False
        
        year = int(parts[0])
        month = int(parts[1])
        
        if year < 2000 or year > 2100:
            return False
        if month < 1 or month > 12:
            return False
        
        return True
    except:
        return False


# ========== 使用示例 ==========

"""
在main.py中注册路由:

from accounting_app.routers import management_reports

app.include_router(management_reports.router, prefix="/api")

然后可以访问:
- GET /api/reports/management/2025-08?format=json
- GET /api/reports/management/2025-08?format=pdf
- GET /api/reports/management/
- GET /api/reports/management/data-quality/2025-08
- GET /api/reports/management/unreconciled/2025-08
"""
