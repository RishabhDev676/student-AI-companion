"""Minimal SQLite helpers. No ORM — Streamlit-safe via check_same_thread=False."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_DB = Path(__file__).resolve().parent / "apexstudy.db"
_OLD_DB = Path(__file__).resolve().parent / "ruia_companion.db"
if not _DEFAULT_DB.exists() and _OLD_DB.exists():
    _DEFAULT_DB = _OLD_DB
DB_PATH = Path(os.getenv("APEXSTUDY_DB_PATH", os.getenv("RUIA_DB_PATH", _DEFAULT_DB)))

VALID_TASK_TYPES = ("plan_item", "exam", "quiz_result")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS student_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                subject TEXT,
                due_date TEXT,
                confidence_score REAL,
                status TEXT NOT NULL DEFAULT 'open',
                details TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_context(key: str) -> str | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT value FROM student_context WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None
    finally:
        conn.close()


def get_all_context() -> dict[str, str]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT key, value FROM student_context ORDER BY key"
        ).fetchall()
        return {row["key"]: row["value"] for row in rows}
    finally:
        conn.close()


def set_context(key: str, value: str) -> None:
    ts = _now()
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO student_context (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, ts),
        )
        conn.commit()
    finally:
        conn.close()


def add_task(
    task_type: str,
    title: str,
    subject: str | None = None,
    due_date: str | None = None,
    confidence_score: float | None = None,
    status: str = "open",
    details: str | None = None,
) -> int:
    if task_type not in VALID_TASK_TYPES:
        raise ValueError(f"Invalid task type: {task_type}")
    ts = _now()
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO tasks
                (type, title, subject, due_date, confidence_score, status, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (task_type, title, subject, due_date, confidence_score, status, details, ts),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def query_tasks(task_type: str | None = None, limit: int = 50) -> list[sqlite3.Row]:
    conn = get_conn()
    try:
        if task_type:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE type = ? ORDER BY id DESC LIMIT ?",
                (task_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return list(rows)
    finally:
        conn.close()


def update_task_status(task_id: int, status: str) -> None:
    conn = get_conn()
    try:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        conn.commit()
    finally:
        conn.close()


def _ensure_chat_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def add_chat(role: str, content: str) -> None:
    ts = _now()
    conn = get_conn()
    try:
        _ensure_chat_table(conn)
        conn.execute(
            "INSERT INTO chat_messages (role, content, created_at) VALUES (?, ?, ?)",
            (role, content, ts),
        )
        conn.commit()
    finally:
        conn.close()


def get_chat(limit: int = 40) -> list[sqlite3.Row]:
    for attempt in range(2):
        conn = get_conn()
        try:
            _ensure_chat_table(conn)
            rows = conn.execute(
                "SELECT * FROM chat_messages ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return list(reversed(rows))
        except sqlite3.OperationalError:
            if attempt == 0:
                init_db()
                continue
            return []
        finally:
            conn.close()
    return []


def clear_chat() -> None:
    conn = get_conn()
    try:
        _ensure_chat_table(conn)
        conn.execute("DELETE FROM chat_messages")
        conn.commit()
    finally:
        conn.close()
