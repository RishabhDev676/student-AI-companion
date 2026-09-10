"""Small input and output guards for the Streamlit app."""

from __future__ import annotations

import html
import re
import time

MAX_TEXT = 4000
MAX_CHAT = 2000
MIN_AI_INTERVAL_SEC = 1.25
CONTEXT_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def escape_html(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def clamp_text(value: str | None, limit: int = MAX_TEXT) -> str:
    return (value or "").strip()[:limit]


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return (cleaned or "ruia")[:80]


def valid_context_key(key: str) -> bool:
    return bool(CONTEXT_KEY_RE.match(key or ""))


def allow_ai_call(last_ts: float, now: float | None = None) -> tuple[bool, float]:
    now = time.monotonic() if now is None else now
    if last_ts and (now - last_ts) < MIN_AI_INTERVAL_SEC:
        return False, last_ts
    return True, now
