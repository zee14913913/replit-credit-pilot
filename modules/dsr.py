"""
DSR (Debt Service Ratio) 计算模块
用于贷款产品匹配系统
"""

def calculate_dsr(total_commitment, monthly_income):
    """
    计算债务偿还比率
    
    Args:
        total_commitment: 月度总负债
        monthly_income: 月收入
        
    Returns:
        DSR百分比，如果收入<=0则返回None
    """
    if monthly_income <= 0:
        return None
    return round((total_commitment / monthly_income) * 100, 2)
