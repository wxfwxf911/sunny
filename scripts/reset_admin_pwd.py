r"""重置管理员密码（写 bcrypt hash 到 admin 表）。

用法：
    python scripts/reset_admin_pwd.py <新密码>
或交互式：
    python scripts/reset_admin_pwd.py
"""
import getpass
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.auth import hash_pwd  # noqa: E402
from backend.db import get_conn, init_db  # noqa: E402


def main() -> None:
    init_db()
    if len(sys.argv) > 1:
        new_pwd = sys.argv[1]
    else:
        new_pwd = getpass.getpass("新密码：")
        again = getpass.getpass("再输一次：")
        if new_pwd != again:
            print("两次输入不一致", file=sys.stderr)
            sys.exit(1)
    if len(new_pwd) < 4:
        print("密码至少 4 位", file=sys.stderr)
        sys.exit(1)

    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO admin (id, password_hash) VALUES (1, ?)", (hash_pwd(new_pwd),))
    print("✅ 管理员密码已重置为 bcrypt")


if __name__ == "__main__":
    main()
