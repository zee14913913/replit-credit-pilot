"""
Phase 2-1 修复：正确的RBAC中间件实现
使用FastAPI依赖注入系统，避免强制注入参数导致的TypeError
"""
from typing import Optional
from fastapi import Header, HTTPException, Cookie, Depends
from sqlalchemy.orm import Session
import logging

from ..db import get_db
from ..models import User, Permission
from ..services.auth_service import get_user_by_token

logger = logging.getLogger(__name__)


# 定义角色层级（数字越大权限越高）
ROLE_HIERARCHY = {
    'viewer': 1,
    'data_entry': 2,
    'loan_officer': 3,
    'accountant': 4,
    'admin': 5
}


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None)
) -> Optional[User]:
    """
    FastAPI依赖函数：从请求中获取当前用户
    
    认证方式优先级：
    1. Authorization header (Bearer token)
    2. Cookie (session_token)
    
    Args:
        db: 数据库session（自动注入）
        authorization: Authorization header
        session_token: Cookie中的session_token
    
    Returns:
        User对象或None
    
    Raises:
        HTTPException: 401 未授权
    """
    token = None
    
    # 方式1：从Authorization header获取
    if authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ')[1]
    
    # 方式2：从Cookie获取
    elif session_token:
        token = session_token
    
    if not token:
        return None
    
    # 验证token并获取用户
    user = get_user_by_token(db, token)
    
    return user


def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    FastAPI依赖函数：要求用户已登录
    
    使用方式：
    ```python
    @router.get("/protected")
    async def protected_route(user: User = Depends(require_auth)):
        return {"username": user.username}
    ```
    
    Args:
        current_user: 当前用户（由get_current_user注入）
    
    Returns:
        User对象
    
    Raises:
        HTTPException: 401 未授权
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="未登录或身份验证失败，请先登录"
        )
    
    return current_user


def require_role(*allowed_roles: str):
    """
    FastAPI依赖函数工厂：要求用户拥有指定角色
    
    使用方式：
    ```python
    @router.post("/invoices")
    async def create_invoice(
        user: User = Depends(require_role('accountant', 'admin'))
    ):
        return {"user": user.username, "role": user.role}
    ```
    
    Args:
        *allowed_roles: 允许的角色列表
    
    Returns:
        依赖函数
    """
    def check_role(current_user: User = Depends(require_auth)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"角色权限不足：用户 {current_user.username} ({current_user.role}) "
                f"尝试访问需要 {allowed_roles} 角色的资源"
            )
            raise HTTPException(
                status_code=403,
                detail=f"权限不足：需要 {', '.join(allowed_roles)} 角色"
            )
        
        logger.info(f"角色验证通过：{current_user.username} ({current_user.role})")
        return current_user
    
    return check_role


def check_permission(
    db: Session,
    user: User,
    resource: str,
    action: str
) -> bool:
    """
    检查用户是否有权限执行指定资源的操作
    
    权限检查逻辑：
    1. admin角色：自动通过（拥有* *权限）
    2. 查询permissions表：role + resource + action
    3. 通配符支持：resource=* 或 action=*
    
    Args:
        db: 数据库session
        user: 当前用户对象
        resource: 资源名称（如：bank_statements, invoices）
        action: 操作类型（如：create, read, update, delete, export）
    
    Returns:
        bool: 是否有权限
    """
    if not user or not user.is_active:
        logger.warning(f"权限检查失败：用户不存在或未激活")
        return False
    
    # admin角色自动通过
    if user.role == 'admin':
        logger.info(f"admin用户 {user.username} 自动通过权限检查")
        return True
    
    # 查询权限表
    # 优先级1：精确匹配（role + resource + action）
    exact_permission = db.query(Permission).filter(
        Permission.role == user.role,
        Permission.resource == resource,
        Permission.action == action,
        Permission.allowed == True
    ).first()
    
    if exact_permission:
        logger.info(f"权限检查通过（精确匹配）：{user.username} ({user.role}) -> {resource}.{action}")
        return True
    
    # 优先级2：资源通配符（role + resource=* + action）
    wildcard_resource_permission = db.query(Permission).filter(
        Permission.role == user.role,
        Permission.resource == '*',
        Permission.action == action,
        Permission.allowed == True
    ).first()
    
    if wildcard_resource_permission:
        logger.info(f"权限检查通过（资源通配符）：{user.username} ({user.role}) -> *.{action}")
        return True
    
    # 优先级3：操作通配符（role + resource + action=*）
    wildcard_action_permission = db.query(Permission).filter(
        Permission.role == user.role,
        Permission.resource == resource,
        Permission.action == '*',
        Permission.allowed == True
    ).first()
    
    if wildcard_action_permission:
        logger.info(f"权限检查通过（操作通配符）：{user.username} ({user.role}) -> {resource}.*")
        return True
    
    # 优先级4：完全通配符（role + resource=* + action=*）
    full_wildcard_permission = db.query(Permission).filter(
        Permission.role == user.role,
        Permission.resource == '*',
        Permission.action == '*',
        Permission.allowed == True
    ).first()
    
    if full_wildcard_permission:
        logger.info(f"权限检查通过（完全通配符）：{user.username} ({user.role}) -> *.*")
        return True
    
    # 无权限
    logger.warning(
        f"权限检查失败：{user.username} ({user.role}) 无权访问 {resource}.{action}"
    )
    return False


def require_permission(resource: str, action: str):
    """
    FastAPI依赖函数工厂：要求用户拥有指定资源的操作权限
    
    使用方式：
    ```python
    @router.delete("/invoices/{invoice_id}")
    async def delete_invoice(
        invoice_id: int,
        user: User = Depends(require_permission('invoices', 'delete')),
        db: Session = Depends(get_db)
    ):
        # 用户已通过权限检查，可以删除发票
        pass
    ```
    
    Args:
        resource: 资源名称
        action: 操作类型
    
    Returns:
        依赖函数
    """
    def check_perm(
        current_user: User = Depends(require_auth),
        db: Session = Depends(get_db)
    ) -> User:
        # 检查权限
        has_permission = check_permission(db, current_user, resource, action)
        
        if not has_permission:
            logger.warning(
                f"权限检查失败：用户 {current_user.username} ({current_user.role}) "
                f"尝试对 {resource} 执行 {action} 操作"
            )
            raise HTTPException(
                status_code=403,
                detail=f"权限不足：无法对 {resource} 执行 {action} 操作"
            )
        
        logger.info(
            f"权限验证通过：{current_user.username} ({current_user.role}) "
            f"对 {resource} 执行 {action}"
        )
        
        return current_user
    
    return check_perm


def check_role_hierarchy(user_role: str, required_role: str) -> bool:
    """
    检查用户角色是否满足层级要求
    
    角色层级：viewer < data_entry < loan_officer < accountant < admin
    
    Args:
        user_role: 用户的角色
        required_role: 要求的最低角色
    
    Returns:
        bool: 用户角色是否满足要求
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 999)
    
    return user_level >= required_level
