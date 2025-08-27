# db.py
import os
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any

DB_PATH = os.getenv("LUMINAIQ_DB_PATH", "luminaiq.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Create required tables if they don't exist."""
    with get_conn() as conn:
        cur = conn.cursor()

        # Basic uploads table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                rows INTEGER DEFAULT 0,
                cols INTEGER DEFAULT 0
            )
            """
        )

        # Saved views for pages (dashboard, etc.)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                page TEXT NOT NULL,
                name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(user_id, page, name)
            )
            """
        )

        conn.commit()


# ---------- Uploads ----------

def insert_upload(
    user_id: str,
    filename: str,
    path: str,
    uploaded_at: str,
    rows: int,
    cols: int,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO uploads (user_id, filename, path, uploaded_at, rows, cols)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, filename, path, uploaded_at, rows, cols),
        )
        conn.commit()


def list_uploads_for_user(user_id: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, filename, path, uploaded_at, rows, cols
            FROM uploads
            WHERE user_id = ?
            ORDER BY uploaded_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------- Saved Views ----------

def save_view(user_id: str, page: str, name: str, payload_json: str) -> None:
    """
    Upsert a saved view by (user_id, page, name).
    """
    if not name:
        raise ValueError("View name cannot be empty.")

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO saved_views (user_id, page, name, payload_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, page, name) DO UPDATE SET
              payload_json = excluded.payload_json
            """,
            (user_id, page, name, payload_json),
        )
        conn.commit()


def list_views(user_id: str, page: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT name, payload_json as payload
            FROM saved_views
            WHERE user_id = ? AND page = ?
            ORDER BY name COLLATE NOCASE
            """,
            (user_id, page),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_view(user_id: str, page: str, name: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            DELETE FROM saved_views
            WHERE user_id = ? AND page = ? AND name = ?
            """,
            (user_id, page, name),
        )
        conn.commit()
