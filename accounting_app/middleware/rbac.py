"""
Phase 2-1: RBAC权限系统中间件
提供角色检查装饰器和权限验证函数
"""
from functools import wraps
from typing import List, Optional, Callable
from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
import logging

from ..db import get_db
from ..models import User, Permission

logger = logging.getLogger(__name__)


# 定义角色层级（数字越大权限越高）
ROLE_HIERARCHY = {
    'viewer': 1,
    'data_entry': 2,
    'loan_officer': 3,
    'accountant': 4,
    'admin': 5
}


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """
    从请求中获取当前用户
    
    优先级：
    1. Authorization header (Bearer token)
    2. Session cookie
    3. Query parameter (临时方案)
    
    Returns:
        User对象或None
    """
    # Phase 2-1: 临时实现 - 从query参数或header获取user_id
    # TODO: 实现完整的JWT token认证系统
    
    user_id = None
    
    # 方式1：从Authorization header获取
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        # TODO: 解析JWT token获取user_id
        # user_id = decode_jwt_token(token)
        pass
    
    # 方式2：从session获取
    if hasattr(request, 'session'):
        user_id = request.session.get('user_id')
    
    # 方式3：临时方案 - 从query参数获取（仅开发环境）
    if not user_id and request.query_params.get('user_id'):
        user_id = int(request.query_params.get('user_id'))
        logger.warning(f"使用query参数user_id={user_id}（仅开发环境）")
    
    if not user_id:
        return None
    
    # 从数据库获取用户
    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True
    ).first()
    
    return user


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


def require_role(
    allowed_roles: List[str],
    resource: Optional[str] = None,
    action: Optional[str] = None
):
    """
    FastAPI路由装饰器：要求用户拥有指定角色
    
    使用方式1：仅检查角色
    @router.post("/invoices")
    @require_role(['accountant', 'admin'])
    async def create_invoice(...):
        pass
    
    使用方式2：检查角色+权限矩阵
    @router.post("/invoices")
    @require_role(['accountant', 'admin'], resource='invoices', action='create')
    async def create_invoice(...):
        pass
    
    Args:
        allowed_roles: 允许的角色列表
        resource: 可选，资源名称（用于权限矩阵检查）
        action: 可选，操作类型（用于权限矩阵检查）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            request: Request = None,
            db: Session = Depends(get_db),
            **kwargs
        ):
            # 获取当前用户
            current_user = get_current_user(request, db)
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="未登录或身份验证失败，请先登录"
                )
            
            # 检查角色
            if current_user.role not in allowed_roles:
                logger.warning(
                    f"角色权限不足：用户 {current_user.username} ({current_user.role}) "
                    f"尝试访问需要 {allowed_roles} 角色的资源"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"权限不足：需要 {', '.join(allowed_roles)} 角色"
                )
            
            # 如果提供了resource和action，进一步检查权限矩阵
            if resource and action:
                has_permission = check_permission(db, current_user, resource, action)
                
                if not has_permission:
                    raise HTTPException(
                        status_code=403,
                        detail=f"权限不足：无法对 {resource} 执行 {action} 操作"
                    )
            
            logger.info(
                f"权限验证通过：{current_user.username} ({current_user.role}) "
                f"访问 {func.__name__}"
            )
            
            # 将当前用户注入到kwargs中，供路由函数使用
            kwargs['current_user'] = current_user
            
            return await func(*args, request=request, db=db, **kwargs)
        
        return wrapper
    return decorator


def require_permission(resource: str, action: str):
    """
    FastAPI路由装饰器：要求用户拥有指定资源的操作权限
    
    使用方式：
    @router.delete("/invoices/{invoice_id}")
    @require_permission(resource='invoices', action='delete')
    async def delete_invoice(invoice_id: int, current_user: User):
        pass
    
    Args:
        resource: 资源名称
        action: 操作类型
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            request: Request = None,
            db: Session = Depends(get_db),
            **kwargs
        ):
            # 获取当前用户
            current_user = get_current_user(request, db)
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="未登录或身份验证失败，请先登录"
                )
            
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
            
            # 将当前用户注入到kwargs中
            kwargs['current_user'] = current_user
            
            return await func(*args, request=request, db=db, **kwargs)
        
        return wrapper
    return decorator


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
