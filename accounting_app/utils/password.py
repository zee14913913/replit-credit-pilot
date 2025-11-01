"""
Phase 2-1 修复：安全的密码hash工具
使用bcrypt替代不安全的SHA-256
"""
from passlib.context import CryptContext

# 密码加密上下文（使用bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    使用bcrypt对密码进行安全hash
    
    Args:
        password: 明文密码
    
    Returns:
        bcrypt hash字符串（自动加盐）
    
    Example:
        >>> hash_password("admin123")
        '$2b$12$...'
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配hash
    
    Args:
        plain_password: 明文密码
        hashed_password: bcrypt hash
    
    Returns:
        bool: 密码是否正确
    
    Example:
        >>> hash = hash_password("admin123")
        >>> verify_password("admin123", hash)
        True
        >>> verify_password("wrong", hash)
        False
    """
    # 兼容旧的SHA-256格式（迁移期间）
    if hashed_password.startswith("SHA256:"):
        import hashlib
        sha_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        return hashed_password == f"SHA256:{sha_hash}"
    
    # bcrypt验证
    return pwd_context.verify(plain_password, hashed_password)
