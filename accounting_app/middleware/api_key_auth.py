"""
Phase 2-2 Task 5: API密钥认证中间件

功能：
1. API Key验证（从Authorization头提取）
2. 权限检查（基于密钥权限列表）
3. 速率限制（基于密钥配置）
4. 审计日志记录
"""
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import time
from collections import defaultdict
import threading
from datetime import datetime, timedelta
import logging

from accounting_app.services.api_key_service import APIKeyService
from accounting_app.utils.flask_session_parser import parse_flask_session_from_request

logger = logging.getLogger(__name__)

# ========== HTTP Bearer认证方案 ==========

api_key_scheme = HTTPBearer(
    scheme_name="API Key",
    description="API密钥认证 (格式: Bearer sk_live_xxx 或 Bearer sk_test_xxx)"
)


# ========== 速率限制器 ==========

class RateLimiter:
    """
    基于令牌桶算法的速率限制器
    
    每个API密钥独立限制，支持动态配置限速值
    """
    
    def __init__(self):
        # {api_key_id: {"tokens": int, "last_refill": timestamp, "initialized": bool}}
        self._buckets = {}
        self._lock = threading.Lock()
    
    def is_allowed(self, api_key_id: int, rate_limit: int) -> tuple[bool, int]:
        """
        检查请求是否允许通过
        
        Args:
            api_key_id: API密钥ID
            rate_limit: 每分钟允许的请求数
        
        Returns:
            tuple: (是否允许, 剩余令牌数)
        """
        with self._lock:
            now = time.time()
            
            # 1. 初始化bucket（首次请求时给予满额令牌）
            if api_key_id not in self._buckets:
                self._buckets[api_key_id] = {
                    "tokens": rate_limit,  # 首次请求给予满额令牌
                    "last_refill": now,
                    "initialized": True
                }
            
            bucket = self._buckets[api_key_id]
            
            # 2. 计算需要补充的令牌数（每分钟补充rate_limit个）
            time_passed = now - bucket["last_refill"]
            refill_tokens = int((time_passed / 60.0) * rate_limit)
            
            # 3. 补充令牌（最多不超过rate_limit）
            if refill_tokens > 0:
                bucket["tokens"] = min(rate_limit, bucket["tokens"] + refill_tokens)
                bucket["last_refill"] = now
            
            # 4. 检查是否有令牌可用
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True, bucket["tokens"]
            else:
                return False, 0


# 全局速率限制器实例
rate_limiter = RateLimiter()


# ========== API密钥验证依赖 ==========

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = api_key_scheme
) -> dict:
    """
    验证API密钥的FastAPI依赖函数
    
    使用方法：
    ```python
    @router.get("/protected")
    async def protected_route(api_key_info: dict = Depends(verify_api_key)):
        user_id = api_key_info["user_id"]
        company_id = api_key_info["company_id"]
        ...
    ```
    
    Returns:
        dict: API密钥信息 {
            "id": 密钥ID,
            "user_id": 用户ID,
            "company_id": 公司ID,
            "username": 用户名,
            "role": 角色,
            "permissions": 权限列表,
            "environment": "live" 或 "test"
        }
    
    Raises:
        HTTPException: 401 如果密钥无效
    """
    api_key = credentials.credentials
    
    # 1. 验证密钥格式
    if not api_key.startswith("sk_live_") and not api_key.startswith("sk_test_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format. Expected: sk_live_xxx or sk_test_xxx"
        )
    
    # 2. 验证密钥有效性
    api_key_service = APIKeyService()
    key_info = api_key_service.verify_api_key(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
    
    # 3. 速率限制检查
    allowed, remaining = rate_limiter.is_allowed(
        api_key_id=key_info["id"],
        rate_limit=key_info["rate_limit"]
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {key_info['rate_limit']} requests/minute",
            headers={"Retry-After": "60"}
        )
    
    # 4. 返回密钥信息（供路由使用）
    return {
        "id": key_info["id"],
        "user_id": key_info["user_id"],
        "company_id": key_info["company_id"],
        "username": key_info["username"],
        "role": key_info["role"],
        "permissions": key_info["permissions"],
        "environment": key_info["environment"],
        "rate_limit_remaining": remaining
    }


# ========== 权限检查装饰器 ==========

def require_api_permission(required_permission: str):
    """
    API密钥权限检查装饰器
    
    用法：
    ```python
    @router.get("/export")
    @require_api_permission("export:bank_statements")
    async def export_data(api_key_info: dict = Depends(verify_api_key)):
        ...
    ```
    
    Args:
        required_permission: 需要的权限（如 "export:bank_statements"）
    """
    def decorator(func):
        async def wrapper(*args, api_key_info: dict = None, **kwargs):
            if not api_key_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required"
                )
            
            # 检查权限
            permissions = api_key_info.get("permissions", [])
            if required_permission not in permissions:
                logger.warning(
                    f"API密钥权限不足: key_id={api_key_info['id']}, "
                    f"required={required_permission}, has={permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key does not have required permission: {required_permission}"
                )
            
            return await func(*args, api_key_info=api_key_info, **kwargs)
        
        return wrapper
    return decorator


# ========== 混合认证（Session或API Key） ==========

async def verify_session_or_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> dict:
    """
    支持Session认证或API Key认证（二选一）- Phase 2-2 Task 8完整实现
    
    优先级：
    1. 如果有Authorization头 -> 使用API Key认证
    2. 否则检查Session -> 使用Flask Session认证（完整session解析）
    3. 两者都没有 -> 401错误
    
    Returns:
        dict: 认证信息 {
            "auth_type": "api_key" 或 "session",
            "user_id": 用户ID,
            "company_id": 公司ID,
            "username": 用户名,
            "role": 角色,
            ...
        }
    """
    # 1. 尝试API Key认证
    if credentials:
        try:
            api_key_info = await verify_api_key(credentials)
            api_key_info["auth_type"] = "api_key"
            logger.info(f"✅ API Key认证成功: user_id={api_key_info['user_id']}")
            return api_key_info
        except HTTPException:
            logger.debug("API Key认证失败，尝试Session认证")
            pass
    
    # 2. 尝试Flask Session认证（Phase 2-2 Task 8新增）
    session_data = await parse_flask_session_from_request(request)
    
    if session_data:
        # 验证必需字段（安全加固 - 禁止默认company_id）
        user_id = session_data.get('user_id')
        company_id = session_data.get('company_id')
        
        if not user_id:
            logger.warning("Flask session缺少user_id字段，拒绝认证")
            session_data = None  # 标记为无效session
        elif not company_id:
            logger.warning(f"Flask session缺少company_id字段 (user_id={user_id})，拒绝认证以保护多租户隔离")
            session_data = None  # 标记为无效session
        else:
            # Session认证成功，返回统一格式
            logger.info(f"✅ Flask Session认证成功: user_id={user_id}, company_id={company_id}")
            return {
                "auth_type": "session",
                "user_id": user_id,
                "username": session_data.get('username', f"user_{user_id}"),
                "role": session_data.get('role', 'user'),
                "company_id": company_id,
                "permissions": []  # Session用户默认继承role权限，不限制特定permissions
            }
    
    # 3. 两者都失败 - 返回401错误
    logger.warning("认证失败：既无有效API Key也无有效Session")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide API key (Authorization: Bearer sk_xxx) or login session.",
        headers={"WWW-Authenticate": "Bearer"}
    )
