"""密码哈希（SHA-256 兼容 + bcrypt 升级）与 token 鉴权。"""
import hashlib
import secrets
from datetime import datetime

import bcrypt
from fastapi import Header, HTTPException

# token -> 签发时间；内存存储，重启需重新登录（单 worker MVP 可接受）
SESSIONS = {}


def hash_pwd(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_pwd(plain: str, stored: str) -> bool:
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(plain.encode(), stored.encode())
        except ValueError:
            return False
    # 旧 SHA-256 hex
    if len(stored) == 64 and all(c in "0123456789abcdef" for c in stored):
        return hashlib.sha256(plain.encode()).hexdigest() == stored
    return False


def is_legacy(stored: str) -> bool:
    return not stored.startswith("$2")


def issue_token() -> str:
    token = secrets.token_hex(32)
    SESSIONS[token] = datetime.now()
    return token


def require_admin(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    if token not in SESSIONS:
        raise HTTPException(status_code=401, detail="登录已过期")
    return token
