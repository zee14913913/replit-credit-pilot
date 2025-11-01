"""
Phase 1-3: 文件索引Pydantic schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, date


class FileIndexCreate(BaseModel):
    """创建文件索引请求（Flask→FastAPI必传字段）"""
    company_id: int = Field(..., description="公司ID（必须）")
    file_category: str = Field(..., description="文件分类: bank_statement, invoice, receipt, report")
    file_type: str = Field(..., description="文件类型: original | generated")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    module: str = Field(..., description="模块: credit-card | bank | savings | pos | supplier | reports")
    raw_document_id: Optional[int] = Field(None, description="raw_documents记录ID（原始文件强制）")
    
    # 可选字段
    related_entity_type: Optional[str] = Field(None, description="关联实体类型: bank_statement_id, invoice_id等")
    related_entity_id: Optional[int] = Field(None, description="关联实体ID")
    file_size_kb: Optional[int] = Field(None, description="文件大小（KB）")
    file_extension: Optional[str] = Field(None, description="文件扩展名")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    period: Optional[str] = Field(None, description="期间 YYYY-MM")
    transaction_date: Optional[date] = Field(None, description="交易日期")
    upload_by: Optional[str] = Field(None, description="上传人")
    description: Optional[str] = Field(None, description="描述")
    tags: Optional[str] = Field(None, description="标签")
    
    @validator('file_type')
    def validate_file_type(cls, v):
        if v not in ['original', 'generated']:
            raise ValueError('file_type必须是original或generated')
        return v
    
    @validator('module')
    def validate_module(cls, v):
        allowed = ['credit-card', 'bank', 'savings', 'pos', 'supplier', 'reports', 'management', 'temp']
        if v not in allowed:
            raise ValueError(f'module必须是{allowed}之一')
        return v


class FileIndexResponse(BaseModel):
    """文件索引响应"""
    id: int
    company_id: int
    file_category: str
    file_type: str
    filename: str
    file_path: str
    module: Optional[str]
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    file_size_kb: Optional[int]
    file_extension: Optional[str]
    mime_type: Optional[str]
    period: Optional[str]
    transaction_date: Optional[date]
    upload_by: Optional[str]
    upload_date: Optional[datetime]
    description: Optional[str]
    tags: Optional[str]
    is_active: Optional[bool]
    status: str
    deleted_at: Optional[datetime]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class FileIndexUpdate(BaseModel):
    """更新文件索引"""
    description: Optional[str] = None
    tags: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None


class FileIndexList(BaseModel):
    """文件索引列表响应"""
    total: int
    items: list[FileIndexResponse]


class RecycleBinResponse(BaseModel):
    """回收站响应"""
    total: int
    items: list[FileIndexResponse]
    

class FlaskToFastAPIFileSync(BaseModel):
    """
    Flask → FastAPI 文件索引同步请求
    关键：Flask上传完成后必须把company_id/customer_id识别结果一并传给FastAPI
    Phase 1-3修复：强制要求raw_document_id，防止绕过1:1封存
    """
    company_id: int = Field(..., description="公司ID（Flask识别结果）")
    raw_document_id: int = Field(..., description="raw_documents记录ID（必须，防绕过）")
    customer_id: Optional[int] = Field(None, description="客户ID（Flask识别结果，如果适用）")
    file_path: str = Field(..., description="文件路径")
    filename: str = Field(..., description="文件名")
    module: str = Field(..., description="模块: credit-card | bank | savings | receipts")
    file_category: str = Field(..., description="文件分类")
    file_type: str = Field(default='original', description="文件类型: original | generated")
    file_size_kb: Optional[int] = Field(None, description="文件大小（KB）")
    period: Optional[str] = Field(None, description="期间 YYYY-MM")
    upload_by: Optional[str] = Field(None, description="上传人")
    
    @validator('module')
    def validate_module(cls, v):
        allowed = ['credit-card', 'bank', 'savings', 'receipts', 'pos', 'supplier', 'reports']
        if v not in allowed:
            raise ValueError(f'module必须是{allowed}之一')
        return v
