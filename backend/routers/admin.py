"""管理员登录 / 验证 / 改密。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import hash_pwd, is_legacy, issue_token, require_admin, verify_pwd
from ..db import get_conn

router = APIRouter()


class LoginIn(BaseModel):
    password: str


class ChangePwdIn(BaseModel):
    old_password: str
    new_password: str


def _get_hash(conn) -> str:
    r = conn.execute("SELECT password_hash FROM admin WHERE id=1").fetchone()
    return r["password_hash"] if r else None


@router.post("/admin/login")
def login(body: LoginIn):
    with get_conn() as conn:
        stored = _get_hash(conn)
        if not stored:
            raise HTTPException(status_code=500, detail="管理员未初始化")
        if not verify_pwd(body.password, stored):
            raise HTTPException(status_code=401, detail="密码错误")
        # 旧 SHA-256 密码登录成功后自动升级为 bcrypt
        if is_legacy(stored):
            conn.execute("UPDATE admin SET password_hash=? WHERE id=1", (hash_pwd(body.password),))
    return {"token": issue_token()}


@router.get("/admin/verify")
def verify(_=Depends(require_admin)):
    return {"ok": True}


@router.post("/admin/change-password")
def change_password(body: ChangePwdIn, _=Depends(require_admin)):
    if len(body.new_password) < 4:
        raise HTTPException(status_code=400, detail="新密码至少 4 位")
    with get_conn() as conn:
        stored = _get_hash(conn)
        if not stored or not verify_pwd(body.old_password, stored):
            raise HTTPException(status_code=401, detail="原密码错误")
        conn.execute("UPDATE admin SET password_hash=? WHERE id=1", (hash_pwd(body.new_password),))
    return {"ok": True}
