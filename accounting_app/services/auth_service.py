"""
Phase 2-1 修复：简单的session认证服务
临时token认证系统（生产环境需要JWT）
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import logging

from ..models import User
from ..utils.password import hash_password, verify_password

logger = logging.getLogger(__name__)

# 临时Session存储（生产环境应使用Redis）
# 格式：{token: {user_id, expires_at, company_id}}
_session_store = {}


def create_user(
    db: Session,
    company_id: int,
    username: str,
    email: str,
    password: str,
    full_name: str,
    role: str
) -> User:
    """
    创建新用户（使用bcrypt hash）
    
    Args:
        db: 数据库session
        company_id: 公司ID
        username: 用户名
        email: 邮箱
        password: 明文密码
        full_name: 全名
        role: 角色（admin/accountant/viewer/data_entry/loan_officer）
    
    Returns:
        User对象
    
    Raises:
        ValueError: 用户名或邮箱已存在
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(
        User.company_id == company_id,
        User.username == username
    ).first()
    
    if existing_user:
        raise ValueError(f"用户名 {username} 已存在")
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(
        User.company_id == company_id,
        User.email == email
    ).first()
    
    if existing_email:
        raise ValueError(f"邮箱 {email} 已被使用")
    
    # 创建bcrypt hash
    password_hash = hash_password(password)
    
    # 创建用户
    new_user = User(
        company_id=company_id,
        username=username,
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"新用户创建成功：{username} ({role})")
    
    return new_user


def authenticate_user(
    db: Session,
    username: str,
    password: str,
    company_id: Optional[int] = None
) -> Optional[User]:
    """
    验证用户凭据
    
    Args:
        db: 数据库session
        username: 用户名或邮箱
        password: 明文密码
        company_id: 可选，公司ID（多租户隔离）
    
    Returns:
        User对象（成功）或None（失败）
    """
    # 查询用户（支持用户名或邮箱登录）
    query = db.query(User).filter(
        (User.username == username) | (User.email == username),
        User.is_active == True
    )
    
    if company_id:
        query = query.filter(User.company_id == company_id)
    
    user = query.first()
    
    if not user:
        logger.warning(f"登录失败：用户 {username} 不存在")
        return None
    
    # 验证密码
    if not verify_password(password, user.password_hash):
        logger.warning(f"登录失败：用户 {username} 密码错误")
        return None
    
    logger.info(f"用户登录成功：{user.username} ({user.role})")
    
    return user


def create_session(user: User, expires_in_hours: int = 24) -> str:
    """
    为用户创建session token
    
    Args:
        user: User对象
        expires_in_hours: token过期时间（小时）
    
    Returns:
        session_token字符串
    """
    # 生成随机token
    token = secrets.token_urlsafe(32)
    
    # 计算过期时间
    expires_at = datetime.now() + timedelta(hours=expires_in_hours)
    
    # 存储session
    _session_store[token] = {
        'user_id': user.id,
        'company_id': user.company_id,
        'username': user.username,
        'role': user.role,
        'expires_at': expires_at
    }
    
    logger.info(f"Session创建成功：user={user.username}, token={token[:8]}..., expires={expires_at}")
    
    return token


def verify_session(token: str) -> Optional[dict]:
    """
    验证session token
    
    Args:
        token: session token
    
    Returns:
        session数据（成功）或None（失败）
    """
    if not token:
        return None
    
    session = _session_store.get(token)
    
    if not session:
        logger.warning(f"Session验证失败：token不存在")
        return None
    
    # 检查是否过期
    if session['expires_at'] < datetime.now():
        logger.warning(f"Session已过期：user={session['username']}")
        # 删除过期session
        del _session_store[token]
        return None
    
    return session


def get_user_by_token(db: Session, token: str) -> Optional[User]:
    """
    通过session token获取用户对象
    
    Args:
        db: 数据库session
        token: session token
    
    Returns:
        User对象（成功）或None（失败）
    """
    session = verify_session(token)
    
    if not session:
        return None
    
    # 从数据库获取最新的用户数据
    user = db.query(User).filter(
        User.id == session['user_id'],
        User.is_active == True
    ).first()
    
    if not user:
        logger.warning(f"Session验证失败：用户已被删除或禁用")
        # 删除无效session
        del _session_store[token]
        return None
    
    return user


def revoke_session(token: str) -> bool:
    """
    撤销session（登出）
    
    Args:
        token: session token
    
    Returns:
        bool: 是否成功
    """
    if token in _session_store:
        username = _session_store[token].get('username')
        del _session_store[token]
        logger.info(f"Session已撤销：user={username}")
        return True
    
    return False


def cleanup_expired_sessions():
    """
    清理过期的sessions（定期任务）
    """
    now = datetime.now()
    expired_tokens = [
        token for token, session in _session_store.items()
        if session['expires_at'] < now
    ]
    
    for token in expired_tokens:
        del _session_store[token]
    
    if expired_tokens:
        logger.info(f"清理了 {len(expired_tokens)} 个过期session")
