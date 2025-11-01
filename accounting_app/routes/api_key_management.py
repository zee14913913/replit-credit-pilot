"""
Phase 2-2 Task 5: API密钥管理路由

提供API密钥的CRUD操作：
1. 创建新密钥
2. 列出当前用户的密钥
3. 撤销密钥
4. 更新密钥权限
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging

from accounting_app.services.api_key_service import APIKeyService
from accounting_app.middleware.rbac_fixed import get_current_user
from accounting_app.utils.audit_logger import AuditLogger, extract_request_info
from accounting_app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/api-keys", tags=["API Key Management"])


# ========== Pydantic Models ==========

class APIKeyCreateRequest(BaseModel):
    """创建API密钥请求"""
    name: str = Field(..., min_length=1, max_length=255, description="密钥名称（如：Production API Key）")
    environment: str = Field(default="live", description="环境：live 或 test")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    rate_limit: int = Field(default=100, ge=1, le=10000, description="每分钟请求限制")
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365, description="过期天数（None=永不过期）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Production API Key",
                "environment": "live",
                "permissions": ["export:bank_statements", "read:transactions"],
                "rate_limit": 100,
                "expires_in_days": 365
            }
        }


class APIKeyResponse(BaseModel):
    """API密钥响应（创建时包含明文密钥）"""
    id: int
    api_key: str = Field(..., description="⚠️ 明文密钥，仅此一次显示！请妥善保存")
    key_prefix: str
    name: str
    environment: str
    permissions: List[str]
    created_at: str


class APIKeyListItem(BaseModel):
    """API密钥列表项（不包含明文密钥）"""
    id: int
    key_prefix: str
    name: str
    environment: str
    permissions: List[str]
    rate_limit: int
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]


class APIKeyRevokeRequest(BaseModel):
    """撤销API密钥请求"""
    reason: str = Field(..., min_length=1, description="撤销原因")


# ========== API Routes ==========

@router.post("/", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: dict = Depends(get_current_user),
    req: Request = None,
    db: Session = Depends(get_db)
):
    """
    创建新的API密钥
    
    **⚠️ 重要：明文密钥仅在创建时返回一次，请妥善保存！**
    
    权限要求：admin 或 accountant 角色
    """
    # 1. 权限检查（仅admin和accountant可创建API密钥）
    if current_user["role"] not in ["admin", "accountant"]:
        # 记录权限失败审计日志
        audit_logger = AuditLogger(db)
        try:
            req_info = extract_request_info(req) if req else {}
            audit_logger.log(
                action_type="config_change",
                description=f"创建API密钥失败: 权限不足 (role={current_user['role']})",
                company_id=current_user["company_id"],
                user_id=current_user["id"],
                username=current_user["username"],
                entity_type="api_key",
                success=False,
                error_message=f"Insufficient permissions: {current_user['role']}",
                **req_info
            )
        finally:
            audit_logger.close()
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and accountant roles can create API keys"
        )
    
    # 2. 验证环境值
    if request.environment not in ["live", "test"]:
        # 记录验证失败审计日志
        audit_logger = AuditLogger(db)
        try:
            req_info = extract_request_info(req) if req else {}
            audit_logger.log(
                action_type="config_change",
                description=f"创建API密钥失败: 无效环境值 (environment={request.environment})",
                company_id=current_user["company_id"],
                user_id=current_user["id"],
                username=current_user["username"],
                entity_type="api_key",
                success=False,
                error_message=f"Invalid environment: {request.environment}",
                **req_info
            )
        finally:
            audit_logger.close()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid environment. Must be 'live' or 'test'"
        )
    
    # 3. 创建API密钥
    try:
        api_key_service = APIKeyService()
        result = api_key_service.create_api_key(
            user_id=current_user["id"],
            company_id=current_user["company_id"],
            name=request.name,
            permissions=request.permissions,
            environment=request.environment,
            rate_limit=request.rate_limit,
            expires_in_days=request.expires_in_days,
            created_by=current_user["id"]
        )
        
        # 4. 写入审计日志
        audit_logger = AuditLogger(db)
        try:
            req_info = extract_request_info(req) if req else {}
            audit_logger.log(
                action_type="config_change",
                description=f"创建API密钥: {request.name} (environment={request.environment})",
                company_id=current_user["company_id"],
                user_id=current_user["id"],
                username=current_user["username"],
                entity_type="api_key",
                entity_id=result["id"],
                success=True,
                new_value={
                    "name": request.name,
                    "environment": request.environment,
                    "permissions": request.permissions,
                    "rate_limit": request.rate_limit
                },
                **req_info
            )
        finally:
            audit_logger.close()
        
        logger.info(
            f"API密钥创建成功: id={result['id']}, "
            f"user={current_user['username']}, name={request.name}"
        )
        
        return APIKeyResponse(**result)
    
    except HTTPException:
        # HTTPException直接向上抛出（不记录重复审计日志）
        raise
    except Exception as e:
        logger.error(f"创建API密钥失败: {e}")
        
        # 写入失败审计日志
        audit_logger = AuditLogger(db)
        try:
            req_info = extract_request_info(req) if req else {}
            audit_logger.log(
                action_type="config_change",
                description=f"创建API密钥失败: {request.name}",
                company_id=current_user["company_id"],
                user_id=current_user["id"],
                username=current_user["username"],
                entity_type="api_key",
                success=False,
                error_message=str(e),
                **req_info
            )
        finally:
            audit_logger.close()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/", response_model=List[APIKeyListItem])
async def list_api_keys(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    列出当前用户的API密钥
    
    权限要求：所有已认证用户
    
    Args:
        include_inactive: 是否包含已撤销的密钥
    """
    try:
        api_key_service = APIKeyService()
        
        # 根据角色决定查询范围
        if current_user["role"] == "admin":
            # Admin可以查看公司所有密钥
            keys = api_key_service.list_api_keys(
                company_id=current_user["company_id"],
                include_inactive=include_inactive
            )
        else:
            # 其他用户只能查看自己的密钥
            keys = api_key_service.list_api_keys(
                user_id=current_user["id"],
                include_inactive=include_inactive
            )
        
        return [APIKeyListItem(**key) for key in keys]
    
    except Exception as e:
        logger.error(f"列出API密钥失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    request: APIKeyRevokeRequest,
    current_user: dict = Depends(get_current_user),
    req: Request = None,
    db: Session = Depends(get_db)
):
    """
    撤销API密钥
    
    权限要求：密钥所有者 或 admin角色
    """
    try:
        api_key_service = APIKeyService()
        
        # 1. 检查密钥是否存在且属于当前用户/公司
        keys = api_key_service.list_api_keys(
            company_id=current_user["company_id"],
            include_inactive=False
        )
        
        target_key = next((k for k in keys if k["id"] == key_id), None)
        
        if not target_key:
            # 记录密钥不存在审计日志
            audit_logger = AuditLogger(db)
            try:
                req_info = extract_request_info(req) if req else {}
                audit_logger.log(
                    action_type="config_change",
                    description=f"撤销API密钥失败: 密钥不存在或已撤销 (key_id={key_id})",
                    company_id=current_user["company_id"],
                    user_id=current_user["id"],
                    username=current_user["username"],
                    entity_type="api_key",
                    entity_id=key_id,
                    reason=request.reason,
                    success=False,
                    error_message="API key not found or already revoked",
                    **req_info
                )
            finally:
                audit_logger.close()
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or already revoked"
            )
        
        # 2. 权限检查（仅密钥所有者或admin可撤销）
        if current_user["role"] != "admin" and target_key["user_id"] != current_user["id"]:
            # 记录权限不足审计日志
            audit_logger = AuditLogger(db)
            try:
                req_info = extract_request_info(req) if req else {}
                audit_logger.log(
                    action_type="config_change",
                    description=f"撤销API密钥失败: 权限不足 (key_id={key_id}, owner_id={target_key['user_id']})",
                    company_id=current_user["company_id"],
                    user_id=current_user["id"],
                    username=current_user["username"],
                    entity_type="api_key",
                    entity_id=key_id,
                    reason=request.reason,
                    success=False,
                    error_message="Insufficient permissions to revoke this API key",
                    **req_info
                )
            finally:
                audit_logger.close()
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revoke your own API keys"
            )
        
        # 3. 撤销密钥
        success = api_key_service.revoke_api_key(
            key_id=key_id,
            revoked_by=current_user["id"],
            reason=request.reason
        )
        
        if not success:
            # 记录撤销失败审计日志
            audit_logger = AuditLogger(db)
            try:
                req_info = extract_request_info(req) if req else {}
                audit_logger.log(
                    action_type="config_change",
                    description=f"撤销API密钥失败: 操作失败 (key_id={key_id})",
                    company_id=current_user["company_id"],
                    user_id=current_user["id"],
                    username=current_user["username"],
                    entity_type="api_key",
                    entity_id=key_id,
                    reason=request.reason,
                    success=False,
                    error_message="Failed to revoke API key",
                    **req_info
                )
            finally:
                audit_logger.close()
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or already revoked"
            )
        
        # 4. 写入审计日志
        audit_logger = AuditLogger(db)
        try:
            req_info = extract_request_info(req) if req else {}
            audit_logger.log(
                action_type="config_change",
                description=f"撤销API密钥: {target_key['name']}",
                company_id=current_user["company_id"],
                user_id=current_user["id"],
                username=current_user["username"],
                entity_type="api_key",
                entity_id=key_id,
                reason=request.reason,
                success=True,
                old_value={"is_active": True},
                new_value={"is_active": False, "revoked_reason": request.reason},
                **req_info
            )
        finally:
            audit_logger.close()
        
        logger.info(
            f"API密钥已撤销: id={key_id}, "
            f"by={current_user['username']}, reason={request.reason}"
        )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"撤销API密钥失败: {e}")
        
        # 写入失败审计日志
        audit_logger = AuditLogger(db)
        try:
            req_info = extract_request_info(req) if req else {}
            audit_logger.log(
                action_type="config_change",
                description=f"撤销API密钥失败: key_id={key_id}",
                company_id=current_user["company_id"],
                user_id=current_user["id"],
                username=current_user["username"],
                entity_type="api_key",
                entity_id=key_id,
                success=False,
                error_message=str(e),
                **req_info
            )
        finally:
            audit_logger.close()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.get("/{key_id}", response_model=APIKeyListItem)
async def get_api_key_details(
    key_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取API密钥详情
    
    权限要求：密钥所有者 或 admin角色
    """
    try:
        api_key_service = APIKeyService()
        
        # 查询密钥
        keys = api_key_service.list_api_keys(
            company_id=current_user["company_id"],
            include_inactive=True
        )
        
        target_key = next((k for k in keys if k["id"] == key_id), None)
        
        if not target_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # 权限检查
        if current_user["role"] != "admin" and target_key["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own API keys"
            )
        
        return APIKeyListItem(**target_key)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取API密钥详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key details: {str(e)}"
        )
