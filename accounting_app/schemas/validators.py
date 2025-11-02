"""
Schema Validators - 通用校验器
用于Pydantic schema的字段验证
"""
from datetime import datetime
from pydantic import field_validator


def validate_yyyy_mm(v: str) -> str:
    """
    校验月份格式为 YYYY-MM
    
    Args:
        v: 月份字符串
    
    Returns:
        验证通过的月份字符串
    
    Raises:
        ValueError: 格式不符合 YYYY-MM
    
    Examples:
        >>> validate_yyyy_mm("2025-01")
        "2025-01"
        >>> validate_yyyy_mm("2025/01")
        ValueError: period / month must be in 'YYYY-MM' format, e.g. 2025-01
    """
    if not v:
        raise ValueError("period / month cannot be empty")
    
    try:
        # 必须是 YYYY-MM 格式
        dt = datetime.strptime(v, "%Y-%m")
        # 验证通过后，返回标准化的格式（确保月份是两位数）
        return dt.strftime("%Y-%m")
    except ValueError:
        raise ValueError(
            f"period / month must be in 'YYYY-MM' format, e.g. 2025-01. "
            f"Received: '{v}'"
        )


# 创建可复用的字段校验器装饰器
# 使用方法：在Pydantic model中使用 @field_validator
# 例如：
#
# class MyRequest(BaseModel):
#     period: str
#     
#     @field_validator('period')
#     @classmethod
#     def validate_period_format(cls, v):
#         return validate_yyyy_mm(v)
