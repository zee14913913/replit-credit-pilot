"""
Phase 1-1: 原件保护相关Pydantic schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class RawDocumentCreate(BaseModel):
    """创建原件记录请求"""
    company_id: int = Field(..., description="公司ID")
    file_name: str = Field(..., description="文件名")
    storage_path: str = Field(..., description="存储路径")
    file_hash: str = Field(..., description="分块SHA256哈希值")
    file_size: int = Field(..., description="文件大小（字节）", gt=0)
    source_engine: str = Field(..., description="来源引擎: flask | fastapi")
    module: str = Field(..., description="模块: credit-card | bank | savings | pos | supplier | reports")
    uploaded_by: Optional[int] = Field(None, description="上传人ID")
    
    @validator('source_engine')
    def validate_source_engine(cls, v):
        if v not in ['flask', 'fastapi']:
            raise ValueError('source_engine必须是flask或fastapi')
        return v
    
    @validator('module')
    def validate_module(cls, v):
        allowed = ['credit-card', 'bank', 'savings', 'pos', 'supplier', 'reports', 'management', 'temp']
        if v not in allowed:
            raise ValueError(f'module必须是{allowed}之一')
        return v


class RawDocumentResponse(BaseModel):
    """原件记录响应"""
    id: int
    company_id: int
    file_name: str
    file_hash: str
    file_size: int
    storage_path: str
    uploaded_at: datetime
    uploaded_by: Optional[int]
    source_engine: str
    module: str
    status: str
    total_lines: Optional[int]
    parsed_lines: Optional[int]
    reconciliation_status: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class RawLineCreate(BaseModel):
    """创建原始行记录"""
    line_no: int = Field(..., description="行号（1-based）", gt=0)
    page_no: Optional[int] = Field(None, description="页码（PDF专用）")
    raw_text: str = Field(..., description="原始文本内容")


class RawLineBatchCreate(BaseModel):
    """批量创建原始行"""
    raw_document_id: int = Field(..., description="原件ID")
    lines: List[RawLineCreate] = Field(..., description="行数据列表")
    parser_version: str = Field(default="1.0", description="解析器版本号")


class RawLineResponse(BaseModel):
    """原始行响应"""
    id: int
    raw_document_id: int
    line_no: int
    page_no: Optional[int]
    raw_text: str
    parser_version: Optional[str]
    is_parsed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReconciliationRequest(BaseModel):
    """行数对账请求"""
    raw_document_id: int = Field(..., description="原件ID")
    total_lines: int = Field(..., description="文件总行数", gt=0)
    parsed_lines: int = Field(..., description="成功解析行数", ge=0)


class ReconciliationResponse(BaseModel):
    """行数对账响应"""
    status: str = Field(..., description="对账状态: match | mismatch")
    can_post: bool = Field(..., description="是否可以入账")
    reason: str = Field(..., description="对账结果说明")
    total_lines: int = Field(..., description="文件总行数")
    parsed_lines: int = Field(..., description="成功解析行数")
    actual_raw_lines: int = Field(..., description="raw_lines表实际行数")


class MigrationLogCreate(BaseModel):
    """迁移日志创建"""
    company_id: Optional[int] = Field(None, description="公司ID")
    src_path: str = Field(..., description="原路径")
    dest_path: Optional[str] = Field(None, description="目标路径")
    module: Optional[str] = Field(None, description="模块")
    batch_id: Optional[str] = Field(None, description="批次ID")
    run_by: Optional[str] = Field(None, description="执行人")
    status: str = Field(..., description="状态: success | failed | skipped")
    error_message: Optional[str] = Field(None, description="错误信息")
    file_hash: Optional[str] = Field(None, description="文件hash")
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['success', 'failed', 'skipped']:
            raise ValueError('status必须是success, failed或skipped')
        return v


class MigrationLogResponse(BaseModel):
    """迁移日志响应"""
    id: int
    company_id: Optional[int]
    src_path: str
    dest_path: Optional[str]
    module: Optional[str]
    batch_id: Optional[str]
    run_at: datetime
    run_by: Optional[str]
    status: str
    error_message: Optional[str]
    file_hash: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
