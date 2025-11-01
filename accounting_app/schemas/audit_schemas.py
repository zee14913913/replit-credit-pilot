"""
Phase 1-4: 审计日志Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogCreate(BaseModel):
    """创建审计日志请求"""
    action_type: str = Field(..., description="操作类型: export, delete, rule_change, manual_entry等")
    description: str = Field(..., description="操作描述")
    company_id: Optional[int] = Field(None, description="公司ID")
    username: Optional[str] = Field(None, description="操作人")
    user_id: Optional[int] = Field(None, description="用户ID")
    entity_type: Optional[str] = Field(None, description="实体类型")
    entity_id: Optional[int] = Field(None, description="实体ID")
    reason: Optional[str] = Field(None, description="操作原因（手工改账/删除必填）")
    old_value: Optional[Dict[str, Any]] = Field(None, description="修改前的值")
    new_value: Optional[Dict[str, Any]] = Field(None, description="修改后的值")
    success: bool = Field(True, description="操作是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int
    company_id: Optional[int]
    user_id: Optional[int]
    username: Optional[str]
    action_type: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    description: str
    reason: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_method: Optional[str]
    request_path: Optional[str]
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    success: bool
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    """审计日志列表响应"""
    total: int
    items: list[AuditLogResponse]


class AuditLogFilter(BaseModel):
    """审计日志查询过滤器"""
    company_id: Optional[int] = None
    action_type: Optional[str] = None
    entity_type: Optional[str] = None
    username: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    success: Optional[bool] = None
