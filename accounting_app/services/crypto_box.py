import os
from cryptography.fernet import Fernet, InvalidToken

_FKEY = os.getenv("FERNET_KEY")
if not _FKEY:
    _FKEY = Fernet.generate_key().decode()
fernet = Fernet(_FKEY.encode() if isinstance(_FKEY, str) else _FKEY)

def enc(s: str) -> str:
    if s is None:
        return ""
    return fernet.encrypt(s.encode()).decode()

def dec(s: str) -> str:
    if not s:
        return ""
    try:
        return fernet.decrypt(s.encode()).decode()
    except InvalidToken:
        return ""
