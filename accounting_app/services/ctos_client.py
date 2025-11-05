# accounting_app/services/ctos_client.py
import os
from typing import Dict, Any

def is_enabled() -> bool:
    return os.getenv("CTOS_API_ENABLED", "0") == "1"

def submit_consent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    直连模式：提交授权；这里是桩函数。
    真实对接时：发起 HTTP 请求到 CTOS，返回 request_id 等信息。
    """
    if not is_enabled():
        return {"mode": "manual", "status": "queued"}
    return {"mode": "api", "status": "submitted", "request_id": "CTOSREQ123"}

def poll_report(request_id: str) -> Dict[str, Any]:
    """
    直连模式：轮询报告是否就绪；桩函数。
    """
    if not is_enabled():
        return {"mode": "manual", "status": "pending"}
    return {"mode": "api", "status": "ready", "download_url": "https://example.com/report.pdf"}

def fetch_metrics_from_report(report_bytes: bytes) -> Dict[str, Any]:
    """
    从报告字节解析关键指标：DSR/DSRC/commitments 等。
    当前为示例解析。
    """
    return {
        "dsr": 0.43,
        "dsrc": 0.50,
        "commitments": 2500.0,
        "monthly_income": 8000.0
    }
