"""FastAPI 入口。"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routers import admin, categories, items

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
WWW_DIR = BASE_DIR / "www"

UPLOAD_DIR.mkdir(exist_ok=True)
WWW_DIR.mkdir(exist_ok=True)

init_db()

app = FastAPI(title="Sunny 二手集市")

app.include_router(items.router, prefix="/sunny/api", tags=["items"])
app.include_router(categories.router, prefix="/sunny/api", tags=["categories"])
app.include_router(admin.router, prefix="/sunny/api", tags=["admin"])

# 顺序重要：先挂 uploads，再挂 www（兜底）
app.mount("/sunny/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/sunny", StaticFiles(directory=str(WWW_DIR), html=True), name="www")
