r"""一次性迁移：data.json → SQLite + uploads/。幂等（重复跑结果一致）。

用法：python scripts/migrate_data.py

数据源：仓库根目录 data.json（6 条商品）+ images/（5 张 URL 图）。
- image 是 data:...;base64 → 解码存 uploads/mig_base64_<i>.jpg
- image 是 https://.../images/*.jpg → 从本地 images/ 复制到 uploads/（保留文件名）
- 商品 id 固定为 index+1（1~6），新商品从 7 自增
- admin 保留旧 SHA-256 哈希，首次登录成功后自动升级 bcrypt

⚠️ 只在部署时跑一次，不要在已有生产数据的环境重跑（会清空 items/categories）。
"""
import base64
import json
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.db import get_conn, init_db  # noqa: E402

DATA_JSON = BASE_DIR / "data.json"
IMAGES_DIR = BASE_DIR / "images"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MIME_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def decode_data_url(image: str):
    """'data:image/jpeg;base64,...' -> ('.jpg', bytes)"""
    header, b64 = image.split(",", 1)
    mime = header.split(";")[0].split(":")[1]
    ext = MIME_EXT.get(mime, ".jpg")
    return ext, base64.b64decode(b64)


def migrate() -> dict:
    d = json.load(open(DATA_JSON, encoding="utf-8"))
    init_db()

    cats = [c for c in d.get("categories", []) if c != "全部"]
    admin_pwd = d.get("_config", {}).get("admin_pwd", "")
    report = {"categories": len(cats), "items": 0, "admin": bool(admin_pwd), "images": []}

    with get_conn() as conn:
        conn.execute("DELETE FROM items")
        conn.execute("DELETE FROM categories")
        for c in cats:
            conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (c,))
        if admin_pwd:
            conn.execute("INSERT OR REPLACE INTO admin (id, password_hash) VALUES (1, ?)", (admin_pwd,))

        for i, it in enumerate(d.get("items", [])):
            image = it.get("image", "")
            if image.startswith("data:"):
                ext, raw = decode_data_url(image)
                fname = f"mig_base64_{i}{ext}"
                (UPLOAD_DIR / fname).write_bytes(raw)
                image_path = f"/sunny/uploads/{fname}"
            elif image:
                fname = image.rsplit("/", 1)[-1]
                src = IMAGES_DIR / fname
                if src.exists():
                    shutil.copyfile(src, UPLOAD_DIR / fname)
                image_path = f"/sunny/uploads/{fname}"
            else:
                image_path = ""

            conn.execute(
                "INSERT INTO items (id, title, category, price, unit, description, contact, image, time) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (i + 1, it["title"], it["category"], it["price"], it["unit"],
                 it.get("desc", ""), it.get("contact", ""), image_path, it.get("time", "刚刚")),
            )
            report["images"].append(image_path)
            report["items"] += 1

    return report


if __name__ == "__main__":
    r = migrate()
    print(f"✅ 迁移完成：分类 {r['categories']} 个，商品 {r['items']} 条，admin {'已写入' if r['admin'] else '未写入'}")
    for p in r["images"]:
        print("  ", p)
