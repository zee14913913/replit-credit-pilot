"""
Parser Registry API Endpoints

Provides information about supported banks and their parsers.
Integrates with circuit breaker for per-bank availability status.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Literal, Optional
from pydantic import BaseModel
from datetime import datetime

# Phase 1-10: Import from parsers module
try:
    from accounting_app.parsers import get_supported_banks, get_circuit_breaker
except ImportError:
    # Fallback if module not found (shouldn't happen)
    def get_supported_banks():
        return []
    def get_circuit_breaker():
        return None

router = APIRouter(prefix="/api/parsers", tags=["Parser Registry"])


class SupportedBankResponse(BaseModel):
    """支持的银行信息（含熔断状态）"""
    bank_code: str
    bank_name_en: str
    bank_name_zh: str
    supported_formats: List[str]
    parser_version: str
    enabled: bool
    circuit_open: bool = False
    circuit_reason: Optional[str] = None
    notes: str = ""


# DEPRECATED: Legacy hardcoded list (保留作为fallback)
_LEGACY_SUPPORTED_BANKS = [
    {
        "bank_code": "maybank",
        "bank_name_en": "Maybank (Malayan Banking Berhad)",
        "bank_name_zh": "马来亚银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Supports both PDF text extraction and CSV import"
    },
    {
        "bank_code": "cimb",
        "bank_name_en": "CIMB Bank",
        "bank_name_zh": "联昌国际银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Supports standard statement format"
    },
    {
        "bank_code": "public_bank",
        "bank_name_en": "Public Bank",
        "bank_name_zh": "大众银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Multi-page PDF support"
    },
    {
        "bank_code": "rhb",
        "bank_name_en": "RHB Bank",
        "bank_name_zh": "兴业银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Standard format support"
    },
    {
        "bank_code": "hong_leong",
        "bank_name_en": "Hong Leong Bank",
        "bank_name_zh": "丰隆银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Bilingual statement support (EN/BM)"
    },
    {
        "bank_code": "ambank",
        "bank_name_en": "AmBank (AmBank Group)",
        "bank_name_zh": "安联银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Standard format"
    },
    {
        "bank_code": "ocbc",
        "bank_name_en": "OCBC Bank",
        "bank_name_zh": "华侨银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Singapore-based, operates in Malaysia"
    },
    {
        "bank_code": "hsbc",
        "bank_name_en": "HSBC Bank Malaysia",
        "bank_name_zh": "汇丰银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "International format support"
    },
    {
        "bank_code": "standard_chartered",
        "bank_name_en": "Standard Chartered Bank Malaysia",
        "bank_name_zh": "渣打银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "International format"
    },
    {
        "bank_code": "uob",
        "bank_name_en": "United Overseas Bank (UOB)",
        "bank_name_zh": "大华银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Singapore-based"
    },
    {
        "bank_code": "affin",
        "bank_name_en": "Affin Bank",
        "bank_name_zh": "艾芬银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Local Malaysian bank"
    },
    {
        "bank_code": "alliance",
        "bank_name_en": "Alliance Bank Malaysia",
        "bank_name_zh": "联盟银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Standard format"
    },
    {
        "bank_code": "bank_islam",
        "bank_name_en": "Bank Islam Malaysia",
        "bank_name_zh": "马来西亚伊斯兰银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Islamic banking format"
    },
    {
        "bank_code": "muamalat",
        "bank_name_en": "Bank Muamalat Malaysia",
        "bank_name_zh": "马来西亚穆阿玛拉银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Islamic banking"
    },
    {
        "bank_code": "bsn",
        "bank_name_en": "Bank Simpanan Nasional (BSN)",
        "bank_name_zh": "国民储蓄银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "notes": "Government-backed bank"
    }
]


@router.get("/supported", response_model=List[SupportedBankResponse])
async def get_supported_banks_endpoint():
    """
    ## 📋 获取支持的银行列表（Phase 1-10 Enhanced）
    
    返回所有支持的马来西亚银行及其解析器信息，包含熔断状态。
    
    ### 响应字段：
    - **bank_code**: 银行代码（用于API请求）
    - **bank_name_en**: 英文名称
    - **bank_name_zh**: 中文名称
    - **supported_formats**: 支持的文件格式（pdf/csv/xlsx）
    - **parser_version**: 解析器版本
    - **enabled**: 是否在环境变量中启用
    - **circuit_open**: 熔断器是否打开（True=不可用）
    - **circuit_reason**: 熔断原因（如有）
    - **notes**: 备注信息
    
    ### 使用场景：
    1. 前端展示银行选择下拉菜单
    2. 验证bank_code参数的有效性
    3. 显示支持的文件格式提示
    4. 显示银行熔断状态（临时不可用警告）
    
    ### 示例：
    ```bash
    curl -X GET "http://localhost:8000/api/parsers/supported"
    ```
    
    ### 返回示例：
    ```json
    [
      {
        "bank_code": "maybank",
        "bank_name_en": "Maybank (Malayan Banking Berhad)",
        "bank_name_zh": "马来亚银行",
        "supported_formats": ["pdf", "csv"],
        "parser_version": "v1.0",
        "enabled": true,
        "circuit_open": false,
        "circuit_reason": null,
        "notes": ""
      },
      ...
    ]
    ```
    """
    # Phase 1-10: Get banks from registry
    banks = get_supported_banks()
    
    # Phase 1-10: Enhance with circuit breaker status
    cb = get_circuit_breaker()
    result = []
    
    for bank in banks:
        circuit_open = False
        circuit_reason = None
        
        if cb:
            is_available, reason = cb.is_bank_available(bank["bank_code"])
            circuit_open = not is_available
            circuit_reason = reason if not is_available else None
        
        result.append(SupportedBankResponse(
            bank_code=bank["bank_code"],
            bank_name_en=bank["bank_name_en"],
            bank_name_zh=bank["bank_name_zh"],
            supported_formats=bank["supported_formats"],
            parser_version=bank["parser_version"],
            enabled=bank["enabled"],
            circuit_open=circuit_open,
            circuit_reason=circuit_reason,
            notes=bank.get("notes", "")
        ))
    
    return result


@router.get("/bank/{bank_code}")
async def get_bank_info(bank_code: str):
    """
    ## 📋 获取特定银行信息
    
    根据bank_code获取银行详细信息。
    
    ### 参数：
    - **bank_code**: 银行代码（如：maybank, cimb, hong_leong）
    
    ### 返回：
    银行信息对象或404错误
    """
    banks = get_supported_banks()
    bank = next((b for b in banks if b["bank_code"] == bank_code), None)
    if not bank:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"Bank code '{bank_code}' not found. Use /api/parsers/supported to see all supported banks."
        )
    return bank
