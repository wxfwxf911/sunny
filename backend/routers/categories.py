"""分类读写。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_admin
from ..db import get_conn

router = APIRouter()


class CatIn(BaseModel):
    name: str


@router.get("/categories")
def list_categories():
    with get_conn() as conn:
        rows = conn.execute("SELECT name FROM categories ORDER BY rowid").fetchall()
    return [r["name"] for r in rows]


@router.post("/categories")
def add_category(body: CatIn, _=Depends(require_admin)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="分类名不能为空")
    if name == "全部":
        raise HTTPException(status_code=400, detail="「全部」是内置分类")
    with get_conn() as conn:
        if conn.execute("SELECT 1 FROM categories WHERE name=?", (name,)).fetchone():
            raise HTTPException(status_code=400, detail="分类已存在")
        conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    return {"ok": True}


@router.delete("/categories/{name}")
def del_category(name: str, _=Depends(require_admin)):
    with get_conn() as conn:
        if conn.execute("SELECT 1 FROM items WHERE category=?", (name,)).fetchone():
            raise HTTPException(status_code=409, detail="该分类下仍有商品")
        if not conn.execute("SELECT 1 FROM categories WHERE name=?", (name,)).fetchone():
            raise HTTPException(status_code=404, detail="分类不存在")
        conn.execute("DELETE FROM categories WHERE name=?", (name,))
    return {"ok": True}
