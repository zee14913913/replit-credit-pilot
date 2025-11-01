"""
安全中间件
包含任务Token验证
"""
from fastapi import Request, HTTPException, Header
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


def get_task_secret_token() -> str:
    """
    从环境变量获取任务密钥
    """
    token = os.getenv('TASK_SECRET_TOKEN', '')
    if not token:
        logger.warning("⚠️ TASK_SECRET_TOKEN 未设置，使用默认值（不安全！）")
        return 'default-insecure-token-please-change'
    return token


def verify_task_token(x_task_token: Optional[str] = Header(None)) -> bool:
    """
    验证任务Token
    
    使用方法:
    @router.post("/tasks/run-daily")
    def run_daily_task(
        verified: bool = Depends(verify_task_token),
        db: Session = Depends(get_db)
    ):
        # 已验证Token，可以执行
        ...
    """
    expected_token = get_task_secret_token()
    
    if not x_task_token:
        raise HTTPException(
            status_code=401,
            detail="缺少 X-Task-Token header"
        )
    
    if x_task_token != expected_token:
        logger.warning(f"无效的任务Token尝试: {x_task_token[:10]}...")
        raise HTTPException(
            status_code=403,
            detail="无效的任务Token"
        )
    
    return True


class TaskAuthMiddleware:
    """
    任务路由认证中间件
    """
    
    PROTECTED_PATHS = [
        "/tasks/run-daily",
        "/tasks/run-monthly",
        "/tasks/run-management",
        "/api/tasks/"
    ]
    
    @staticmethod
    def is_protected_path(path: str) -> bool:
        """检查路径是否需要Token保护"""
        for protected in TaskAuthMiddleware.PROTECTED_PATHS:
            if path.startswith(protected):
                return True
        return False
    
    @staticmethod
    async def validate_request(request: Request, call_next):
        """验证请求Token"""
        if TaskAuthMiddleware.is_protected_path(request.url.path):
            token = request.headers.get('X-Task-Token')
            expected_token = get_task_secret_token()
            
            if token != expected_token:
                logger.warning(f"未授权访问任务路由: {request.url.path}")
                raise HTTPException(
                    status_code=403,
                    detail="需要有效的X-Task-Token header"
                )
        
        response = await call_next(request)
        return response


# ========== 使用示例 ==========

"""
# 在 main.py 中注册中间件:
from accounting_app.middleware.security import TaskAuthMiddleware

@app.middleware("http")
async def task_auth_middleware(request: Request, call_next):
    return await TaskAuthMiddleware.validate_request(request, call_next)


# 在路由中使用依赖注入:
from accounting_app.middleware.security import verify_task_token

@router.post("/tasks/run-daily")
def run_daily_task(
    verified: bool = Depends(verify_task_token),
    db: Session = Depends(get_db)
):
    # Token已验证，执行任务
    return {"status": "success"}
"""
