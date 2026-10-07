# -*- coding: utf-8 -*-
"""
数据层：基于 Python 标准库 sqlite3。
存储用户、会话、页面内容与编辑历史。
"""
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone

import config
from content_seed import INITIAL_PAGES, PAGE_ORDER

_local = threading.local()


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def get_conn() -> sqlite3.Connection:
    """每线程一个连接。"""
    conn = getattr(_local, "conn", None)
    if conn is None:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        _local.conn = conn
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    salt          TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'user',
    created_at    TEXT    NOT NULL,
    last_login    TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    created_at TEXT    NOT NULL,
    expires_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pages (
    slug       TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    updated_by TEXT
);

CREATE TABLE IF NOT EXISTS page_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL,
    editor     TEXT,
    created_at TEXT NOT NULL
);

-- 待审核的页面变更（子管理员提交，超级管理员审核）
CREATE TABLE IF NOT EXISTS pending_changes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    action          TEXT NOT NULL,              -- create | update
    slug            TEXT NOT NULL,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    submitted_by    TEXT NOT NULL,
    submitted_by_id INTEGER,
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    created_at      TEXT NOT NULL,
    reviewed_by     TEXT,
    reviewed_at     TEXT,
    review_note     TEXT
);

-- 站内消息 / 通知
CREATE TABLE IF NOT EXISTS notifications (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    target_user_id INTEGER,                     -- 定向给某个用户
    target_role    TEXT,                        -- 或按角色广播（如 admin）
    title          TEXT NOT NULL,
    body           TEXT,
    link           TEXT,
    is_read        INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL
);
"""


def init_db() -> None:
    """初始化表结构，并写入种子数据（页面 + 管理员账号）。"""
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    _seed_pages(conn)
    _seed_admin(conn)


def _seed_pages(conn: sqlite3.Connection) -> None:
    for idx, slug in enumerate(PAGE_ORDER):
        row = conn.execute("SELECT 1 FROM pages WHERE slug=?", (slug,)).fetchone()
        if row:
            continue
        page = INITIAL_PAGES[slug]
        conn.execute(
            "INSERT INTO pages (slug, title, content, sort_order, updated_at, updated_by) "
            "VALUES (?,?,?,?,?,?)",
            (slug, page["title"], page["content"], idx, _now(), "system"),
        )
    conn.commit()


def _seed_admin(conn: sqlite3.Connection) -> None:
    import auth  # 延迟导入避免循环依赖

    row = conn.execute(
        "SELECT 1 FROM users WHERE username=?", (config.ADMIN_USERNAME,)
    ).fetchone()
    if row:
        # 确保内置管理员角色始终为 admin
        conn.execute(
            "UPDATE users SET role=? WHERE username=?",
            (config.ROLE_ADMIN, config.ADMIN_USERNAME),
        )
        conn.commit()
        return
    pwd_hash, salt = auth.hash_password(config.ADMIN_PASSWORD)
    conn.execute(
        "INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (?,?,?,?,?)",
        (config.ADMIN_USERNAME, pwd_hash, salt, config.ROLE_ADMIN, _now()),
    )
    conn.commit()


# ---------------- 用户相关 ----------------
def get_user_by_username(username: str):
    return get_conn().execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()


def get_user_by_id(user_id: int):
    return get_conn().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


def create_user(username: str, password_hash: str, salt: str, role: str = "user"):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (?,?,?,?,?)",
        (username, password_hash, salt, role, _now()),
    )
    conn.commit()
    return get_user_by_id(cur.lastrowid)


def list_users():
    return get_conn().execute(
        "SELECT id, username, role, created_at, last_login FROM users ORDER BY id ASC"
    ).fetchall()


def set_user_role(user_id: int, role: str) -> None:
    conn = get_conn()
    conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    conn.commit()


def touch_last_login(user_id: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE users SET last_login=? WHERE id=?", (_now(), user_id))
    conn.commit()


def delete_user(user_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()


# ---------------- 会话相关 ----------------
def create_session(token: str, user_id: int, ttl: int) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?,?,?,?)",
        (token, user_id, _now(), int(time.time()) + ttl),
    )
    conn.commit()


def get_session(token: str):
    row = get_conn().execute(
        "SELECT * FROM sessions WHERE token=?", (token,)
    ).fetchone()
    if not row:
        return None
    if row["expires_at"] < int(time.time()):
        delete_session(token)
        return None
    return row


def delete_session(token: str) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM sessions WHERE token=?", (token,))
    conn.commit()


def purge_expired_sessions() -> None:
    conn = get_conn()
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (int(time.time()),))
    conn.commit()


# ---------------- 页面相关 ----------------
def list_pages():
    return get_conn().execute(
        "SELECT slug, title, updated_at, updated_by FROM pages ORDER BY sort_order ASC"
    ).fetchall()


def get_page(slug: str):
    return get_conn().execute("SELECT * FROM pages WHERE slug=?", (slug,)).fetchone()


def update_page(slug: str, title: str, content: str, editor: str) -> None:
    conn = get_conn()
    # 记录历史
    old = get_page(slug)
    if old:
        conn.execute(
            "INSERT INTO page_history (slug, title, content, editor, created_at) VALUES (?,?,?,?,?)",
            (slug, old["title"], old["content"], old["updated_by"], _now()),
        )
    conn.execute(
        "UPDATE pages SET title=?, content=?, updated_at=?, updated_by=? WHERE slug=?",
        (title, content, _now(), editor, slug),
    )
    conn.commit()


def create_page(slug: str, title: str, content: str, editor: str) -> None:
    conn = get_conn()
    max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM pages").fetchone()[0]
    conn.execute(
        "INSERT INTO pages (slug, title, content, sort_order, updated_at, updated_by) VALUES (?,?,?,?,?,?)",
        (slug, title, content, max_order + 1, _now(), editor),
    )
    conn.commit()


def delete_page(slug: str) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM pages WHERE slug=?", (slug,))
    conn.commit()


def get_page_history(slug: str, limit: int = 30):
    return get_conn().execute(
        "SELECT id, slug, title, editor, created_at FROM page_history "
        "WHERE slug=? ORDER BY id DESC LIMIT ?",
        (slug, limit),
    ).fetchall()


# ---------------- 待审核变更 ----------------
def create_pending_change(action, slug, title, content, submitted_by, submitted_by_id):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO pending_changes "
        "(action, slug, title, content, submitted_by, submitted_by_id, status, created_at) "
        "VALUES (?,?,?,?,?,?, 'pending', ?)",
        (action, slug, title, content, submitted_by, submitted_by_id, _now()),
    )
    conn.commit()
    return get_pending_change(cur.lastrowid)


def get_pending_change(change_id):
    return get_conn().execute(
        "SELECT * FROM pending_changes WHERE id=?", (change_id,)
    ).fetchone()


def list_pending_changes(status="pending"):
    if status == "all":
        return get_conn().execute(
            "SELECT * FROM pending_changes ORDER BY (status='pending') DESC, id DESC"
        ).fetchall()
    return get_conn().execute(
        "SELECT * FROM pending_changes WHERE status=? ORDER BY id DESC", (status,)
    ).fetchall()


def list_pending_by_user(username, limit=50):
    return get_conn().execute(
        "SELECT * FROM pending_changes WHERE submitted_by=? ORDER BY id DESC LIMIT ?",
        (username, limit),
    ).fetchall()


def count_pending_changes():
    return get_conn().execute(
        "SELECT COUNT(*) FROM pending_changes WHERE status='pending'"
    ).fetchone()[0]


def set_pending_status(change_id, status, reviewer, note=None):
    conn = get_conn()
    conn.execute(
        "UPDATE pending_changes SET status=?, reviewed_by=?, reviewed_at=?, review_note=? WHERE id=?",
        (status, reviewer, _now(), note, change_id),
    )
    conn.commit()
    return get_pending_change(change_id)


# ---------------- 通知 ----------------
def add_notification(title, body=None, link=None, target_user_id=None, target_role=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO notifications (target_user_id, target_role, title, body, link, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (target_user_id, target_role, title, body, link, _now()),
    )
    conn.commit()


def list_notifications(user, limit=50):
    """返回某个用户可见的通知（定向 + 角色广播）。"""
    uid = user["id"]
    role = user["role"]
    return get_conn().execute(
        "SELECT * FROM notifications "
        "WHERE target_user_id=? OR (target_user_id IS NULL AND target_role=?) "
        "ORDER BY id DESC LIMIT ?",
        (uid, role, limit),
    ).fetchall()


def count_unread_notifications(user):
    uid = user["id"]
    role = user["role"]
    return get_conn().execute(
        "SELECT COUNT(*) FROM notifications "
        "WHERE is_read=0 AND (target_user_id=? OR (target_user_id IS NULL AND target_role=?))",
        (uid, role),
    ).fetchone()[0]


def mark_notifications_read(user, ids=None):
    conn = get_conn()
    uid = user["id"]
    role = user["role"]
    if ids:
        placeholders = ",".join("?" for _ in ids)
        conn.execute(
            f"UPDATE notifications SET is_read=1 WHERE id IN ({placeholders}) "
            "AND (target_user_id=? OR (target_user_id IS NULL AND target_role=?))",
            (*ids, uid, role),
        )
    else:
        conn.execute(
            "UPDATE notifications SET is_read=1 "
            "WHERE target_user_id=? OR (target_user_id IS NULL AND target_role=?)",
            (uid, role),
        )
    conn.commit()
