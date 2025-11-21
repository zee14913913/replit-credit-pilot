"""
Phase 2-1 修复 + 增强：正确的RBAC中间件实现
- 基础：使用FastAPI依赖注入系统，避免强制注入参数导致的TypeError
- 增强：多公司角色绑定（Multi-tenant Role Binding）
- Phase 2-2 Task 4: IP/User-Agent审计日志增强
- Phase 2-2 Task 7: Flask Session桥接支持
"""
from typing import Optional, Dict
from datetime import datetime
from fastapi import Header, HTTPException, Cookie, Depends, Request
from sqlalchemy.orm import Session
import logging
import os
import psycopg2

from ..db import get_db
from ..models import User, Permission, AuditLog
from ..services.auth_service import get_user_by_token, get_user_role_for_company
from ..utils.flask_session_parser import FlaskSessionParser

logger = logging.getLogger(__name__)

# Initialize Flask session parser for cross-service authentication
flask_session_parser = FlaskSessionParser()


# ========== Phase 2-2 Task 4: Request信息提取辅助函数 ==========

def extract_request_info(request: Request) -> dict:
    """
    从FastAPI Request中提取IP地址和User-Agent
    
    Args:
        request: FastAPI Request对象
    
    Returns:
        dict: {'ip_address': str, 'user_agent': str}
    """
    ip_address = None
    user_agent = None
    
    try:
        # 提取IP地址（优先从X-Forwarded-For获取真实IP）
        if request.client:
            ip_address = request.client.host
        
        # 如果有代理，从X-Forwarded-For头获取真实IP
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            ip_address = forwarded_for.split(',')[0].strip()
        
        # 提取User-Agent
        user_agent = request.headers.get('User-Agent')
    
    except Exception as e:
        logger.warning(f"提取Request信息失败: {e}")
    
    return {
        'ip_address': ip_address,
        'user_agent': user_agent
    }


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
    session_token: Optional[str] = Cookie(None),
    session: Optional[str] = Cookie(None)
) -> Optional[User]:
    """
    FastAPI依赖函数：从请求中获取当前用户
    
    认证方式优先级：
    1. Authorization header (Bearer token)
    2. Cookie (session_token) - FastAPI native session
    3. Cookie (session) - Flask session (cross-service authentication)
    
    Args:
        db: 数据库session（自动注入）
        authorization: Authorization header
        session_token: Cookie中的session_token
        session: Flask session cookie (for cross-service auth)
    
    Returns:
        User对象或None
    
    Raises:
        HTTPException: 401 未授权
    """
    token = None
    
    # 方式1：从Authorization header获取
    if authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ')[1]
        user = get_user_by_token(db, token)
        if user:
            return user
    
    # 方式2：从FastAPI session_token Cookie获取
    if session_token:
        token = session_token
        user = get_user_by_token(db, token)
        if user:
            return user
    
    # 方式3：从Flask session cookie获取（跨服务认证）
    if session:
        try:
            session_data = flask_session_parser.parse_session_cookie(session)
            if session_data:
                user_info = flask_session_parser.extract_user_from_session(session_data)
                if user_info and user_info.get('user_id'):
                    # 从数据库查找用户
                    user = db.query(User).filter(User.id == user_info['user_id']).first()
                    if user and user.is_active:
                        logger.info(f"✅ Flask session验证成功：user_id={user.id}, username={user.username}")
                        return user
                    else:
                        logger.warning(f"Flask session用户不存在或未激活：user_id={user_info['user_id']}")
        except Exception as e:
            logger.warning(f"Flask session解析失败: {e}")
    
    return None


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


# ============================================================
# Phase 2-1 增强：多公司角色绑定权限检查
# ============================================================

def require_company_access(company_id: int, min_role: Optional[str] = None):
    """
    FastAPI依赖函数工厂：要求用户有权访问指定公司
    
    使用方式：
    ```python
    @router.post("/api/companies/{company_id}/upload")
    async def upload_statement(
        company_id: int,
        user: User = Depends(require_company_access(company_id, min_role='data_entry')),
        db: Session = Depends(get_db)
    ):
        # 用户已通过公司访问权限检查
        pass
    ```
    
    Args:
        company_id: 要求访问的公司ID
        min_role: 最低角色要求（可选），如：'data_entry'表示至少需要data_entry权限
    
    Returns:
        依赖函数
    
    Raises:
        HTTPException: 403 用户无权访问该公司
    """
    def check_company_access(
        current_user: User = Depends(require_auth),
        db: Session = Depends(get_db)
    ) -> User:
        # 获取用户在该公司的角色
        user_role = get_user_role_for_company(db, current_user, company_id)
        
        if not user_role:
            # 写入审计日志：访问被拒绝
            try:
                audit_log = AuditLog(
                    company_id=company_id,
                    user_id=current_user.id,
                    username=current_user.username,
                    action_type='config_change',
                    entity_type='company_access',
                    entity_id=company_id,
                    description=f"用户尝试访问无权限的公司（Company ID: {company_id}）",
                    success=False,
                    error_message="用户无权访问该公司"
                )
                db.add(audit_log)
                db.commit()
            except Exception as e:
                logger.error(f"审计日志写入失败（访问被拒绝）：{e}")
                db.rollback()
            
            logger.warning(
                f"公司访问权限检查失败：用户 {current_user.username} "
                f"无权访问公司ID {company_id}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"权限不足：您无权访问该公司（Company ID: {company_id}）"
            )
        
        # 如果有最低角色要求，检查角色层级
        if min_role:
            if not check_role_hierarchy(user_role, min_role):
                # 写入审计日志：角色权限不足
                try:
                    audit_log = AuditLog(
                        company_id=company_id,
                        user_id=current_user.id,
                        username=current_user.username,
                        action_type='config_change',
                        entity_type='company_access',
                        entity_id=company_id,
                        description=f"用户在公司{company_id}的角色（{user_role}）不满足要求（需要至少{min_role}）",
                        success=False,
                        error_message=f"角色权限不足：{user_role} < {min_role}"
                    )
                    db.add(audit_log)
                    db.commit()
                except Exception as e:
                    logger.error(f"审计日志写入失败（角色权限不足）：{e}")
                    db.rollback()
                
                logger.warning(
                    f"公司角色权限不足：用户 {current_user.username} "
                    f"在公司 {company_id} 的角色是 {user_role}，需要至少 {min_role}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"权限不足：您在该公司的角色（{user_role}）不满足要求（需要至少{min_role}）"
                )
        
        # 写入审计日志：访问成功
        try:
            audit_log = AuditLog(
                company_id=company_id,
                user_id=current_user.id,
                username=current_user.username,
                action_type='config_change',
                entity_type='company_access',
                entity_id=company_id,
                description=f"用户以{user_role}角色访问公司{company_id}",
                success=True
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"审计日志写入失败（访问成功）：{e}")
            db.rollback()
        
        logger.info(
            f"公司访问权限检查通过：{current_user.username} ({user_role}) "
            f"访问公司 {company_id}"
        )
        
        return current_user
    
    return check_company_access


def get_user_company_role(company_id: int):
    """
    FastAPI依赖函数工厂：获取用户在指定公司的角色（不抛出异常）
    
    使用方式：
    ```python
    @router.get("/api/companies/{company_id}/info")
    async def get_company_info(
        company_id: int,
        user_role: Optional[str] = Depends(get_user_company_role(company_id)),
        current_user: User = Depends(require_auth),
        db: Session = Depends(get_db)
    ):
        if not user_role:
            return {"message": "您无权访问该公司"}
        
        # 根据角色返回不同数据
        if user_role in ['admin', 'accountant']:
            return {"full_data": True}
        else:
            return {"limited_data": True}
    ```
    
    Args:
        company_id: 公司ID
    
    Returns:
        依赖函数，返回角色字符串或None
    """
    def get_role(
        current_user: User = Depends(require_auth),
        db: Session = Depends(get_db)
    ) -> Optional[str]:
        return get_user_role_for_company(db, current_user, company_id)
    
    return get_role


# ============================================================
# Phase 2-2 Task 7: Flask Session桥接支持
# ============================================================

def get_flask_session_user(request: Request) -> Optional[Dict]:
    """
    从FastAPI Request中提取Flask session并验证用户
    
    用于API密钥管理等需要Flask session认证的路由
    
    Args:
        request: FastAPI Request对象
    
    Returns:
        dict: 用户信息字典 {'id', 'username', 'role', 'company_id'}
        None: 如果session无效或用户未登录
    """
    try:
        # 从Cookie中获取session
        session_cookie = request.cookies.get('session')
        if not session_cookie:
            logger.debug("No Flask session cookie found")
            return None
        
        # 解析Flask session获取user_id
        # Flask session的格式: session cookie包含加密数据
        # 我们需要从PostgreSQL直接验证flask_rbac_user_id
        
        # 简化方案：直接从cookie中获取flask_rbac_user_id
        # 注意：这需要Flask session使用server-side storage或shared secret
        
        # 暂时返回None，因为我们需要实现完整的Flask session解析
        # 或者使用共享数据库来存储session信息
        logger.warning("Flask session parsing not fully implemented yet")
        return None
        
    except Exception as e:
        logger.error(f"Failed to parse Flask session: {e}")
        return None


def require_flask_session_user(request: Request) -> Dict:
    """
    FastAPI依赖函数：要求有效的Flask session
    
    用于API密钥管理路由等需要Flask认证的端点
    
    Args:
        request: FastAPI Request对象
    
    Returns:
        dict: 用户信息字典
    
    Raises:
        HTTPException: 401/403 如果未登录或session无效
    """
    user = get_flask_session_user(request)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Flask session required. Please log in through the admin interface."
        )
    
    return user
