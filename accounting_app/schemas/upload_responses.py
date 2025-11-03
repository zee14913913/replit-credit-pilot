"""
Unified Upload Response Schema (Phase 1-10)

7-State Machine (drives all buttons & routing):
- uploaded: File uploaded, not yet verified
- active: File verified; ready for reporting
- failed: Structural/row issues exist (see exceptions)
- duplicate: Primary statement for this company+account+month already exists
- validated: Verification passed; report not generated yet
- posted: Period is closed (view only)
- archived: Historical file (view only)
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# 7-State Machine
FileStatus = Literal[
    "uploaded",    # File uploaded, not yet verified
    "active",      # File verified; ready for reporting
    "failed",      # Original archived, but structural/row issues exist
    "duplicate",   # Primary statement already exists for this period
    "validated",   # Verification passed; report not generated yet
    "posted",      # Period is closed (view only)
    "archived"     # Historical file (view only)
]


# Status → Next Actions Mapping Table
STATUS_NEXT_ACTIONS = {
    "uploaded": ["validate", "view_original"],
    "active": ["generate_report", "download_original"],
    "failed": ["view_exceptions", "reprocess", "download_original"],
    "duplicate": ["set_as_primary", "view_other_files", "download_original"],
    "validated": ["generate_report", "download_original"],
    "posted": ["view_report", "download_original"],
    "archived": ["download_original"]
}


# Status → Human Note (for UI display)
STATUS_NOTES = {
    "uploaded": {
        "en": "File uploaded, not yet verified. Click Verify to continue.",
        "zh": "文件已上传，尚未验证。点击「验证」继续。"
    },
    "active": {
        "en": "File verified; ready for reporting / bank package.",
        "zh": "文件已验证；可生成报表/银行包。"
    },
    "failed": {
        "en": "Original archived, but structural/row issues exist (see exceptions).",
        "zh": "原件已封存，但存在结构/行数问题（查看异常中心）。"
    },
    "duplicate": {
        "en": "Primary statement for this company+account+month already exists.",
        "zh": "当前公司/账号/月份已有主对账单。"
    },
    "validated": {
        "en": "Verification passed; report not generated yet.",
        "zh": "验证通过；报表尚未生成。"
    },
    "posted": {
        "en": "Period is closed. View only; cannot overwrite.",
        "zh": "账期已结账。仅查看，不可覆盖。"
    },
    "archived": {
        "en": "Historical file (view only).",
        "zh": "历史文件（仅查看）。"
    }
}


class UploadResponse(BaseModel):
    """
    Unified Upload Response (success & failure)
    
    Key requirement: on 400/422 failures we still return raw_document_id
    and a human status_reason.
    
    Example (success):
    {
        "success": true,
        "status": "active",
        "raw_document_id": 48,
        "file_id": 48,
        "company_id": 1,
        "statement_month": "2025-05",
        "account_number": "23600594645",
        "next_actions": ["generate_report", "download_original"],
        "message": "✅ 成功导入 57 笔银行流水，自动匹配 34 笔"
    }
    
    Example (failure):
    {
        "success": false,
        "status": "failed",
        "raw_document_id": 50,
        "status_reason": "CSV字段不完整，缺少必需字段: Credit, Debit, Reference",
        "next_actions": ["view_exceptions", "reprocess", "download_original"],
        "warnings": ["请确保CSV包含6个必需列"]
    }
    
    Example (duplicate):
    {
        "success": true,
        "status": "duplicate",
        "raw_document_id": 49,
        "file_id": 49,
        "existing_file_id": 38,
        "next_actions": ["set_as_primary", "view_other_files", "download_original"],
        "duplicate_warning": "当前公司/账号/月份已有主对账单（文件ID: 38）"
    }
    """
    
    success: bool = Field(
        description="Overall operation success"
    )
    status: FileStatus = Field(
        description="File status from 7-state machine"
    )
    raw_document_id: Optional[int] = Field(
        default=None,
        description="原件ID（封存vault中的唯一标识）"
    )
    file_id: Optional[int] = Field(
        default=None,
        description="FileIndex ID（用于详情页URL）"
    )
    company_id: Optional[int] = Field(
        default=None,
        description="公司ID"
    )
    statement_month: Optional[str] = Field(
        default=None,
        description="对账单月份（YYYY-MM格式）"
    )
    account_number: Optional[str] = Field(
        default=None,
        description="银行账号"
    )
    status_reason: Optional[str] = Field(
        default=None,
        description="Human-readable status reason (especially for failures)"
    )
    next_actions: List[str] = Field(
        default_factory=list,
        description="下一步操作（基于7状态机映射）"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="警告信息列表"
    )
    existing_file_id: Optional[int] = Field(
        default=None,
        description="重复文件场景：现有主文件ID"
    )
    duplicate_warning: Optional[str] = Field(
        default=None,
        description="重复文件警告信息"
    )
    message: Optional[str] = Field(
        default=None,
        description="操作结果消息"
    )
    
    # Optional statistics
    imported: Optional[int] = Field(
        default=None,
        description="成功导入的交易笔数"
    )
    matched: Optional[int] = Field(
        default=None,
        description="自动匹配的交易笔数"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="文件存储路径"
    )
    
    # API versioning
    api_version: str = Field(
        default="v2_phase1-10",
        description="API版本号"
    )
    protection_enabled: bool = Field(
        default=True,
        description="原件保护是否启用"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "status": "active",
                    "raw_document_id": 48,
                    "file_id": 48,
                    "company_id": 1,
                    "statement_month": "2025-05",
                    "account_number": "23600594645",
                    "next_actions": ["generate_report", "download_original"],
                    "message": "✅ 成功导入 57 笔银行流水，自动匹配 34 笔",
                    "imported": 57,
                    "matched": 34,
                    "api_version": "v2_phase1-10",
                    "protection_enabled": True
                },
                {
                    "success": False,
                    "status": "failed",
                    "raw_document_id": 50,
                    "status_reason": "CSV字段不完整，缺少必需字段: Credit, Debit, Reference",
                    "next_actions": ["view_exceptions", "reprocess", "download_original"],
                    "warnings": ["请确保CSV包含6个必需列"],
                    "api_version": "v2_phase1-10",
                    "protection_enabled": True
                },
                {
                    "success": True,
                    "status": "duplicate",
                    "raw_document_id": 49,
                    "file_id": 49,
                    "existing_file_id": 38,
                    "next_actions": ["set_as_primary", "view_other_files", "download_original"],
                    "duplicate_warning": "当前公司/账号/月份已有主对账单（文件ID: 38）",
                    "api_version": "v2_phase1-10",
                    "protection_enabled": True
                }
            ]
        }


def get_next_actions(status: FileStatus) -> List[str]:
    """根据状态获取下一步操作"""
    return STATUS_NEXT_ACTIONS.get(status, [])


def get_status_note(status: FileStatus, lang: str = "zh") -> str:
    """根据状态和语言获取提示文本"""
    notes = STATUS_NOTES.get(status, {})
    return notes.get(lang, notes.get("en", ""))
