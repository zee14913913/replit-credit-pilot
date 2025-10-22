"""
客户名称处理工具
"""

def get_customer_initials(full_name):
    """
    获取客户名字缩写
    例：CHANG CHOON CHOW -> CCC
    """
    if not full_name:
        return ""
    
    # 分割名字
    parts = full_name.strip().upper().split()
    
    # 取每个部分的首字母
    initials = ''.join([part[0] for part in parts if part])
    
    return initials


def get_customer_code(full_name):
    """
    获取客户代码（缩写_ALL）
    例：CHANG CHOON CHOW -> CCC_ALL
    """
    initials = get_customer_initials(full_name)
    return f"{initials}_ALL" if initials else "UNKNOWN_ALL"
