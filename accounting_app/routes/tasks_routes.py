"""
定时任务路由
用于外部定时器（UptimeRobot/curl）触发月结任务
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import os
import sys

from ..db import get_db
from ..tasks.monthly_close import run_monthly_close

router = APIRouter()

# 任务密钥（从环境变量读取，必须设置）
TASK_SECRET_TOKEN = os.getenv("TASK_SECRET_TOKEN", "")

# 安全检查：不允许使用默认值或空值
if not TASK_SECRET_TOKEN or TASK_SECRET_TOKEN == "your-secret-token-here":
    print("⚠️ 警告: TASK_SECRET_TOKEN 未设置或使用默认值")
    print("   为了安全，定时任务功能已禁用")
    print("   请在Replit Secrets中设置 TASK_SECRET_TOKEN")
    TASK_SECRET_TOKEN = None  # 禁用定时任务功能


@router.post("/monthly-close")
def trigger_monthly_close(
    company_id: int,
    month: str,
    x_task_token: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    触发月结任务（需要配置TASK_SECRET_TOKEN）
    
    用法：
    1. 在Replit Secrets中设置 TASK_SECRET_TOKEN
    2. curl -X POST "https://your-repl.repl.co/api/tasks/monthly-close?company_id=1&month=2025-01" \
         -H "X-Task-Token: your-secret-token"
    
    或使用UptimeRobot每月1号自动触发
    """
    # 检查是否已配置密钥
    if TASK_SECRET_TOKEN is None:
        raise HTTPException(
            status_code=503,
            detail="Task endpoint is disabled. Please configure TASK_SECRET_TOKEN in Replit Secrets."
        )
    
    # 验证密钥
    if x_task_token != TASK_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid task token")
    
    # 执行月结任务
    result = run_monthly_close(db, company_id, month)
    
    return result
