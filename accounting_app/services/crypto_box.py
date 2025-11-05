# accounting_app/services/crypto_box.py
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

_key = os.getenv("FERNET_KEY", "").encode() if os.getenv("FERNET_KEY") else None
_fernet: Optional[Fernet] = Fernet(_key) if _key else None

def encrypt(s: str) -> str:
    if not s:
        return s
    if not _fernet:
        return s
    return _fernet.encrypt(s.encode()).decode()

def decrypt(s: str) -> str:
    if not s:
        return s
    if not _fernet:
        return s
    try:
        return _fernet.decrypt(s.encode()).decode()
    except (InvalidToken, Exception):
        return s
