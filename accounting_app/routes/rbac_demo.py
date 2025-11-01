"""
Phase 2-1: RBAC权限系统演示路由
展示如何使用require_role和require_permission装饰器
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import hashlib

from ..db import get_db
from ..models import User, Permission
from ..middleware.rbac import require_role, require_permission, check_permission

router = APIRouter(prefix="/api/rbac", tags=["RBAC Demo (Phase 2-1)"])


@router.get("/users")
async def list_users(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ## 🔒 列出所有用户（需要admin或accountant角色）
    
    **权限要求**：
    - 角色：admin 或 accountant
    
    **示例**：
    ```bash
    GET /api/rbac/users?user_id=1
    ```
    """
    # 临时方案：从query参数获取user_id
    user_id = request.query_params.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="请提供user_id参数（临时开发方案）")
    
    current_user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="用户不存在或未激活")
    
    # 权限检查
    if current_user.role not in ['admin', 'accountant']:
        raise HTTPException(status_code=403, detail="权限不足：需要admin或accountant角色")
    
    # 查询用户列表
    users = db.query(User).filter(
        User.company_id == current_user.company_id
    ).all()
    
    return {
        "success": True,
        "current_user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role
        },
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "last_login": u.last_login.isoformat() if u.last_login else None
            }
            for u in users
        ],
        "total": len(users)
    }


@router.post("/users")
async def create_user(
    request: Request,
    username: str,
    email: str,
    password: str,
    full_name: str,
    role: str,
    db: Session = Depends(get_db)
):
    """
    ## 🔒 创建新用户（仅限admin）
    
    **权限要求**：
    - 角色：admin
    
    **支持的角色**：
    - `admin` - 系统管理员（完全权限）
    - `accountant` - 会计师（财务数据读写）
    - `viewer` - 查看者（只读权限）
    - `data_entry` - 数据录入员（上传和录入）
    - `loan_officer` - 贷款专员（贷款业务管理）
    
    **示例**：
    ```bash
    POST /api/rbac/users?user_id=1
    {
        "username": "john_doe",
        "email": "john@company.com",
        "password": "SecurePass123",
        "full_name": "John Doe",
        "role": "accountant"
    }
    ```
    """
    # 临时方案：从query参数获取user_id
    user_id = request.query_params.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="请提供user_id参数（临时开发方案）")
    
    current_user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="用户不存在或未激活")
    
    # 权限检查：仅admin可以创建用户
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足：仅admin可以创建用户")
    
    # 验证角色合法性
    valid_roles = ['admin', 'accountant', 'viewer', 'data_entry', 'loan_officer']
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"无效的角色：{role}，必须是 {', '.join(valid_roles)} 之一")
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(
        User.company_id == current_user.company_id,
        User.username == username
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail=f"用户名 {username} 已存在")
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(
        User.company_id == current_user.company_id,
        User.email == email
    ).first()
    
    if existing_email:
        raise HTTPException(status_code=400, detail=f"邮箱 {email} 已被使用")
    
    # 创建密码hash（SHA-256）
    password_hash = f"SHA256:{hashlib.sha256(password.encode()).hexdigest()}"
    
    # 创建新用户
    new_user = User(
        company_id=current_user.company_id,
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
    
    return {
        "success": True,
        "message": f"用户 {username} 创建成功",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "created_at": new_user.created_at.isoformat()
        }
    }


@router.get("/permissions")
async def list_permissions(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ## 📋 查看权限矩阵（所有登录用户可访问）
    
    **权限要求**：已登录
    
    **示例**：
    ```bash
    GET /api/rbac/permissions?user_id=1
    ```
    """
    # 临时方案：从query参数获取user_id
    user_id = request.query_params.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="请提供user_id参数（临时开发方案）")
    
    current_user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="用户不存在或未激活")
    
    # 查询所有权限
    permissions = db.query(Permission).order_by(Permission.role, Permission.resource, Permission.action).all()
    
    # 按角色分组
    permissions_by_role = {}
    for perm in permissions:
        if perm.role not in permissions_by_role:
            permissions_by_role[perm.role] = []
        permissions_by_role[perm.role].append({
            "resource": perm.resource,
            "action": perm.action,
            "allowed": perm.allowed,
            "description": perm.description
        })
    
    return {
        "success": True,
        "current_user": {
            "username": current_user.username,
            "role": current_user.role
        },
        "permissions_matrix": permissions_by_role,
        "total_permissions": len(permissions)
    }


@router.get("/check-permission")
async def check_my_permission(
    request: Request,
    resource: str,
    action: str,
    db: Session = Depends(get_db)
):
    """
    ## 🔍 检查当前用户对指定资源的权限
    
    **参数**：
    - `resource` - 资源名称（如：bank_statements, invoices）
    - `action` - 操作类型（如：create, read, update, delete, export）
    
    **示例**：
    ```bash
    GET /api/rbac/check-permission?user_id=1&resource=invoices&action=delete
    ```
    """
    # 临时方案：从query参数获取user_id
    user_id = request.query_params.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="请提供user_id参数（临时开发方案）")
    
    current_user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="用户不存在或未激活")
    
    # 检查权限
    has_permission = check_permission(db, current_user, resource, action)
    
    return {
        "success": True,
        "user": {
            "username": current_user.username,
            "role": current_user.role
        },
        "permission_check": {
            "resource": resource,
            "action": action,
            "allowed": has_permission
        },
        "message": f"{'✅ 有权限' if has_permission else '❌ 无权限'} 对 {resource} 执行 {action} 操作"
    }


@router.get("/my-info")
async def get_my_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ## 👤 获取当前用户信息
    
    **权限要求**：已登录
    
    **示例**：
    ```bash
    GET /api/rbac/my-info?user_id=1
    ```
    """
    # 临时方案：从query参数获取user_id
    user_id = request.query_params.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="请提供user_id参数（临时开发方案）")
    
    current_user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="用户不存在或未激活")
    
    # 查询当前用户的所有权限
    my_permissions = db.query(Permission).filter(
        Permission.role == current_user.role,
        Permission.allowed == True
    ).all()
    
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "created_at": current_user.created_at.isoformat()
        },
        "permissions": [
            {
                "resource": p.resource,
                "action": p.action,
                "description": p.description
            }
            for p in my_permissions
        ],
        "total_permissions": len(my_permissions)
    }
