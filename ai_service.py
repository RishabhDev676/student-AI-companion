"""Single Gemini call site. Injects student_context on every request."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

import db
import security

load_dotenv(Path(__file__).resolve().parent / ".env.local")
load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


class AIError(Exception):
    """Raised when the LLM cannot be called or the response is unusable."""


def _api_keys() -> list[str]:
    keys = []
    for i in range(1, 6):
        val = os.getenv(f"API_KEY_{i}") or os.getenv(f"GEMINI_API_KEY_{i}")
        if val:
            keys.append(val.strip())
    single = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if single:
        keys.insert(0, single.strip())
    # de-dupe, keep order
    seen = set()
    out = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def keys_configured() -> bool:
    return bool(_api_keys())


def _context_block() -> str:
    ctx = db.get_all_context()
    if not ctx:
        return "No saved student context yet."
    lines = [f"- {k}: {v}" for k, v in ctx.items()]
    return "\n".join(lines)


def _extract_text(payload: dict) -> str:
    try:
        parts = payload["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIError("Gemini returned an unexpected response shape.") from exc
    texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
    text = "\n".join(t for t in texts if t).strip()
    if not text:
        raise AIError("Gemini returned an empty response.")
    return text


def parse_json(text: str):
    """Parse model output that may be wrapped in markdown fences."""
    raw = text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if fenced:
        raw = fenced.group(1).strip()
    else:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            raw = raw[start : end + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AIError("AI did not return valid JSON. Try generating again.") from exc


def call_ai(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 2048,
    expect_json: bool = False,
) -> str | dict:
    user_prompt = security.clamp_text(user_prompt, 8000)
    system_prompt = security.clamp_text(system_prompt, 8000)
    keys = _api_keys()
    if not keys:
        raise AIError(
            "No Gemini API key found. Put API_KEY_1 (and optional API_KEY_2…) in .env.local."
        )

    system = (
        system_prompt.strip()
        + "\n\n---\nStudent memory (shared across Study Planner, Exams, and Quizzes). "
        "Use this so plans and quizzes stay consistent with what we already know:\n"
        + _context_block()
        + "\n---"
    )
    if expect_json:
        system += "\nRespond with JSON only. No markdown, no commentary."

    last_error = "All Gemini API keys failed."
    for i, key in enumerate(keys, 1):
        try:
            response = requests.post(
                GEMINI_URL,
                headers={"Content-Type": "application/json", "x-goog-api-key": key},
                json={
                    "system_instruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        **({"responseMimeType": "application/json"} if expect_json else {}),
                    },
                },
                timeout=45,
            )
        except requests.Timeout:
            last_error = "Gemini request timed out."
            continue
        except requests.RequestException as exc:
            last_error = f"Network error talking to Gemini: {exc}"
            continue

        if response.status_code == 429:
            last_error = "Gemini rate limit hit; trying next key if available."
            continue
        if response.status_code in (401, 403):
            last_error = f"Gemini key {i} was rejected ({response.status_code})."
            continue
        if response.status_code != 200:
            last_error = f"Gemini HTTP {response.status_code}."
            continue

        try:
            text = _extract_text(response.json())
        except (ValueError, AIError) as exc:
            last_error = str(exc)
            continue

        if expect_json:
            return parse_json(text)
        return text

    raise AIError(last_error)


def remember_insights(updates: dict[str, str]) -> None:
    """Write insights back into shared student_context."""
    for key, value in updates.items():
        if value is None or not security.valid_context_key(key):
            continue
        db.set_context(key, security.clamp_text(str(value), 2000))
