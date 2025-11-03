"""
Bank Parser Metrics API

Provides per-bank statistics for monitoring and alerting.
"""
from fastapi import APIRouter, Query
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime

from accounting_app.parsers import get_circuit_breaker, BANK_CODES

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


class BankMetrics(BaseModel):
    """单银行指标"""
    bank_code: str
    total_requests: int
    success_rate: Optional[float]
    error_rate: Optional[float]
    consecutive_errors: int
    circuit_open: bool
    last_success: Optional[float]
    status: str


class MetricsSummary(BaseModel):
    """指标汇总"""
    total_banks: int
    enabled_banks: int
    circuit_open_count: int
    average_success_rate: Optional[float]
    metrics: List[BankMetrics]
    updated_at: str


@router.get("/banks", response_model=MetricsSummary)
async def get_bank_metrics(
    bank_code: Optional[str] = Query(None, description="特定银行代码（留空查看全部）")
):
    """
    ## 📊 分银行指标监控
    
    获取每个银行的解析性能指标，用于监控看板和告警。
    
    ### 查询参数：
    - **bank_code** (可选): 查看特定银行的指标，留空则返回全部
    
    ### 返回指标：
    - **total_requests**: 10分钟窗口内总请求数
    - **success_rate**: 成功率（0-1）
    - **error_rate**: 错误率（0-1）
    - **consecutive_errors**: 当前连续错误次数
    - **circuit_open**: 熔断器是否打开
    - **last_success**: 最后成功时间戳
    - **status**: 状态（healthy/warning/critical/circuit_open）
    
    ### 告警阈值建议：
    - **warning**: success_rate < 0.9 或 error_rate > 0.1
    - **critical**: success_rate < 0.8 或 error_rate > 0.2
    - **circuit_open**: 自动熔断，等待恢复
    
    ### 示例：
    ```bash
    # 查看所有银行
    curl "http://localhost:8000/api/metrics/banks"
    
    # 查看特定银行
    curl "http://localhost:8000/api/metrics/banks?bank_code=maybank"
    ```
    """
    cb = get_circuit_breaker()
    
    # Determine which banks to query
    banks_to_query = [bank_code] if bank_code else BANK_CODES
    
    metrics_list = []
    total_success_rate = 0
    valid_rates = 0
    circuit_open_count = 0
    
    for code in banks_to_query:
        stats = cb.get_bank_stats(code)
        
        # Determine status
        if stats["circuit_open"]:
            status = "circuit_open"
            circuit_open_count += 1
        elif stats["error_rate"] is None:
            status = "no_data"
        elif stats["error_rate"] > 0.2:
            status = "critical"
        elif stats["error_rate"] > 0.1:
            status = "warning"
        else:
            status = "healthy"
        
        metrics_list.append(BankMetrics(
            bank_code=stats["bank_code"],
            total_requests=stats["total_requests"],
            success_rate=stats["success_rate"],
            error_rate=stats["error_rate"],
            consecutive_errors=stats["consecutive_errors"],
            circuit_open=stats["circuit_open"],
            last_success=stats["last_success"],
            status=status
        ))
        
        if stats["success_rate"] is not None:
            total_success_rate += stats["success_rate"]
            valid_rates += 1
    
    average_success_rate = total_success_rate / valid_rates if valid_rates > 0 else None
    
    return MetricsSummary(
        total_banks=len(metrics_list),
        enabled_banks=len([m for m in metrics_list if not m.circuit_open]),
        circuit_open_count=circuit_open_count,
        average_success_rate=average_success_rate,
        metrics=metrics_list,
        updated_at=datetime.utcnow().isoformat()
    )


@router.get("/alerts", response_model=List[Dict])
async def get_active_alerts():
    """
    ## 🚨 活跃告警列表
    
    返回当前触发warning/critical阈值的银行列表。
    
    ### 返回格式：
    ```json
    [
      {
        "bank_code": "maybank",
        "severity": "critical",
        "message": "错误率 25.5% 超过阈值",
        "error_rate": 0.255,
        "consecutive_errors": 3
      }
    ]
    ```
    """
    cb = get_circuit_breaker()
    alerts = []
    
    for bank_code in BANK_CODES:
        stats = cb.get_bank_stats(bank_code)
        
        if stats["circuit_open"]:
            alerts.append({
                "bank_code": bank_code,
                "severity": "circuit_open",
                "message": f"熔断器已打开，正在冷却中",
                "error_rate": stats["error_rate"],
                "consecutive_errors": stats["consecutive_errors"]
            })
        elif stats["error_rate"] is not None:
            if stats["error_rate"] > 0.2:
                alerts.append({
                    "bank_code": bank_code,
                    "severity": "critical",
                    "message": f"错误率 {stats['error_rate']*100:.1f}% 超过阈值",
                    "error_rate": stats["error_rate"],
                    "consecutive_errors": stats["consecutive_errors"]
                })
            elif stats["error_rate"] > 0.1:
                alerts.append({
                    "bank_code": bank_code,
                    "severity": "warning",
                    "message": f"错误率 {stats['error_rate']*100:.1f}% 需要注意",
                    "error_rate": stats["error_rate"],
                    "consecutive_errors": stats["consecutive_errors"]
                })
    
    return alerts
