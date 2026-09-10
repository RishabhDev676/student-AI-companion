"""Ruia AI Student Companion — Study Planner, Exam Tracker, Quiz Generator."""

from __future__ import annotations

import base64
import importlib
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

import analytics
import db
import security
from ai_service import AIError, call_ai, keys_configured, remember_insights

# Streamlit keeps imported modules in memory across reruns. Reload local
# helpers so new functions (e.g. db.get_chat) are visible without a full restart.
db = importlib.reload(db)
analytics = importlib.reload(analytics)
security = importlib.reload(security)

ROOT = Path(__file__).resolve().parent
ICON_PATH = ROOT / "icon.png"
APP_NAME = "Ruia Pulse"
APP_TAGLINE = "Student companion · planner, exams, quizzes"

st.set_page_config(
    page_title=APP_NAME,
    page_icon=str(ICON_PATH) if ICON_PATH.exists() else "✦",
    layout="wide",
)
db.init_db()

MEMORY_LABELS = {
    "subjects": "Subjects",
    "hours_per_day": "Hours / day",
    "current_focus": "Focus",
    "latest_plan_summary": "Latest plan",
    "weak_topics": "Weak topics",
    "last_quiz_subject": "Last quiz subject",
    "last_quiz_topic": "Last quiz topic",
    "last_quiz_score": "Last quiz score",
    "last_quiz_missed_topics": "Missed topics",
    "next_exam": "Next exam",
    "exam_confidence": "Exam confidence",
    "latest_exam_advice": "Revision note",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
          .stApp { background: #f6f5f2; color: #1c1c1a; }
          [data-testid="stHeader"] { background: transparent; }
          .stAppDeployButton { display: none; }
          footer { visibility: hidden; }
          .brand-shell {
            background: linear-gradient(135deg, #1f1e1d 0%, #4d443d 100%);
            border-radius: 22px;
            padding: 1.05rem 1.2rem;
            margin-bottom: 1rem;
            box-shadow: 0 14px 30px rgba(35, 29, 24, 0.12);
          }
          .brand-shell .brand-title {
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.04em;
            color: #f7f4ef;
            margin: 0;
            line-height: 1.1;
          }
          .brand-shell .brand-tag {
            font-size: 0.9rem;
            color: #e7dfd5;
            margin-top: 0.25rem;
            opacity: 0.95;
          }
          .block-container { padding: 1.6rem 2.2rem 8rem; max-width: 1180px; }
          h1, h2, h3 { font-weight: 560; letter-spacing: -0.03em; color: #171716; }
          [data-testid="stSidebar"] {
            background: #efeee8;
            border-right: 1px solid #e4e1d8;
          }
          .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
            border-bottom: 1px solid #e4e1d8;
          }
          .stTabs [data-baseweb="tab"] {
            padding: 0.55rem 0.9rem;
            font-weight: 500;
          }
          div[data-testid="stForm"] {
            background: #fff;
            border: 1px solid #e7e4dc;
            border-radius: 16px;
            padding: 1.1rem 1.15rem 0.4rem;
          }
          [data-testid="stExpander"] {
            background: #fff;
            border: 1px solid #e7e4dc;
            border-radius: 14px;
            margin-bottom: 0.55rem;
          }
          [data-testid="stTextInput"] input,
          [data-testid="stTextArea"] textarea {
            background: #faf8f4 !important;
            color: #1c1c1a !important;
          }
          div[data-testid="stMetric"] {
            background: #fff;
            border: 1px solid #e7e4dc;
            border-radius: 14px;
            padding: 0.7rem 0.9rem;
          }
          .record {
            background: #fff;
            border: 1px solid #e7e4dc;
            border-radius: 14px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.65rem;
          }
          .record h4 { margin: 0 0 0.2rem; font-size: 0.95rem; color: #171716; }
          .muted { color: #7a776e; font-size: 0.8rem; }
          .pill {
            display: inline-block;
            font-size: 0.72rem;
            letter-spacing: 0.02em;
            padding: 0.12rem 0.5rem;
            border-radius: 999px;
            background: #efeae0;
            color: #4a4840;
            margin-right: 0.35rem;
          }
          .pill.done { background: #e5efe6; color: #2f5a38; }
          .pill.warn { background: #f3ead8; color: #6a4b12; }
          .section-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #8a867c;
            margin: 0 0 0.7rem;
          }
          [data-testid="stChatInput"] {
            position: fixed !important;
            right: 1.15rem;
            bottom: 1.15rem;
            width: min(390px, calc(100vw - 1.6rem));
            z-index: 10000;
            background: #fff;
            border: 1px solid #e7e4dc;
            border-radius: 16px;
            padding: 0.35rem 0.45rem;
            box-shadow: 0 16px 44px rgba(40, 36, 28, 0.14);
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_ai_error(exc: Exception) -> None:
    st.error(str(exc))


def pretty_dt(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%d %b · %H:%M")
    except ValueError:
        return value[:16]


def parse_details(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"tasks": data}
    except json.JSONDecodeError:
        return {"tasks": [raw]}


def record_card(title: str, meta: str, pills: list[str] | None = None, body: str = "") -> None:
    pills_html = "".join(
        f'<span class="pill">{security.escape_html(p)}</span>' for p in (pills or []) if p
    )
    body_html = (
        f"<div style='margin-top:0.45rem;font-size:0.9rem'>{security.escape_html(body)}</div>"
        if body
        else ""
    )
    st.markdown(
        f"""
        <div class="record">
          <h4>{security.escape_html(title)}</h4>
          <div class="muted">{pills_html}{security.escape_html(meta)}</div>
          {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    st.sidebar.markdown('<p class="section-label">Memory</p>', unsafe_allow_html=True)
    st.sidebar.caption("Shared across planner, exams, and quizzes.")
    ctx = db.get_all_context()
    if not ctx:
        st.sidebar.caption("Nothing saved yet.")
    else:
        for key, value in ctx.items():
            label = MEMORY_LABELS.get(key, key.replace("_", " ").title())
            snippet = value if len(value) < 140 else value[:137] + "…"
            st.sidebar.markdown(f"**{label}**")
            st.sidebar.caption(snippet)
    if not keys_configured():
        st.sidebar.error("No Gemini API key in `.env.local`.")

    st.sidebar.divider()
    st.sidebar.markdown('<p class="section-label">Ask Ruia</p>', unsafe_allow_html=True)
    st.sidebar.caption("Instant doubts. Uses your saved plans and quiz misses.")
    if "chat_messages" not in st.session_state:
        chat_rows = db.get_chat(24) if hasattr(db, "get_chat") else []
        st.session_state.chat_messages = [
            {"role": row["role"], "content": row["content"]} for row in chat_rows
        ]
    log = st.sidebar.container(height=260)
    with log:
        if not st.session_state.chat_messages:
            st.caption("Try: explain a missed quiz topic, or walk through a formula.")
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])


def grouped_plan_batches(items: list) -> list[tuple[str, list]]:
    batches: dict[str, list] = defaultdict(list)
    order: list[str] = []
    for row in items:
        details = parse_details(row["details"])
        batch = details.get("batch_id") or (row["created_at"] or "")[:16]
        if batch not in batches:
            order.append(batch)
        batches[batch].append((row, details))
    return [(key, batches[key]) for key in order]


def safe_ai(*args, **kwargs):
    ok, ts = security.allow_ai_call(float(st.session_state.get("_ai_ts", 0.0)))
    if not ok:
        raise AIError("Please wait a moment before another AI request.")
    st.session_state["_ai_ts"] = ts
    return call_ai(*args, **kwargs)


def plan_markdown(focus: str, summary: str, rows_sorted: list, created: str = "") -> str:
    lines = [f"# {focus}", ""]
    if created:
        lines += [f"Saved: {pretty_dt(created)}", ""]
    if summary:
        lines += [summary, ""]
    for row, detail in rows_sorted:
        lines.append(f"## {row['title']}")
        for task in detail.get("tasks") or []:
            lines.append(f"- {task}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def quiz_markdown(row, details: dict) -> str:
    lines = [
        f"# {row['title']}",
        f"Subject: {row['subject'] or ''}",
        f"Score: {int(row['confidence_score'] or 0)}%",
        f"Date: {pretty_dt(row['created_at'])}",
        "",
    ]
    missed = list(dict.fromkeys(details.get("missed") or []))
    if missed:
        lines.append("Missed: " + ", ".join(missed))
        lines.append("")
    for i, item in enumerate(details.get("results") or [], 1):
        mark = "correct" if item.get("correct") else "missed"
        lines.append(f"{i}. ({mark}) {item.get('question', '')}")
        if not item.get("correct"):
            lines.append(f"   Yours: {item.get('your', '')}")
            lines.append(f"   Answer: {item.get('answer', '')}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def exams_markdown(exams: list) -> str:
    lines = ["# Exam records", ""]
    for row in exams:
        lines.append(
            f"- **{row['title']}** ({row['subject']}) · {row['due_date'] or ''} · "
            f"{row['status']} · confidence {row['confidence_score']}"
        )
    return "\n".join(lines).strip() + "\n"


def export_everything() -> str:
    parts = ["# Ruia records", ""]
    plans = grouped_plan_batches(db.query_tasks("plan_item", limit=200))
    parts.append("## Plans")
    if not plans:
        parts.append("None yet.")
    for _batch, rows in plans:
        rows_sorted = sorted(rows, key=lambda x: x[0]["id"])
        first, details = rows_sorted[0]
        focus = details.get("focus") or first["subject"] or "Study plan"
        parts.append(plan_markdown(focus, details.get("summary") or "", rows_sorted, first["created_at"]))
    parts.append("## Exams")
    exams = db.query_tasks("exam", limit=200)
    parts.append(exams_markdown(exams) if exams else "None yet.")
    parts.append("## Quizzes")
    quizzes = db.query_tasks("quiz_result", limit=200)
    if not quizzes:
        parts.append("None yet.")
    for row in quizzes:
        parts.append(quiz_markdown(row, parse_details(row["details"])))
    parts.append("## Chat")
    chat = db.get_chat(80)
    if not chat:
        parts.append("None yet.")
    for msg in chat:
        parts.append(f"**{msg['role']}:** {msg['content']}")
        parts.append("")
    return "\n".join(parts)


def study_planner_tab() -> None:
    create, library = st.columns([0.42, 0.58], gap="large")

    with create:
        st.markdown('<p class="section-label">New plan</p>', unsafe_allow_html=True)
        with st.form("planner_form"):
            subjects = st.text_input("Subjects", placeholder="Physics, Chemistry, Maths", max_chars=200)
            exam_window = st.text_input("Exam window", placeholder="Physics board exam in 14 days", max_chars=200)
            hours = st.slider("Hours per day", 1, 10, 3)
            extra = st.text_area("Notes", placeholder="I struggle with numericals.", height=80, max_chars=800)
            submitted = st.form_submit_button("Generate plan", use_container_width=True)

        if submitted:
            if not subjects.strip():
                st.warning("Enter at least one subject.")
            else:
                user_prompt = (
                    f"Create a practical 7-day study plan.\n"
                    f"Subjects: {subjects}\n"
                    f"Exam window: {exam_window or 'not specified'}\n"
                    f"Hours per day: {hours}\n"
                    f"Notes: {extra or 'none'}\n\n"
                    "Prioritize any weak_topics / last_quiz_missed_topics in student memory. "
                    "Return JSON with keys: summary (string), focus_subject (string), "
                    "days (array of {day, focus, tasks: [string]})."
                )
                try:
                    with st.spinner("Building your plan…"):
                        data = safe_ai(
                            "You are a focused academic coach for a college student at Ruia. "
                            "Be specific and realistic. Prefer weaker topics first.",
                            user_prompt,
                            expect_json=True,
                        )
                except AIError as exc:
                    show_ai_error(exc)
                    return

                summary = data.get("summary", "")
                focus = data.get("focus_subject", "")
                days = data.get("days") or []
                batch_id = f"plan-{uuid4().hex[:8]}"

                remember_insights(
                    {
                        "subjects": subjects,
                        "hours_per_day": str(hours),
                        "current_focus": focus or subjects.split(",")[0].strip(),
                        "latest_plan_summary": summary[:500],
                    }
                )

                for day in days:
                    title = f"Day {day.get('day', '?')}: {day.get('focus', 'Study')}"
                    tasks = day.get("tasks") or []
                    db.add_task(
                        "plan_item",
                        title=title,
                        subject=day.get("focus") or focus,
                        status="planned",
                        details=json.dumps(
                            {
                                "tasks": tasks,
                                "batch_id": batch_id,
                                "summary": summary,
                                "focus": focus,
                            }
                        ),
                    )

                st.session_state["last_plan"] = data
                st.session_state["last_plan_md"] = plan_markdown(
                    focus or subjects,
                    summary,
                    [
                        (
                            {"title": f"Day {d.get('day', '?')}: {d.get('focus', 'Study')}"},
                            {"tasks": d.get("tasks") or []},
                        )
                        for d in days
                    ],
                )
                st.success("Saved to your library.")

        plan = st.session_state.get("last_plan")
        if plan:
            weak = db.get_context("last_quiz_missed_topics") or db.get_context("weak_topics")
            if weak and weak != "none":
                st.markdown(
                    f'<span class="pill warn">Adapted for {weak}</span>',
                    unsafe_allow_html=True,
                )
            if plan.get("summary"):
                st.markdown(plan["summary"])
            if st.session_state.get("last_plan_md"):
                st.download_button(
                    "Download this plan",
                    data=st.session_state["last_plan_md"],
                    file_name="ruia-study-plan.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="dl_current_plan",
                )
            for day in plan.get("days") or []:
                with st.expander(f"Day {day.get('day', '')}  ·  {day.get('focus', 'Focus')}"):
                    for task in day.get("tasks") or []:
                        st.markdown(f"- {task}")
        elif db.get_context("latest_plan_summary"):
            st.caption("Latest saved summary")
            st.write(db.get_context("latest_plan_summary"))

    with library:
        st.markdown('<p class="section-label">Saved planners</p>', unsafe_allow_html=True)
        items = db.query_tasks("plan_item", limit=60)
        groups = grouped_plan_batches(items)
        if not groups:
            st.caption("No plans yet. Generate one to fill this library.")
        else:
            for i, (_batch, rows) in enumerate(groups):
                rows_sorted = sorted(rows, key=lambda x: x[0]["id"])
                first_row, details = rows_sorted[0]
                summary = details.get("summary") or ""
                focus = details.get("focus") or first_row["subject"] or "Study plan"
                header = f"{focus}  ·  {len(rows)} days"
                md = plan_markdown(focus, summary, rows_sorted, first_row["created_at"])
                with st.expander(header, expanded=(i == 0)):
                    st.caption(pretty_dt(first_row["created_at"]))
                    st.download_button(
                        "Download",
                        data=md,
                        file_name=f"{security.safe_filename('ruia-plan-' + str(_batch))}.md",
                        mime="text/markdown",
                        key=f"dl_plan_{_batch}",
                    )
                    if summary:
                        st.write(summary)
                    for row, detail in rows_sorted:
                        tasks = detail.get("tasks") or []
                        st.markdown(f"**{row['title']}**")
                        for task in tasks:
                            st.markdown(f"- {task}")


def exam_tracker_tab() -> None:
    create, records = st.columns([0.4, 0.6], gap="large")

    with create:
        st.markdown('<p class="section-label">Add exam</p>', unsafe_allow_html=True)
        with st.form("exam_form"):
            title = st.text_input("Exam name", placeholder="Semester Physics paper", max_chars=120)
            subject = st.text_input("Subject", placeholder="Physics", max_chars=80)
            due = st.date_input("Date", value=date.today())
            confidence = st.slider("Confidence", 1, 10, 5)
            add = st.form_submit_button("Save exam", use_container_width=True)

        if add:
            if not title.strip() or not subject.strip():
                st.warning("Name and subject are required.")
            else:
                db.add_task(
                    "exam",
                    title=title.strip(),
                    subject=subject.strip(),
                    due_date=due.isoformat(),
                    confidence_score=float(confidence),
                    status="upcoming",
                )
                remember_insights(
                    {
                        "next_exam": f"{title.strip()} ({subject.strip()} on {due.isoformat()})",
                        "exam_confidence": f"{subject.strip()}={confidence}/10",
                    }
                )
                st.success("Exam added.")

        if st.button("Suggest revision order", use_container_width=True):
            exams = db.query_tasks("exam", limit=30)
            exam_lines = [
                f"- {r['title']} | {r['subject']} | {r['due_date']} | confidence {r['confidence_score']}"
                for r in exams
                if r["status"] != "done"
            ]
            if not exam_lines:
                st.warning("Add at least one upcoming exam first.")
            else:
                try:
                    with st.spinner("Ranking exams…"):
                        advice = safe_ai(
                            "You are an exam coach. Rank revision using due dates, low confidence, "
                            "and weak_topics from student memory. Use short markdown (bullets).",
                            "Upcoming exams:\n" + "\n".join(exam_lines),
                        )
                    st.markdown(advice)
                    remember_insights({"latest_exam_advice": advice[:500]})
                except AIError as exc:
                    show_ai_error(exc)

    with records:
        st.markdown('<p class="section-label">Exam records</p>', unsafe_allow_html=True)
        exams = db.query_tasks("exam", limit=30)
        upcoming = [r for r in exams if r["status"] != "done"]
        done = [r for r in exams if r["status"] == "done"]

        if exams:
            st.download_button(
                "Download exams",
                data=exams_markdown(exams),
                file_name="ruia-exams.md",
                mime="text/markdown",
                key="dl_exams",
            )
        if not exams:
            st.caption("No exams saved.")
        else:
            st.caption("Upcoming")
            for row in upcoming:
                cols = st.columns([5, 1])
                with cols[0]:
                    record_card(
                        row["title"],
                        pretty_dt(row["due_date"]) or (row["due_date"] or ""),
                        pills=[row["subject"] or "", f"{int(row['confidence_score'] or 0)}/10"],
                    )
                if cols[1].button("Done", key=f"exam_done_{row['id']}"):
                    db.update_task_status(row["id"], "done")
                    st.rerun()
            if done:
                st.caption("Completed")
                for row in done:
                    record_card(
                        row["title"],
                        row["due_date"] or "",
                        pills=[row["subject"] or "", "done"],
                    )


def quiz_generator_tab() -> None:
    create, records = st.columns([0.55, 0.45], gap="large")

    with create:
        st.markdown('<p class="section-label">New quiz</p>', unsafe_allow_html=True)
        with st.form("quiz_form"):
            subject = st.text_input("Subject", placeholder="Physics", max_chars=80)
            topic = st.text_input("Topic", placeholder="Thermodynamics", max_chars=120)
            n = st.slider("Questions", 3, 8, 4)
            generate = st.form_submit_button("Generate quiz", use_container_width=True)

        if generate:
            if not subject.strip() or not topic.strip():
                st.warning("Subject and topic are required.")
            else:
                prompt = (
                    f"Generate {n} multiple-choice questions on {subject}: {topic}. "
                    "Each question has exactly 4 options. "
                    'JSON shape: {"questions":[{"question":"","options":["","","",""],'
                    '"correct_index":0,"topic":""}]} '
                    "correct_index is 0-3."
                )
                try:
                    with st.spinner("Generating quiz…"):
                        data = safe_ai(
                            "You are a strict but fair examiner. Keep questions at undergraduate level.",
                            prompt,
                            expect_json=True,
                        )
                except AIError as exc:
                    show_ai_error(exc)
                    return
                questions = data.get("questions") or []
                if not questions:
                    st.error("AI returned no questions.")
                    return
                st.session_state["quiz"] = {
                    "subject": subject.strip(),
                    "topic": topic.strip(),
                    "questions": questions,
                }
                st.session_state.pop("quiz_submitted", None)

        quiz = st.session_state.get("quiz")
        if quiz:
            st.markdown(f"**{quiz['subject']}**  ·  {quiz['topic']}")
            answers = {}
            with st.form("quiz_answers"):
                for i, q in enumerate(quiz["questions"]):
                    options = q.get("options") or []
                    answers[i] = st.radio(
                        f"{i+1}. {q.get('question', '')}",
                        options=list(range(len(options))),
                        format_func=lambda idx, opts=options: opts[idx] if idx < len(opts) else str(idx),
                        key=f"q_{i}",
                    )
                submit = st.form_submit_button("Submit", use_container_width=True)

            if submit:
                missed = []
                correct = 0
                results = []
                for i, q in enumerate(quiz["questions"]):
                    chosen = answers[i]
                    ok = int(q.get("correct_index", 0))
                    is_right = chosen == ok
                    if is_right:
                        correct += 1
                    else:
                        missed.append(q.get("topic") or quiz["topic"])
                    opts = q.get("options") or []
                    results.append(
                        {
                            "question": q.get("question"),
                            "correct": is_right,
                            "your": opts[chosen] if chosen < len(opts) else "",
                            "answer": opts[ok] if ok < len(opts) else "",
                        }
                    )
                total = len(quiz["questions"])
                score = round(100 * correct / total) if total else 0
                missed_str = ", ".join(dict.fromkeys(missed)) if missed else "none"

                db.add_task(
                    "quiz_result",
                    title=f"{quiz['subject']}: {quiz['topic']} ({score}%)",
                    subject=quiz["subject"],
                    confidence_score=float(score),
                    status="completed",
                    details=json.dumps(
                        {
                            "missed": missed,
                            "score": score,
                            "topic": quiz["topic"],
                            "results": results,
                            "questions": quiz["questions"],
                        }
                    ),
                )
                remember_insights(
                    {
                        "weak_topics": missed_str if missed else db.get_context("weak_topics") or "none",
                        "last_quiz_subject": quiz["subject"],
                        "last_quiz_topic": quiz["topic"],
                        "last_quiz_score": f"{score}% ({correct}/{total})",
                        "last_quiz_missed_topics": missed_str,
                    }
                )
                st.session_state["quiz_submitted"] = results
                st.session_state["quiz_score"] = score
                st.rerun()

            if st.session_state.get("quiz_submitted"):
                st.markdown(
                    f'<span class="pill">Score {st.session_state.get("quiz_score")}%</span>',
                    unsafe_allow_html=True,
                )
                for row in st.session_state["quiz_submitted"]:
                    mark = "Correct" if row["correct"] else "Missed"
                    st.markdown(f"**{mark}**  ·  {row['question']}")
                    if not row["correct"]:
                        st.caption(f"Yours: {row['your']}  ·  Answer: {row['answer']}")
                missed = db.get_context("last_quiz_missed_topics")
                if missed and missed != "none":
                    st.caption(f"Saved to memory: {missed}. Open Planner to adapt the next plan.")

    with records:
        st.markdown('<p class="section-label">Quiz records</p>', unsafe_allow_html=True)
        past = db.query_tasks("quiz_result", limit=12)
        if not past:
            st.caption("No quizzes yet.")
        else:
            for row in past:
                details = parse_details(row["details"])
                missed = list(dict.fromkeys(details.get("missed") or []))
                missed_txt = ", ".join(missed) if missed else "No misses"
                with st.expander(f"{row['title']}  ·  {pretty_dt(row['created_at'])}"):
                    st.caption(missed_txt)
                    st.download_button(
                        "Download quiz",
                        data=quiz_markdown(row, details),
                        file_name=f"{security.safe_filename(f'ruia-quiz-{row['id']}')}.md",
                        mime="text/markdown",
                        key=f"dl_quiz_{row['id']}",
                    )
                    results = details.get("results") or []
                    if results:
                        for item in results:
                            mark = "Correct" if item.get("correct") else "Missed"
                            st.markdown(f"**{mark}**  ·  {item.get('question', '')}")
                            if not item.get("correct"):
                                st.caption(
                                    f"Yours: {item.get('your', '')}  ·  Answer: {item.get('answer', '')}"
                                )
                    else:
                        record_card(
                            row["title"],
                            pretty_dt(row["created_at"]),
                            pills=[row["subject"] or "", f"{int(row['confidence_score'] or 0)}%"],
                            body=missed_txt,
                        )


def history_tab() -> None:
    st.markdown('<p class="section-label">Past work</p>', unsafe_allow_html=True)
    st.download_button(
        "Download everything",
        data=export_everything(),
        file_name="ruia-records.md",
        mime="text/markdown",
        key="dl_all",
    )

    plans, exams, quizzes, chats = st.tabs(["Plans", "Exams", "Quizzes", "Chat"])

    with plans:
        groups = grouped_plan_batches(db.query_tasks("plan_item", limit=200))
        if not groups:
            st.caption("No saved plans yet.")
        for _batch, rows in groups:
            rows_sorted = sorted(rows, key=lambda x: x[0]["id"])
            first, details = rows_sorted[0]
            focus = details.get("focus") or first["subject"] or "Study plan"
            with st.expander(f"{focus}  ·  {pretty_dt(first['created_at'])}  ·  {len(rows)} days"):
                if details.get("summary"):
                    st.write(details["summary"])
                st.download_button(
                    "Download",
                    data=plan_markdown(focus, details.get("summary") or "", rows_sorted, first["created_at"]),
                    file_name=f"{security.safe_filename('ruia-plan-' + str(_batch))}.md",
                    mime="text/markdown",
                    key=f"hist_dl_plan_{_batch}",
                )
                for row, detail in rows_sorted:
                    st.markdown(f"**{row['title']}**")
                    for task in detail.get("tasks") or []:
                        st.markdown(f"- {task}")

    with exams:
        exam_rows = db.query_tasks("exam", limit=200)
        if not exam_rows:
            st.caption("No exams yet.")
        else:
            st.download_button(
                "Download exams",
                data=exams_markdown(exam_rows),
                file_name="ruia-exams.md",
                mime="text/markdown",
                key="hist_dl_exams",
            )
            for row in exam_rows:
                with st.expander(f"{row['title']}  ·  {row['status']}"):
                    st.write(f"Subject: {row['subject']}")
                    st.write(f"Date: {row['due_date'] or '—'}")
                    st.write(f"Confidence: {row['confidence_score']}")

    with quizzes:
        past = db.query_tasks("quiz_result", limit=200)
        if not past:
            st.caption("No quizzes yet.")
        for row in past:
            details = parse_details(row["details"])
            with st.expander(f"{row['title']}  ·  {pretty_dt(row['created_at'])}"):
                st.download_button(
                    "Download quiz",
                    data=quiz_markdown(row, details),
                    file_name=f"ruia-quiz-{row['id']}.md",
                    mime="text/markdown",
                    key=f"hist_dl_quiz_{row['id']}",
                )
                results = details.get("results") or []
                if not results:
                    st.caption("Only the score was saved for this older quiz.")
                for item in results:
                    mark = "Correct" if item.get("correct") else "Missed"
                    st.markdown(f"**{mark}**  ·  {item.get('question', '')}")
                    if not item.get("correct"):
                        st.caption(
                            f"Yours: {item.get('your', '')}  ·  Answer: {item.get('answer', '')}"
                        )

    with chats:
        messages = db.get_chat(80)
        if not messages:
            st.caption("No chat yet. Ask a doubt in the Ask Ruia box.")
        for msg in messages:
            st.markdown(f"**{msg['role']}** · {pretty_dt(msg['created_at'])}")
            st.write(msg["content"])


def insights_tab() -> None:
    st.markdown('<p class="section-label">Progress</p>', unsafe_allow_html=True)
    quizzes = list(reversed(db.query_tasks("quiz_result", limit=40)))
    exams = db.query_tasks("exam", limit=40)
    quizzes_all = db.query_tasks("quiz_result", limit=200)
    exams_all = db.query_tasks("exam", limit=200)

    c1, c2, c3 = st.columns(3)
    avg = 0
    if quizzes_all:
        avg = round(sum(float(q["confidence_score"] or 0) for q in quizzes_all) / len(quizzes_all))
    c1.metric("Quizzes taken", len(quizzes_all))
    c2.metric("Average score", f"{avg}%" if quizzes_all else "—")
    c3.metric("Upcoming exams", len([e for e in exams_all if e["status"] != "done"]))

    left, right = st.columns(2, gap="large")
    with left:
        st.caption("Quiz scores")
        if quizzes:
            score_map = {
                f"{i+1}. {row['subject'] or 'Quiz'}": float(row["confidence_score"] or 0)
                for i, row in enumerate(quizzes)
            }
            st.bar_chart(score_map, use_container_width=True)
        else:
            st.caption("Take a quiz to see your score trend.")
        st.caption("Exam confidence")
        if exams:
            conf_map = {
                (row["subject"] or row["title"] or f"Exam {row['id']}"): float(row["confidence_score"] or 0)
                for row in exams
            }
            st.bar_chart(conf_map, use_container_width=True)
        else:
            st.caption("Add exams to compare readiness.")

    with right:
        st.caption("Missed topics")
        counts: dict[str, int] = defaultdict(int)
        for row in quizzes_all:
            details = parse_details(row["details"])
            for topic in dict.fromkeys(details.get("missed") or []):
                if topic and topic != "none":
                    counts[str(topic)] += 1
        if counts:
            st.bar_chart(dict(counts), use_container_width=True)
        else:
            st.caption("Missed quiz topics will appear here.")
        st.caption("Activity mix")
        mix = {
            "Plans": len(grouped_plan_batches(db.query_tasks("plan_item", limit=200))),
            "Exams": len(exams_all),
            "Quizzes": len(quizzes_all),
        }
        st.bar_chart(mix, use_container_width=True)


def handle_chat_input() -> None:
    prompt = st.chat_input("Ask Ruia a doubt…")
    if not prompt:
        return
    prompt = security.clamp_text(prompt, security.MAX_CHAT)
    if not prompt:
        return
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    db.add_chat("user", prompt)
    try:
        reply = safe_ai(
            "You are Ruia, a calm, precise tutor. Solve the student's doubt clearly. "
            "Use their saved weak topics and plans when relevant. Keep answers short, "
            "with steps if it is a numerical or coding problem.",
            prompt,
            max_tokens=1024,
        )
    except AIError as exc:
        reply = str(exc)
    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
    db.add_chat("assistant", reply)
    st.rerun()


def main() -> None:
    inject_css()
    plans = db.query_tasks("plan_item", limit=200)
    exams = db.query_tasks("exam", limit=200)
    quizzes = db.query_tasks("quiz_result", limit=200)

    st.markdown(
        f"""
        <div class="brand-shell">
          <div style="display:flex; align-items:center; gap:0.95rem;">
            <img src="data:image/png;base64,{base64.b64encode(ICON_PATH.read_bytes()).decode('utf-8')}" style="width:52px; height:52px; border-radius:16px; object-fit:cover;" />
            <div>
              <div class="brand-title">{APP_NAME}</div>
              <div class="brand-tag">{APP_TAGLINE}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Saved plans", len(grouped_plan_batches(plans)))
    m2.metric("Exams", len(exams))
    m3.metric("Quizzes", len(quizzes))

    snapshot = analytics.build_dashboard_snapshot(plans, exams, quizzes)
    counts_df = pd.DataFrame(
        {
            "Category": list(snapshot["counts"].keys()),
            "Value": list(snapshot["counts"].values()),
        }
    )

    st.markdown("### Dashboard insights")
    st.caption("Quick visual overview of student activity and progress.")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Records by type")
        st.bar_chart(counts_df.set_index("Category")["Value"])

    with chart_col2:
        st.subheader("Quiz scores")
        if snapshot["quiz_scores"]:
            quiz_df = pd.DataFrame(snapshot["quiz_scores"])
            st.line_chart(quiz_df.set_index("date")["score"])
        else:
            st.info("No quiz scores yet. Complete a quiz to see score trends.")

    if snapshot["exam_confidence"]:
        exam_df = pd.DataFrame(snapshot["exam_confidence"])
        st.subheader("Exam confidence")
        st.bar_chart(exam_df.set_index("subject")["confidence"])

    render_sidebar()
    tab1, tab2, tab3, tab4 = st.tabs(["Planner", "Exams", "Quizzes", "History"])
    with tab1:
        st.write("")
        study_planner_tab()
    with tab2:
        st.write("")
        exam_tracker_tab()
    with tab3:
        st.write("")
        quiz_generator_tab()
    with tab4:
        st.write("")
        history_tab()

    handle_chat_input()


main()
