"""
Phase 2-1 修复 + 增强：Session认证服务
- 基础：临时token认证系统（生产环境需要JWT）
- 增强：多公司角色绑定（Multi-tenant Role Binding）
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import logging

from ..models import User, UserCompanyRole, Company, AuditLog
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


# ============================================================
# Phase 2-1 增强：多公司角色绑定功能
# ============================================================

def get_user_companies(db: Session, user: User) -> List[Dict]:
    """
    获取用户可访问的所有公司及其对应角色
    
    Args:
        db: 数据库session
        user: User对象
    
    Returns:
        List[Dict]: [
            {
                'company_id': 1,
                'company_code': 'GZ001',
                'company_name': 'XX有限公司',
                'role': 'accountant',
                'created_at': '2025-01-01T10:00:00'
            },
            ...
        ]
    """
    # 查询用户在所有公司的角色
    company_roles = db.query(UserCompanyRole).filter(
        UserCompanyRole.user_id == user.id
    ).all()
    
    result = []
    for ucr in company_roles:
        company = db.query(Company).filter(Company.id == ucr.company_id).first()
        if company:
            result.append({
                'company_id': ucr.company_id,
                'company_code': company.company_code,
                'company_name': company.company_name,
                'role': ucr.role,
                'created_at': ucr.created_at.isoformat()
            })
    
    # 如果user_company_roles表没有数据，回退到users表的company_id（向后兼容）
    if not result and user.company_id:
        company = db.query(Company).filter(Company.id == user.company_id).first()
        if company:
            result.append({
                'company_id': user.company_id,
                'company_code': company.company_code,
                'company_name': company.company_name,
                'role': user.role,
                'created_at': user.created_at.isoformat()
            })
            logger.warning(f"用户 {user.username} 在user_company_roles表无数据，使用users表的company_id回退")
    
    return result


def get_user_role_for_company(db: Session, user: User, company_id: int) -> Optional[str]:
    """
    获取用户在特定公司的角色
    
    Args:
        db: 数据库session
        user: User对象
        company_id: 公司ID
    
    Returns:
        str: 角色名称（admin/accountant/viewer/data_entry/loan_officer）
        None: 用户在该公司无权限
    """
    # 先查询user_company_roles表
    ucr = db.query(UserCompanyRole).filter(
        UserCompanyRole.user_id == user.id,
        UserCompanyRole.company_id == company_id
    ).first()
    
    if ucr:
        return ucr.role
    
    # 回退到users表（向后兼容）
    if user.company_id == company_id:
        return user.role
    
    # 用户对该公司无权限
    return None


def assign_user_to_company(
    db: Session,
    user_id: int,
    company_id: int,
    role: str,
    created_by: Optional[int] = None
) -> UserCompanyRole:
    """
    将用户分配到公司并授予角色
    
    Args:
        db: 数据库session
        user_id: 用户ID
        company_id: 公司ID
        role: 角色（admin/accountant/viewer/data_entry/loan_officer）
        created_by: 授权人ID（可选）
    
    Returns:
        UserCompanyRole对象
    
    Raises:
        ValueError: 用户或公司不存在
    """
    # 验证用户和公司是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"用户ID {user_id} 不存在")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValueError(f"公司ID {company_id} 不存在")
    
    valid_roles = ['admin', 'accountant', 'viewer', 'data_entry', 'loan_officer']
    if role not in valid_roles:
        raise ValueError(f"无效的角色：{role}，必须是 {', '.join(valid_roles)} 之一")
    
    # 检查是否已存在
    existing_ucr = db.query(UserCompanyRole).filter(
        UserCompanyRole.user_id == user_id,
        UserCompanyRole.company_id == company_id
    ).first()
    
    if existing_ucr:
        # 更新角色（审计日志）
        old_role = existing_ucr.role
        
        # 正确的更新方式（直接使用query.update）
        db.query(UserCompanyRole).filter(
            UserCompanyRole.id == existing_ucr.id
        ).update({
            'role': role,
            'updated_at': datetime.now()
        }, synchronize_session=False)
        db.commit()
        
        # 重新查询获取更新后的对象
        updated_ucr = db.query(UserCompanyRole).filter(
            UserCompanyRole.id == existing_ucr.id
        ).first()
        
        # 写入审计日志（防御性）
        try:
            audit_log = AuditLog(
                company_id=company_id,
                user_id=created_by if created_by else None,
                username=user.username,
                action_type='role_change',
                entity_type='user_company_role',
                entity_id=existing_ucr.id,
                description=f"更新用户 {user.username} 在公司 {company.company_name} 的角色",
                old_value={'role': old_role},
                new_value={'role': role},
                success=True
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"审计日志写入失败（角色更新）：{e}")
            db.rollback()
        
        logger.info(f"更新用户 {user.username} 在公司 {company.company_name} 的角色：{old_role} → {role}")
        return updated_ucr
    else:
        # 创建新关联
        new_ucr = UserCompanyRole(
            user_id=user_id,
            company_id=company_id,
            role=role,
            created_by=created_by
        )
        db.add(new_ucr)
        db.commit()
        db.refresh(new_ucr)
        
        # 写入审计日志（防御性）
        try:
            audit_log = AuditLog(
                company_id=company_id,
                user_id=created_by if created_by else None,
                username=user.username,
                action_type='role_change',
                entity_type='user_company_role',
                entity_id=new_ucr.id,
                description=f"将用户 {user.username} 分配到公司 {company.company_name}",
                new_value={'role': role, 'company_id': company_id},
                success=True
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"审计日志写入失败（角色分配）：{e}")
            db.rollback()
        
        logger.info(f"将用户 {user.username} 分配到公司 {company.company_name}，角色为 {role}")
        return new_ucr


def remove_user_from_company(
    db: Session, 
    user_id: int, 
    company_id: int,
    removed_by: Optional[int] = None
) -> bool:
    """
    移除用户对某个公司的访问权限（写入审计日志）
    
    Args:
        db: 数据库session
        user_id: 用户ID
        company_id: 公司ID
        removed_by: 执行移除操作的管理员ID（可选）
    
    Returns:
        bool: 是否成功移除
    """
    ucr = db.query(UserCompanyRole).filter(
        UserCompanyRole.user_id == user_id,
        UserCompanyRole.company_id == company_id
    ).first()
    
    if ucr:
        user = db.query(User).filter(User.id == user_id).first()
        company = db.query(Company).filter(Company.id == company_id).first()
        
        old_role = ucr.role
        
        # 删除关联
        db.delete(ucr)
        db.commit()
        
        # 写入审计日志（防御性）
        try:
            audit_log = AuditLog(
                company_id=company_id,
                user_id=removed_by if removed_by else None,
                username=user.username if user else f"User#{user_id}",
                action_type='delete',
                entity_type='user_company_role',
                entity_id=ucr.id,
                description=f"移除用户 {user.username if user else user_id} 对公司 {company.company_name if company else company_id} 的访问权限",
                old_value={'role': old_role, 'company_id': company_id},
                success=True
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"审计日志写入失败（移除权限）：{e}")
            db.rollback()
        
        logger.info(f"移除用户 {user.username if user else user_id} 对公司 {company.company_name if company else company_id} 的访问权限")
        return True
    
    return False
