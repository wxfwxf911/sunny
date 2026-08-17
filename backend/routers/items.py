"""商品 CRUD 与图片上传。"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from ..auth import require_admin
from ..db import get_conn

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_SIZE = 8 * 1024 * 1024


class ItemIn(BaseModel):
    title: str
    category: str
    price: float
    unit: str = "元"
    desc: str = ""
    contact: str
    image: str = ""


def _row_to_item(r) -> dict:
    return {
        "id": r["id"],
        "title": r["title"],
        "category": r["category"],
        "price": r["price"],
        "unit": r["unit"],
        "desc": r["description"],
        "contact": r["contact"],
        "image": r["image"],
        "time": r["time"],
    }


def _validate_image(image: str) -> None:
    if image == "" or image.startswith("/sunny/uploads/"):
        return
    raise HTTPException(status_code=400, detail="图片路径非法")


@router.get("/items")
def list_items():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    return [_row_to_item(r) for r in rows]


@router.get("/items/{item_id}")
def get_item(item_id: int):
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="商品不存在")
    return _row_to_item(r)


@router.post("/items")
def create_item(body: ItemIn, _=Depends(require_admin)):
    _validate_image(body.image)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO items (title, category, price, unit, description, contact, image, time) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, '刚刚')",
            (body.title, body.category, body.price, body.unit, body.desc, body.contact, body.image),
        )
        new_id = cur.lastrowid
    return {"ok": True, "id": new_id}


@router.put("/items/{item_id}")
def update_item(item_id: int, body: ItemIn, _=Depends(require_admin)):
    _validate_image(body.image)
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="商品不存在")
        conn.execute(
            "UPDATE items SET title=?, category=?, price=?, unit=?, description=?, contact=?, image=? "
            "WHERE id=?",
            (body.title, body.category, body.price, body.unit, body.desc, body.contact, body.image, item_id),
        )
    return {"ok": True}


@router.delete("/items/{item_id}")
def delete_item(item_id: int, _=Depends(require_admin)):
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="商品不存在")
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    return {"ok": True}


@router.post("/upload")
async def upload(file: UploadFile = File(...), _=Depends(require_admin)):
    ext = ALLOWED.get(file.content_type)
    if not ext:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/WebP/GIF")
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="图片不能超过 8MB")
    fname = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / fname).write_bytes(data)
    return {"url": f"/sunny/uploads/{fname}"}
