"""SQLite 连接与建表。"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "sunny.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
              name TEXT PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS items (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              category TEXT NOT NULL,
              price REAL NOT NULL,
              unit TEXT NOT NULL DEFAULT '元',
              description TEXT NOT NULL DEFAULT '',
              contact TEXT NOT NULL,
              image TEXT NOT NULL DEFAULT '',
              time TEXT NOT NULL DEFAULT '刚刚',
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS admin (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              password_hash TEXT NOT NULL
            );
            """
        )
