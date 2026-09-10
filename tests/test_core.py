"""Unit tests that do not call the live Gemini API."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import db
from ai_service import AIError, parse_json
import security


class DbTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self.tmp.name) / "test.db"
        db.init_db()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_context_roundtrip(self) -> None:
        db.set_context("weak_topics", "Thermodynamics")
        self.assertEqual(db.get_context("weak_topics"), "Thermodynamics")
        self.assertEqual(db.get_all_context()["weak_topics"], "Thermodynamics")

    def test_tasks_and_chat_persist(self) -> None:
        task_id = db.add_task("quiz_result", "Physics: Heat (80%)", subject="Physics", confidence_score=80)
        self.assertTrue(task_id > 0)
        rows = db.query_tasks("quiz_result")
        self.assertEqual(len(rows), 1)
        self.assertTrue(hasattr(db, "get_chat"))
        db.add_chat("user", "What is entropy?")
        chat = db.get_chat()
        self.assertEqual(chat[0]["content"], "What is entropy?")
        self.assertEqual(chat[0]["role"], "user")


class SecurityTests(unittest.TestCase):
    def test_escape_html(self) -> None:
        self.assertIn("&lt;script&gt;", security.escape_html("<script>x</script>"))

    def test_clamp_and_filename(self) -> None:
        self.assertEqual(len(security.clamp_text("a" * 50, 10)), 10)
        self.assertEqual(security.safe_filename("../etc/passwd"), "etc-passwd")

    def test_rate_limit(self) -> None:
        ok, ts = security.allow_ai_call(0, now=10.0)
        self.assertTrue(ok)
        ok2, _ = security.allow_ai_call(ts, now=10.1)
        self.assertFalse(ok2)


class ParseJsonTests(unittest.TestCase):
    def test_fenced_json(self) -> None:
        self.assertEqual(parse_json('```json\n{"a": 1}\n```')["a"], 1)

    def test_invalid_json(self) -> None:
        with self.assertRaises(AIError):
            parse_json("not json")


if __name__ == "__main__":
    unittest.main()
