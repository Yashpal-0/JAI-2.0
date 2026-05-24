import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "chat_history.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                tenant_id   TEXT NOT NULL,
                title       TEXT NOT NULL DEFAULT 'New Chat',
                created_at  INTEGER NOT NULL,
                updated_at  INTEGER NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_threads_user ON threads(user_id, tenant_id, updated_at DESC)"
        )
        conn.commit()


def upsert_thread(thread_id: str, user_id: str, tenant_id: str, title: str) -> None:
    ts = int(time.time() * 1000)
    with _conn() as conn:
        conn.execute("""
            INSERT INTO threads (id, user_id, tenant_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at
        """, (thread_id, user_id, tenant_id, title, ts, ts))
        conn.commit()


def list_threads(user_id: str, tenant_id: str) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT id, title, created_at, updated_at
            FROM threads
            WHERE user_id = ? AND tenant_id = ?
            ORDER BY updated_at DESC
        """, (user_id, tenant_id)).fetchall()
    return [dict(r) for r in rows]


def delete_thread(thread_id: str) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        conn.commit()


def get_thread_owner(thread_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT user_id, tenant_id FROM threads WHERE id = ?", (thread_id,)
        ).fetchone()
    return dict(row) if row else None
