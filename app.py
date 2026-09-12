"""Ruia AI Student Companion — Study Planner, Exam Tracker, Quiz Generator."""

from __future__ import annotations

import importlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st
import altair as alt

import analytics
import db
import security
from ai_service import AIError, call_ai, keys_configured, remember_insights
from ui_components import (
    activity_streak,
    circular_progress,
    empty_state,
    inject_css,
    metric_row,
    pill,
    pretty_date,
    pretty_dt,
    render_exam_card,
    render_week_grid,
    section_header,
    snapshot_item,
)

# Streamlit keeps imported modules in memory across reruns. Reload local
# helpers so new functions (e.g. db.get_chat) are visible without a full restart.
db = importlib.reload(db)
analytics = importlib.reload(analytics)
security = importlib.reload(security)

ROOT = Path(__file__).resolve().parent
ICON_PATH = ROOT / "icon.png"
APP_NAME = "Ruia Pulse"
APP_TAGLINE = "Planner · exams · quizzes · tutor"

# Wide layout: weekly plan grid, exam lists, and history tables need horizontal
# room. CSS still caps the main column so lines stay readable on large screens.
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

# Sidebar radio instead of st.tabs or st.navigation:
# - Branding + student snapshot stay visible while switching workspaces.
# - Four study tools plus a dedicated tutor view (chat needs full width).
# - Multipage files would split a single-script app without a real gain.
NAV_ITEMS = ("Dashboard", "Planner", "Exams", "Quizzes", "Tutor", "History")


def go_to_page(page: str) -> None:
    st.session_state.current_page = page


def back_to_dashboard(key_suffix: str) -> None:
    st.button("← Back to Dashboard", key=f"back_{key_suffix}", on_click=go_to_page, args=("Dashboard",))


def show_ai_error(exc: Exception) -> None:
    st.error(str(exc))


def parse_details(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"tasks": data}
    except json.JSONDecodeError:
        return {"tasks": [raw]}


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


def ensure_chat_state() -> None:
    if "chat_messages" not in st.session_state:
        chat_rows = db.get_chat(24) if hasattr(db, "get_chat") else []
        st.session_state.chat_messages = [
            {"role": row["role"], "content": row["content"]} for row in chat_rows
        ]


def render_sidebar() -> str:
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    with st.sidebar:
        brand_cols = st.columns([1, 4])
        with brand_cols[0]:
            if ICON_PATH.exists():
                st.image(str(ICON_PATH), width=40)
            else:
                st.markdown('<div class="brand-mark">R</div>', unsafe_allow_html=True)
        with brand_cols[1]:
            st.markdown(
                f'<p class="brand-title">{APP_NAME}</p>'
                f'<p class="brand-tag">{APP_TAGLINE}</p>',
                unsafe_allow_html=True,
            )

        st.divider()
        page = st.radio("Workspace", NAV_ITEMS, key="current_page", label_visibility="collapsed")

        st.divider()
        section_header("Snapshot", "Student context")
        ctx = db.get_all_context()
        all_tasks = db.query_tasks(limit=200)
        snapshot_item("Weak topics", ctx.get("weak_topics") or ctx.get("last_quiz_missed_topics"), "None saved yet")
        snapshot_item("Next exam", ctx.get("next_exam"), "No exam on file")
        snapshot_item("Study streak", str(activity_streak(all_tasks)) + " day(s)", "0 day(s)")
        snapshot_item("Last quiz", ctx.get("last_quiz_score"), "No quiz yet")

        with st.expander("All memory"):
            if not ctx:
                st.caption("Nothing saved yet.")
            else:
                for key, value in ctx.items():
                    label = MEMORY_LABELS.get(key, key.replace("_", " ").title())
                    snippet = value if len(value) < 140 else value[:137] + "…"
                    st.markdown(f"**{label}**")
                    st.caption(snippet)

        if not keys_configured():
            st.error("No Gemini API key in `.env.local`.")

    return page


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------
def study_planner_tab() -> None:
    section_header("Study planner", "Seven-day plan")
    create, library = st.tabs(["✨ Create New Plan", "📚 My Library"])

    with create:
        section_header("New plan", "Inputs")
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

        st.divider()
        section_header("This week", "Generated plan")
        plan = st.session_state.get("last_plan")
        if plan:
            weak = db.get_context("last_quiz_missed_topics") or db.get_context("weak_topics")
            if weak and weak != "none":
                st.markdown(pill(f"Adapted for {weak}", "warn"), unsafe_allow_html=True)
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
            render_week_grid(plan.get("days") or [], db.get_context("hours_per_day"))
        elif db.get_context("latest_plan_summary"):
            st.caption("Latest saved summary")
            st.info(db.get_context("latest_plan_summary"))
        else:
            empty_state(
                "No plan generated yet",
                "Fill in subjects and hours, then generate a 7-day plan.",
                "▦",
            )

    with library:
        section_header("Saved planners", "Library")
        items = db.query_tasks("plan_item", limit=60)
        groups = grouped_plan_batches(items)
        if not groups:
            empty_state("No plans saved yet", "Generate one on the left to fill this library.", "▤")
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
                    lib_days = []
                    for row, detail in rows_sorted:
                        title = row["title"] or ""
                        day_num = title.split(":")[0].replace("Day", "").strip() if title else "?"
                        lib_days.append(
                            {
                                "day": day_num,
                                "focus": row["subject"] or title,
                                "tasks": detail.get("tasks") or [],
                            }
                        )
                    render_week_grid(lib_days, details.get("hours") or db.get_context("hours_per_day"))


# ---------------------------------------------------------------------------
# Exams
# ---------------------------------------------------------------------------
def exam_tracker_tab() -> None:
    section_header("Exam tracker", "Upcoming and completed")
    create, records = st.tabs(["➕ Add Exam", "📋 Exam Records"])

    with create:
        section_header("Add exam", "Inputs")
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

        st.divider()
        section_header("Revision order", "Coach")
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
        else:
            note = db.get_context("latest_exam_advice")
            if note:
                with st.container(border=True):
                    st.caption("Latest advice")
                    st.markdown(note)

    with records:
        section_header("Exam records", "List")
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
            empty_state("No exams saved yet", "Add your first one on the left.", "▣")
        else:
            st.caption("Upcoming")
            for row in upcoming:
                cols = st.columns([5, 1])
                with cols[0]:
                    render_exam_card(row, completed=False)
                if cols[1].button("Done", key=f"exam_done_{row['id']}"):
                    db.update_task_status(row["id"], "done")
                    st.rerun()
            if done:
                st.caption("Completed")
                for row in done:
                    render_exam_card(row, completed=True)


# ---------------------------------------------------------------------------
# Quizzes
# ---------------------------------------------------------------------------
def _quiz_results_panel(
    results: list,
    score: int | None,
    missed_topics: str | None = None,
    *,
    show_memory_note: bool = False,
) -> None:
    total = len(results)
    correct = sum(1 for r in results if r.get("correct"))
    missed_label = missed_topics if missed_topics and missed_topics != "none" else "None"
    metric_row(
        [
            ("Score", f"{score}%" if score is not None else "—"),
            ("Correct", f"{correct}/{total}" if total else "—"),
            ("Missed topics", missed_label),
        ]
    )
    for row in results:
        with st.container(border=True):
            mark = "Correct" if row["correct"] else "Missed"
            cls = "quiz-result-ok" if row["correct"] else "quiz-result-miss"
            st.markdown(f'<p class="{cls}">{mark}</p>', unsafe_allow_html=True)
            st.markdown(row.get("question") or "")
            if not row["correct"]:
                st.caption(f"Yours: {row.get('your', '')}")
                st.caption(f"Answer: {row.get('answer', '')}")
    if show_memory_note and missed_topics and missed_topics != "none":
        st.caption(f"Saved to memory: {missed_topics}. Open Planner to adapt the next plan.")


def quiz_generator_tab() -> None:
    section_header("Quiz generator", "Practice MCQs")
    create, records = st.tabs(["🎯 New Quiz", "📈 Past Attempts"])

    with create:
        section_header("New quiz", "Inputs")
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
        if quiz and not st.session_state.get("quiz_submitted"):
            st.divider()
            section_header(f"{quiz['subject']}", quiz["topic"])
            answers = {}
            with st.form("quiz_answers"):
                for i, q in enumerate(quiz["questions"]):
                    options = q.get("options") or []
                    with st.container(border=True):
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
        elif quiz and st.session_state.get("quiz_submitted"):
            st.divider()
            section_header("Results", "This attempt")
            missed = db.get_context("last_quiz_missed_topics")
            _quiz_results_panel(
                st.session_state["quiz_submitted"],
                st.session_state.get("quiz_score"),
                missed,
                show_memory_note=True,
            )
        else:
            empty_state("No quiz in progress", "Choose a subject and topic, then generate questions.", "?")

    with records:
        section_header("Quiz records", "Past attempts")
        past = db.query_tasks("quiz_result", limit=12)
        if not past:
            empty_state("No quizzes yet", "Generate and submit a quiz to see scores here.", "◇")
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
                        _quiz_results_panel(results, int(row["confidence_score"] or 0), missed_txt)
                    else:
                        st.caption(f"{row['subject'] or ''} · {int(row['confidence_score'] or 0)}%")


# ---------------------------------------------------------------------------
# Tutor (chat)
# ---------------------------------------------------------------------------
def tutor_tab() -> None:
    title_col, action_col = st.columns([0.82, 0.18], vertical_alignment="bottom")
    with title_col:
        section_header("Tutor", "Ask Ruia")
    with action_col:
        if st.button("Clear chat", key="clear_chat", help="Delete this chat history"):
            db.clear_chat()
            st.session_state.chat_messages = []
            st.rerun()
    st.caption("Uses your saved plans and quiz misses. Keep questions specific.")
    ensure_chat_state()
    log = st.container()
    with log:
        if not st.session_state.chat_messages:
            empty_state(
                "No messages yet",
                "Try: explain a missed quiz topic, or walk through a formula.",
                "💬",
            )
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    handle_chat_input()


def handle_chat_input() -> None:
    prompt = st.chat_input("Ask Ruia a doubt…")
    if not prompt:
        return
    prompt = security.clamp_text(prompt, security.MAX_CHAT)
    if not prompt:
        return
    ensure_chat_state()
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    db.add_chat("user", prompt)
    try:
        with st.spinner("Ruia is thinking…"):
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


# ---------------------------------------------------------------------------
# History + progress (former insights charts live here)
# ---------------------------------------------------------------------------
def history_tab() -> None:
    section_header("History", "Records and progress")
    plans = db.query_tasks("plan_item", limit=200)
    exams = db.query_tasks("exam", limit=200)
    quizzes = db.query_tasks("quiz_result", limit=200)
    quizzes_chrono = list(reversed(quizzes[:40]))

    avg = 0
    if quizzes:
        avg = round(sum(float(q["confidence_score"] or 0) for q in quizzes) / len(quizzes))
    upcoming_n = len([e for e in exams if e["status"] != "done"])
    done_n = len([e for e in exams if e["status"] == "done"])
    metric_row(
        [
            ("Saved plans", str(len(grouped_plan_batches(plans)))),
            ("Quizzes", str(len(quizzes))),
            ("Avg. quiz score", f"{avg}%" if quizzes else "—"),
            ("Exams done", f"{done_n}"),
            ("Upcoming", str(upcoming_n)),
        ]
    )

    st.download_button(
        "Download everything",
        data=export_everything(),
        file_name="ruia-records.md",
        mime="text/markdown",
        key="dl_all",
    )

    st.divider()
    section_header("Progress", "Charts")
    snapshot = analytics.build_dashboard_snapshot(plans, exams, quizzes)
    left, right = st.columns(2, gap="large")
    with left:
        st.caption("Quiz scores")
        if quizzes_chrono:
            df_quizzes = pd.DataFrame([
                {
                    "Quiz": f"{i+1}. {row['subject'] or 'Quiz'}",
                    "Score": float(row["confidence_score"] or 0),
                    "Date": pretty_dt(row["created_at"])
                }
                for i, row in enumerate(quizzes_chrono)
            ])
            chart = alt.Chart(df_quizzes).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Quiz:N", sort=None, title=None),
                y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("Score:Q", scale=alt.Scale(scheme="purples"), legend=None),
                tooltip=["Quiz", "Score", "Date"]
            ).properties(height=240)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("Take a quiz to see your score trend.")

        if snapshot["quiz_scores"]:
            quiz_df = pd.DataFrame(snapshot["quiz_scores"])
            line_chart = alt.Chart(quiz_df).mark_line(point=True, color="#6366F1").encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 100]), title="Score (%)"),
                tooltip=["date:T", "score:Q"]
            ).properties(height=200)
            st.altair_chart(line_chart, use_container_width=True)

        st.caption("Exam confidence")
        if exams:
            df_exams = pd.DataFrame([
                {
                    "Exam": row["subject"] or row["title"] or f"Exam {row['id']}",
                    "Confidence": float(row["confidence_score"] or 0)
                }
                for row in exams
            ])
            chart = alt.Chart(df_exams).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Exam:N", sort=None, title=None),
                y=alt.Y("Confidence:Q", scale=alt.Scale(domain=[0, 10])),
                color=alt.Color("Confidence:Q", scale=alt.Scale(scheme="tealblues"), legend=None),
                tooltip=["Exam", "Confidence"]
            ).properties(height=240)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("Add exams to compare readiness.")

    with right:
        st.caption("Missed topics")
        counts: dict[str, int] = defaultdict(int)
        for row in quizzes:
            details = parse_details(row["details"])
            for topic in dict.fromkeys(details.get("missed") or []):
                if topic and topic != "none":
                    counts[str(topic)] += 1
        if counts:
            df_counts = pd.DataFrame(list(counts.items()), columns=["Topic", "Count"])
            chart = alt.Chart(df_counts).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6).encode(
                x=alt.X("Count:Q", title="Missed Count"),
                y=alt.Y("Topic:N", sort="-x", title=None),
                color=alt.Color("Count:Q", scale=alt.Scale(scheme="reds"), legend=None),
                tooltip=["Topic", "Count"]
            ).properties(height=240)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("Missed quiz topics will appear here.")

        st.caption("Activity mix")
        mix = [
            {"Activity": "Plans", "Count": len(grouped_plan_batches(plans))},
            {"Activity": "Exams", "Count": len(exams)},
            {"Activity": "Quizzes", "Count": len(quizzes)}
        ]
        df_mix = pd.DataFrame(mix)
        if df_mix["Count"].sum() > 0:
            chart = alt.Chart(df_mix).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Activity", type="nominal", scale=alt.Scale(scheme="category10")),
                tooltip=["Activity", "Count"]
            ).properties(height=240)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("No activity logged yet.")

    st.divider()
    section_header("Plans", "Table")
    groups = grouped_plan_batches(plans)
    if not groups:
        empty_state("No saved plans yet", "Generate a plan in Planner.", "▤")
    else:
        plan_rows = []
        for _batch, rows in groups:
            rows_sorted = sorted(rows, key=lambda x: x[0]["id"])
            first, details = rows_sorted[0]
            plan_rows.append(
                {
                    "Focus": details.get("focus") or first["subject"] or "Study plan",
                    "Days": len(rows),
                    "Saved": pretty_dt(first["created_at"]),
                    "Summary": (details.get("summary") or "")[:160],
                }
            )
        st.dataframe(
            pd.DataFrame(plan_rows),
            use_container_width=True,
            hide_index=True,
        )
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

    st.divider()
    section_header("Exams", "Table")
    if not exams:
        empty_state("No exams yet", "Add exams in the Exams workspace.", "▣")
    else:
        st.download_button(
            "Download exams",
            data=exams_markdown(exams),
            file_name="ruia-exams.md",
            mime="text/markdown",
            key="hist_dl_exams",
        )
        exam_df = pd.DataFrame(
            [
                {
                    "Exam": row["title"],
                    "Subject": row["subject"] or "",
                    "Date": pretty_date(row["due_date"]),
                    "Status": row["status"],
                    "Confidence": float(row["confidence_score"] or 0),
                }
                for row in exams
            ]
        )
        st.dataframe(
            exam_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Confidence": st.column_config.ProgressColumn(
                    "Confidence", min_value=0, max_value=10, format="%d/10"
                ),
            },
        )

    st.divider()
    section_header("Quizzes", "Table")
    if not quizzes:
        empty_state("No quizzes yet", "Complete a quiz to see scores here.", "◇")
    else:
        quiz_table = []
        for row in quizzes:
            details = parse_details(row["details"])
            missed = list(dict.fromkeys(details.get("missed") or []))
            quiz_table.append(
                {
                    "Title": row["title"],
                    "Subject": row["subject"] or "",
                    "Score": float(row["confidence_score"] or 0),
                    "Missed": ", ".join(missed) if missed else "—",
                    "Date": pretty_dt(row["created_at"]),
                }
            )
        st.dataframe(
            pd.DataFrame(quiz_table),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d%%"),
            },
        )
        for row in quizzes:
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
                else:
                    missed = list(dict.fromkeys(details.get("missed") or []))
                    missed_txt = ", ".join(missed) if missed else "none"
                    _quiz_results_panel(results, int(row["confidence_score"] or 0), missed_txt)

    st.divider()
    section_header("Chat", "Table")
    messages = db.get_chat(80)
    if not messages:
        empty_state("No chat yet", "Ask a doubt in the Tutor workspace.", "💬")
    else:
        chat_df = pd.DataFrame(
            [
                {
                    "Role": msg["role"],
                    "When": pretty_dt(msg["created_at"]),
                    "Message": msg["content"],
                }
                for msg in messages
            ]
        )
        st.dataframe(chat_df, use_container_width=True, hide_index=True)


def dashboard_tab() -> None:
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            padding: 2rem;
            border-radius: 20px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.4);
        ">
            <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 800;">Welcome back, Scholar! 🎓</h1>
            <p style="color: #E0E7FF; font-size: 1.1rem; margin-top: 0.5rem; margin-bottom: 0;">
                Track your progress, test your skills, and master your subjects with AI-driven prep.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    ctx = db.get_all_context()
    all_tasks = db.query_tasks(limit=200)
    exams = db.query_tasks("exam", limit=10)
    quizzes = db.query_tasks("quiz_result", limit=10)
    
    streak = activity_streak(all_tasks)
    
    # Calculate average score
    avg_score = 0
    if quizzes:
        valid_scores = [float(q["confidence_score"]) for q in quizzes if q.get("confidence_score") is not None]
        if valid_scores:
            avg_score = int(sum(valid_scores) / len(valid_scores))
            
    upcoming = [e for e in exams if e["status"] != "done"]

    # Highlights / Stats row
    c1, c2, c3 = st.columns(3)
    with c1:
        streak_badge = "🌱 Beginner" if streak < 3 else ("🔥 On Fire!" if streak < 7 else "⚡ Unstoppable")
        st.markdown(f"""
        <div class="day-card" style="text-align: center; display: flex; flex-direction: column; justify-content: center; height: 100%;">
            <div style="font-size: 2rem; margin-bottom: 0.2rem;">🔥</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #1E293B;">{streak} Days</div>
            <div style="color: #64748B; font-size: 0.85rem; font-weight: 600;">{streak_badge}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        circular_progress(avg_score, "Avg Quiz Score", color="#10B981" if avg_score >= 70 else "#F59E0B")
    with c3:
        next_exam_text = ctx.get("next_exam") or "No upcoming exams"
        st.markdown(f"""
        <div class="day-card" style="text-align: center; display: flex; flex-direction: column; justify-content: center; height: 100%;">
            <div style="font-size: 2rem; margin-bottom: 0.2rem;">📅</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1E293B;">Next Target</div>
            <div style="color: #64748B; font-size: 0.85rem; margin-top: 4px;">{next_exam_text}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Quick Actions")
    cols = st.columns(4)
    with cols[0]:
        st.button("📅 Plan My Week", use_container_width=True, on_click=go_to_page, args=("Planner",))
    with cols[1]:
        st.button("📝 Manage Exams", use_container_width=True, on_click=go_to_page, args=("Exams",))
    with cols[2]:
        st.button("🎯 Practice Quiz", use_container_width=True, on_click=go_to_page, args=("Quizzes",))
    with cols[3]:
        st.button("💬 Ask AI Tutor", use_container_width=True, on_click=go_to_page, args=("Tutor",))

    st.markdown("---")
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("#### ⏳ Urgent Deadlines")
        if upcoming:
            for ex in upcoming[:3]:
                render_exam_card(ex, completed=False)
        else:
            empty_state("All clear!", "No upcoming exams scheduled.", "🎉")
            
    with col2:
        st.markdown("#### 🧠 Needs Practice")
        weak = ctx.get("weak_topics") or ctx.get("last_quiz_missed_topics")
        if weak and weak != "none":
            st.markdown(f"""
            <div class="day-card" style="border-left: 4px solid #EF4444;">
                <p style="margin: 0; font-size: 0.95rem; font-weight: 600; color: #DC2626;">Focus Areas from Quizzes:</p>
                <p style="margin: 0.5rem 0 0 0; color: #475569;">{weak}</p>
            </div>
            """, unsafe_allow_html=True)
            st.button("Generate a Quiz on These", on_click=go_to_page, args=("Quizzes",), key="quiz_from_dash")
        else:
            empty_state("Mastery Achieved", "No specific weak spots identified yet. Keep it up!", "⭐")


def main() -> None:
    inject_css()
    page = render_sidebar()

    if page != "Dashboard":
        back_to_dashboard("main_top")

    if page == "Dashboard":
        dashboard_tab()
    elif page == "Planner":
        study_planner_tab()
    elif page == "Exams":
        exam_tracker_tab()
    elif page == "Quizzes":
        quiz_generator_tab()
    elif page == "Tutor":
        tutor_tab()
    else:
        history_tab()


main()

