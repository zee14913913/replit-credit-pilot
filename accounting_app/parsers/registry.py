"""
Bank Parser Registry

Manages 15 Malaysian bank parsers with metadata and auto-detection.
"""
import os
from typing import List, Dict, Optional

# 15 Major Malaysian Banks (标准代码)
BANK_CODES = [
    "maybank", "cimb", "public_bank", "rhb", "hong_leong", "ambank",
    "uob", "ocbc", "hsbc", "standard_chartered", "citibank",
    "affin", "alliance", "bank_islam", "mbsb"
]

# 银行别名映射（用于文件名/首行自动识别）
BANK_ALIASES = {
    "maybank": ["maybank", "malayan banking", "m2u", "mbb"],
    "cimb": ["cimb", "clicks", "cimb bank"],
    "public_bank": ["public bank", "pbe", "pbb"],
    "rhb": ["rhb", "rhb bank"],
    "hong_leong": ["hong leong", "hlb", "hl bank"],
    "ambank": ["ambank", "amonline", "am bank"],
    "uob": ["uob", "united overseas"],
    "ocbc": ["ocbc", "ocbc bank"],
    "hsbc": ["hsbc", "hsbc malaysia"],
    "standard_chartered": ["standard chartered", "sc bank", "scb"],
    "citibank": ["citi", "citibank", "citi malaysia"],
    "affin": ["affin", "affin bank"],
    "alliance": ["alliance", "alliance bank"],
    "bank_islam": ["bank islam", "bimb", "islamic"],
    "mbsb": ["mbsb", "mbsb bank", "malaysia building"]
}

# 银行元数据（支持格式、显示名称等）
BANK_METADATA = {
    "maybank": {
        "bank_name_en": "Maybank (Malayan Banking Berhad)",
        "bank_name_zh": "马来亚银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "cimb": {
        "bank_name_en": "CIMB Bank",
        "bank_name_zh": "联昌国际银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "public_bank": {
        "bank_name_en": "Public Bank",
        "bank_name_zh": "大众银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "rhb": {
        "bank_name_en": "RHB Bank",
        "bank_name_zh": "兴业银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "hong_leong": {
        "bank_name_en": "Hong Leong Bank",
        "bank_name_zh": "丰隆银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "ambank": {
        "bank_name_en": "AmBank (AmBank Group)",
        "bank_name_zh": "安联银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "uob": {
        "bank_name_en": "United Overseas Bank (UOB)",
        "bank_name_zh": "大华银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "ocbc": {
        "bank_name_en": "OCBC Bank",
        "bank_name_zh": "华侨银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "hsbc": {
        "bank_name_en": "HSBC Bank Malaysia",
        "bank_name_zh": "汇丰银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "standard_chartered": {
        "bank_name_en": "Standard Chartered Bank Malaysia",
        "bank_name_zh": "渣打银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "citibank": {
        "bank_name_en": "Citibank Malaysia",
        "bank_name_zh": "花旗银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "affin": {
        "bank_name_en": "Affin Bank",
        "bank_name_zh": "艾芬银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "alliance": {
        "bank_name_en": "Alliance Bank Malaysia",
        "bank_name_zh": "联盟银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "bank_islam": {
        "bank_name_en": "Bank Islam Malaysia",
        "bank_name_zh": "马来西亚伊斯兰银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    },
    "mbsb": {
        "bank_name_en": "MBSB Bank",
        "bank_name_zh": "马来西亚建设银行",
        "supports": {"pdf": True, "csv": True, "xlsx": False},
        "parser_version": "v1.0"
    }
}


def normalize_bank_name(bank_name: str) -> str:
    """
    规范化银行名称为标准bank_code
    
    Args:
        bank_name: 任意格式的银行名称（如"Hong Leong Bank", "hong leong", "HLB"）
    
    Returns:
        标准化的bank_code（如"hong_leong"），找不到返回原值的normalized版本
    
    Examples:
        >>> normalize_bank_name("Hong Leong Bank")
        'hong_leong'
        >>> normalize_bank_name("hong leong")
        'hong_leong'
        >>> normalize_bank_name("HLB")
        'hong_leong'
    """
    # Step 1: 清理和标准化输入
    search_text = bank_name.lower().strip()
    
    # Step 2: 精确匹配bank_code
    if search_text in BANK_CODES:
        return search_text
    
    # Step 3: 去除常见后缀（bank, berhad, sdn bhd, bhd, malaysia等）
    suffixes_to_remove = [" berhad", " sdn bhd", " bhd", " bank", " malaysia", " group"]
    cleaned = search_text
    for suffix in suffixes_to_remove:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)].strip()
    
    # Step 4: 再次精确匹配（去除后缀后）
    if cleaned in BANK_CODES:
        return cleaned
    
    # Step 5: 别名匹配（原始+清理版）
    for bank_code, aliases in BANK_ALIASES.items():
        lower_aliases = [a.lower() for a in aliases]
        if search_text in lower_aliases or cleaned in lower_aliases:
            return bank_code
        # Partial match in aliases
        for alias in lower_aliases:
            if alias in search_text or search_text in alias:
                return bank_code
    
    # Step 6: No match found - return cleaned version as fallback (for backward compatibility)
    # Production systems should validate and reject unknown banks upstream
    final = cleaned.replace(" ", "_")
    return final if final in BANK_CODES else cleaned.replace(" ", "_")


def detect_bank_code(filename: str = "", first_line: str = "", account_number: str = "") -> Optional[str]:
    """
    启发式银行代码检测
    
    Args:
        filename: 文件名
        first_line: CSV/PDF首行文本
        account_number: 账号（可选）
    
    Returns:
        检测到的bank_code，找不到返回None
    """
    search_text = f"{filename} {first_line}".lower()
    
    for bank_code, aliases in BANK_ALIASES.items():
        for alias in aliases:
            if alias.lower() in search_text:
                return bank_code
    
    return None


def is_bank_enabled(bank_code: str) -> bool:
    """
    检查银行是否在环境变量启用列表中
    
    Args:
        bank_code: 银行代码
    
    Returns:
        True表示启用，False表示禁用
    """
    enabled_str = os.getenv("PARSER_ENABLED_BANKS", "")
    if not enabled_str:
        return True
    
    enabled_banks = [b.strip() for b in enabled_str.split(",")]
    return bank_code in enabled_banks


def get_supported_banks() -> List[Dict]:
    """
    获取支持的银行列表（结合环境变量启用状态）
    
    Returns:
        银行信息列表，包含enabled字段
    """
    enabled_str = os.getenv("PARSER_ENABLED_BANKS", "")
    enabled_banks = [b.strip() for b in enabled_str.split(",")] if enabled_str else BANK_CODES
    
    result = []
    for bank_code in BANK_CODES:
        metadata = BANK_METADATA.get(bank_code, {})
        result.append({
            "bank_code": bank_code,
            "bank_name_en": metadata.get("bank_name_en", bank_code),
            "bank_name_zh": metadata.get("bank_name_zh", bank_code),
            "supported_formats": [k for k, v in metadata.get("supports", {}).items() if v],
            "parser_version": metadata.get("parser_version", "v1.0"),
            "enabled": bank_code in enabled_banks,
            "notes": ""
        })
    
    return result
