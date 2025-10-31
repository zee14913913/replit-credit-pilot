"""
定时任务路由
用于外部定时器（UptimeRobot/curl）触发月结任务
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import os

from ..db import get_db
from ..tasks.monthly_close import run_monthly_close

router = APIRouter()

# 任务密钥（从环境变量读取）
TASK_SECRET_TOKEN = os.getenv("TASK_SECRET_TOKEN", "your-secret-token-here")


@router.post("/monthly-close")
def trigger_monthly_close(
    company_id: int,
    month: str,
    x_task_token: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    触发月结任务
    
    用法：
    curl -X POST "https://your-repl.repl.co/api/tasks/monthly-close?company_id=1&month=2025-01" \
         -H "X-Task-Token: your-secret-token"
    
    或使用UptimeRobot每月1号自动触发
    """
    # 验证密钥
    if x_task_token != TASK_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid task token")
    
    # 执行月结任务
    result = run_monthly_close(db, company_id, month)
    
    return result
