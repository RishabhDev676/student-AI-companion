"""Dashboard data helpers for the Ruia Student Companion app."""

from __future__ import annotations

from typing import Any


def _value(row: dict[str, Any] | Any, key: str) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    return row[key]


def _details_object(details: Any) -> dict[str, Any]:
    if isinstance(details, dict):
        return details
    if not details:
        return {}
    if isinstance(details, str):
        try:
            import json

            parsed = json.loads(details)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def build_dashboard_snapshot(plans: list[Any], exams: list[Any], quizzes: list[Any]) -> dict[str, Any]:
    """Return simple chart-friendly data for the main dashboard."""
    counts = {
        "Plans": len(plans),
        "Exams": len(exams),
        "Quizzes": len(quizzes),
    }

    quiz_scores: list[dict[str, Any]] = []
    for row in quizzes:
        details = _details_object(_value(row, "details"))
        score = details.get("score")
        if score is None:
            score = _value(row, "confidence_score")
        created_at = _value(row, "created_at") or ""
        try:
            score_value = float(score)
        except (TypeError, ValueError):
            continue
        quiz_scores.append({
            "date": created_at[:10] if created_at else "unknown",
            "score": score_value,
        })

    exam_confidence: list[dict[str, Any]] = []
    for row in exams:
        subject = _value(row, "subject") or _value(row, "title") or "Unknown"
        score = _value(row, "confidence_score")
        try:
            score_value = float(score)
        except (TypeError, ValueError):
            continue
        exam_confidence.append({
            "subject": subject,
            "confidence": score_value,
        })

    return {
        "counts": counts,
        "quiz_scores": sorted(quiz_scores, key=lambda item: item["date"]),
        "exam_confidence": exam_confidence,
    }
