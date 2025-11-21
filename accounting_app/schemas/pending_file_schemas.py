
"""
Phase 1-11: 文件上传确认系统 - Pydantic Schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class PendingFileExtractedInfo(BaseModel):
    """OCR提取的信息"""
    customer_name: Optional[str] = None
    ic_number: Optional[str] = None
    bank: Optional[str] = None
    period: Optional[str] = None
    card_last4: Optional[str] = None
    account_number: Optional[str] = None


class PendingFileCreate(BaseModel):
    """创建待确认文件"""
    original_filename: str
    file_path: str
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    extracted_info: Optional[PendingFileExtractedInfo] = None


class PendingFileConfirm(BaseModel):
    """确认文件请求"""
    confirmed_by: str = Field(..., description="确认人")
    matched_customer_id: Optional[int] = Field(None, description="匹配的客户ID")
    matched_company_id: Optional[int] = Field(None, description="匹配的公司ID")
    notes: Optional[str] = Field(None, description="备注")


class PendingFileReject(BaseModel):
    """拒绝文件请求"""
    rejected_reason: str = Field(..., description="拒绝原因")
    rejected_by: str = Field(..., description="拒绝人")


class PendingFileResponse(BaseModel):
    """待确认文件响应"""
    id: int
    original_filename: str
    uploaded_at: datetime
    file_path: str
    file_size: Optional[int]
    
    # OCR提取信息
    extracted_customer_name: Optional[str]
    extracted_ic_number: Optional[str]
    extracted_bank: Optional[str]
    extracted_period: Optional[str]
    extracted_card_last4: Optional[str]
    extracted_account_number: Optional[str]
    
    # 匹配结果
    matched_customer_id: Optional[int]
    matched_company_id: Optional[int]
    match_confidence: Optional[float]
    match_reason: Optional[str]
    
    # 状态
    verification_status: str
    confirmed_by: Optional[str]
    confirmed_at: Optional[datetime]
    rejected_reason: Optional[str]
    notes: Optional[str]
    
    # 处理状态
    is_processed: bool
    processed_at: Optional[datetime]
    processing_error: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PendingFileListResponse(BaseModel):
    """待确认文件列表响应"""
    total: int
    pending_count: int
    matched_count: int
    mismatch_count: int
    confirmed_count: int
    rejected_count: int
    items: list[PendingFileResponse]


class CustomerMatchInfo(BaseModel):
    """客户匹配信息"""
    customer_id: int
    customer_name: str
    ic_number: Optional[str]
    email: Optional[str]
    match_score: float
    match_reasons: list[str]
    
    class Config:
        from_attributes = True
