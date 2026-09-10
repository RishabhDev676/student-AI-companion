import json
import math
from ai import ai, safe_json_parse

URGENCY_SYSTEM_PROMPT = """You are an academic risk analyst for a student companion app.
Given a list of exams with dates and self-rated confidence (1-5, where 1=very weak, 5=very confident),
compute an urgency score for each exam and explain your reasoning briefly.

Rules:
- Fewer days left + lower confidence = higher urgency
- Urgency score is 0-100
- Be specific in reasoning: mention days left AND confidence together
- Output ONLY valid JSON, no markdown fences, no commentary

Output schema:
{
  "results": [
    {"subject": "string", "urgency_score": number, "reason": "one short sentence"}
  ]
}"""


def calculate_fallback_urgency(exams: list[dict]) -> dict:
    """Deterministic heuristic calculation for exam urgency.
    
    Used as an offline/resilient fallback when the LLM API is unavailable,
    quota-limited, or returns invalid JSON.
    Follows all prompt rules:
    - Urgency score 0-100
    - Fewer days left + lower confidence = higher urgency
    - Specific reasoning mentioning days left AND confidence level
    """
    results = []
    for exam in exams:
        subject = exam.get("subject", "Unknown Subject")
        days_left = max(0, int(exam.get("days_left", 0)))
        confidence = max(1, min(5, int(exam.get("confidence", 3))))

        # Days weight (0 to 60 points): exponential decay as days increase
        # 0 days -> 60, 6 days -> ~36, 14 days -> ~18, 30 days -> ~5
        day_weight = math.exp(-days_left / 12.0)
        days_score = 60.0 * day_weight

        # Confidence weight (0 to 40 points): lower confidence -> higher urgency
        # 1 -> 40, 2 -> 30, 3 -> 20, 4 -> 10, 5 -> 0
        conf_score = 40.0 * ((5 - confidence) / 4.0)

        urgency_score = int(round(max(0, min(100, days_score + conf_score))))

        # Determine qualitative label
        if urgency_score >= 80:
            level = "critical"
        elif urgency_score >= 60:
            level = "high"
        elif urgency_score >= 40:
            level = "moderate"
        else:
            level = "low"

        day_text = "today" if days_left == 0 else f"in {days_left} day{'s' if days_left != 1 else ''}"
        reason = (
            f"Exam is {day_text} with a low confidence of {confidence}/5, requiring {level} preparation urgency."
            if confidence <= 2
            else f"Exam is {day_text} with confidence rated {confidence}/5, reflecting {level} urgency."
        )

        results.append({
            "subject": subject,
            "urgency_score": urgency_score,
            "reason": reason
        })

    return {"results": results}


def score_urgency(exams: list[dict], fallback_on_error: bool = True) -> dict:
    """Score the urgency of upcoming exams based on days left and confidence.
    
    Args:
        exams: List of dicts, e.g. [{"subject": "DSA", "days_left": 6, "confidence": 2}, ...]
        fallback_on_error: If True, uses deterministic calculation if AI fails or returns invalid format.
    
    Returns:
        dict: {"results": [{"subject": "...", "urgency_score": int, "reason": "..."}]}
    """
    if not exams:
        return {"results": []}

    prompt = f"Today's exam list:\n{json.dumps(exams)}\n\nScore urgency for each."
    raw = ai(prompt, system=URGENCY_SYSTEM_PROMPT, max_tokens=800)

    # 1. Handle if raw is already parsed dict
    if isinstance(raw, dict) and "results" in raw:
        return raw

    # 2. Handle string output: safely parse (strips markdown fences and commentary)
    if isinstance(raw, str):
        parsed = safe_json_parse(raw)
        if isinstance(parsed, dict) and "results" in parsed:
            return parsed
        
        # Try direct json.loads as secondary attempt
        try:
            direct_parsed = json.loads(raw)
            if isinstance(direct_parsed, dict) and "results" in direct_parsed:
                return direct_parsed
        except Exception:
            pass

    # 3. If AI call or parsing failed, fallback or raise
    if fallback_on_error:
        print("[Urgency Scorer] AI unavailable or response malformed. Using heuristic calculation.")
        return calculate_fallback_urgency(exams)

    raise ValueError(f"Failed to score exams via AI. Raw response: {raw}")


if __name__ == "__main__":
    sample_exams = [
        {"subject": "DSA", "days_left": 6, "confidence": 2},
        {"subject": "Linear Algebra", "days_left": 1, "confidence": 1},
        {"subject": "Computer Networks", "days_left": 18, "confidence": 4},
        {"subject": "Operating Systems", "days_left": 3, "confidence": 3},
    ]

    print("Scoring exam urgency for:")
    print(json.dumps(sample_exams, indent=2))
    print("\nResult:")
    scored = score_urgency(sample_exams)
    print(json.dumps(scored, indent=2))
