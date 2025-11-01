"""
Phase 2-1 修复：认证API路由
提供登录、登出、注册等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Response, Header, Cookie
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..db import get_db
from ..models import User
from ..services.auth_service import (
    authenticate_user,
    create_session,
    revoke_session,
    create_user,
    get_user_companies  # Phase 2-1 增强：多公司角色
)
import logging

logger = logging.getLogger(__name__)
from ..middleware.rbac_fixed import require_auth, require_role

router = APIRouter(prefix="/api/auth", tags=["Authentication (Phase 2-1 Fixed)"])


class LoginRequest(BaseModel):
    """登录请求"""
    username: str  # 用户名或邮箱
    password: str
    company_id: Optional[int] = None  # 可选，多租户场景


class RegisterRequest(BaseModel):
    """注册请求"""
    company_id: int
    username: str
    email: str
    password: str
    full_name: str
    role: str = 'viewer'  # 默认viewer角色


@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    ## 🔐 用户登录
    
    **请求示例**：
    ```json
    {
        "username": "admin",
        "password": "admin123",
        "company_id": 1
    }
    ```
    
    **成功响应**：
    - 返回session_token
    - 自动设置Cookie (session_token)
    
    **失败响应**：
    - 401: 用户名或密码错误
    """
    # 验证用户凭据
    user = authenticate_user(
        db=db,
        username=request.username,
        password=request.password,
        company_id=request.company_id
    )
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    # 创建session
    token = create_session(user, expires_in_hours=24)
    
    # 设置Cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,  # 防止XSS
        max_age=24 * 3600,  # 24小时
        samesite="lax"
    )
    
    # 更新最后登录时间
    user.last_login = db.query(User).filter(User.id == user.id).first().created_at
    db.commit()
    
    return {
        "success": True,
        "message": "登录成功",
        "token": token,  # 也返回token供header使用
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_id": user.company_id
        }
    }


@router.post("/logout")
async def logout(
    response: Response,
    authorization: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None),
    current_user: User = Depends(require_auth)
):
    """
    ## 🚪 用户登出
    
    **权限要求**：已登录
    
    **响应**：
    - 撤销服务器端session
    - 清除Cookie
    """
    # 获取当前token（从header或cookie）
    token = None
    
    if authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ')[1]
    elif session_token:
        token = session_token
    
    # 撤销服务器端session（关键修复）
    if token:
        revoked = revoke_session(token)
        if not revoked:
            logger.warning(f"登出时token已不存在：{current_user.username}")
    else:
        logger.warning(f"登出时未找到token：{current_user.username}")
    
    # 清除Cookie
    response.delete_cookie("session_token")
    
    return {
        "success": True,
        "message": f"用户 {current_user.username} 已登出",
        "token_revoked": bool(token and revoked) if token else False
    }


@router.post("/register")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    ## 📝 用户注册（仅限admin创建其他用户）
    
    **注意**：此接口暂时公开，生产环境应限制为仅admin可调用
    
    **请求示例**：
    ```json
    {
        "company_id": 1,
        "username": "john_doe",
        "email": "john@company.com",
        "password": "SecurePass123",
        "full_name": "John Doe",
        "role": "accountant"
    }
    ```
    
    **支持的角色**：
    - `admin` - 系统管理员
    - `accountant` - 会计师
    - `viewer` - 查看者
    - `data_entry` - 数据录入员
    - `loan_officer` - 贷款专员
    """
    valid_roles = ['admin', 'accountant', 'viewer', 'data_entry', 'loan_officer']
    
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"无效的角色：{request.role}，必须是 {', '.join(valid_roles)} 之一"
        )
    
    try:
        new_user = create_user(
            db=db,
            company_id=request.company_id,
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            role=request.role
        )
        
        return {
            "success": True,
            "message": f"用户 {request.username} 创建成功",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": new_user.role,
                "created_at": new_user.created_at.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    ## 👤 获取当前登录用户信息（Phase 2-1 增强版）
    
    **权限要求**：已登录
    
    **响应**：
    - 用户基本信息
    - 用户可访问的所有公司及角色（多租户支持）
    - 角色权限
    
    **重要变更**：
    - 新增 `companies` 字段：返回用户可访问的所有公司列表
    - 每个公司包含：company_id, company_code, company_name, role
    - 支持同一用户在不同公司拥有不同角色
    """
    from ..models import Permission
    
    # Phase 2-1 增强：获取用户可访问的所有公司
    user_companies = get_user_companies(db, current_user)
    
    # 查询当前用户的权限（基于主要角色）
    permissions = db.query(Permission).filter(
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
            "role": current_user.role,  # 主要角色（向后兼容）
            "company_id": current_user.company_id,  # 主要公司（向后兼容）
            "is_active": current_user.is_active,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "created_at": current_user.created_at.isoformat()
        },
        "companies": user_companies,  # 【新增】用户可访问的所有公司及角色
        "total_companies": len(user_companies),  # 【新增】可访问公司数量
        "permissions": [
            {
                "resource": p.resource,
                "action": p.action,
                "description": p.description
            }
            for p in permissions
        ],
        "total_permissions": len(permissions)
    }


@router.get("/test-auth")
async def test_auth(
    current_user: User = Depends(require_auth)
):
    """
    ## 🧪 测试认证是否工作
    
    **权限要求**：已登录
    """
    return {
        "success": True,
        "message": "认证成功！",
        "user": {
            "username": current_user.username,
            "role": current_user.role
        }
    }


@router.get("/test-admin")
async def test_admin_only(
    current_user: User = Depends(require_role('admin'))
):
    """
    ## 🧪 测试admin角色限制
    
    **权限要求**：admin角色
    """
    return {
        "success": True,
        "message": "你是admin！",
        "user": {
            "username": current_user.username,
            "role": current_user.role
        }
    }
