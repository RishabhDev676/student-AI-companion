"""Shared Streamlit UI helpers — presentation only, no data or AI logic."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import streamlit as st

import security

# Indigo + warm paper. One accent, hairline borders, no gradients.
APP_CSS = """
<style>
  @import url("https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&display=swap");

  html, body, [data-testid="stAppViewContainer"], .stApp, .stMarkdown, p, h1, h2, h3, h4 {
    font-family: "Source Sans 3", ui-sans-serif, system-ui, sans-serif !important;
  }

  .stApp { color: #1A1D26; background: #F3F4F7; }
  [data-testid="stHeader"] { background: transparent; }
  .stAppDeployButton, [data-testid="stToolbar"], #MainMenu { display: none !important; }
  footer { visibility: hidden; }

  .block-container {
    padding: 1.75rem 2.1rem 3.5rem;
    max-width: 1140px;
  }

  [data-testid="stSidebar"] {
    background: #EBEDF2;
    border-right: 1px solid #DCDFE6;
  }
  [data-testid="stSidebar"] > div:first-child { padding-top: 1.15rem; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #3A3F4D; }

  [data-testid="stSidebar"] [data-testid="stRadio"] > label { display: none; }
  [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
    gap: 0.2rem;
    display: flex;
    flex-direction: column;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: transparent;
    border-radius: 8px;
    padding: 0.48rem 0.7rem !important;
    border: 1px solid transparent;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,0.55);
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: #fff;
    border-color: #DCDFE6;
    box-shadow: 0 1px 2px rgba(26, 29, 38, 0.05);
    font-weight: 600;
  }

  h1, h2, h3 { font-weight: 650; letter-spacing: -0.03em; color: #12151C; }

  div[data-testid="stForm"] {
    background: #fff;
    border: 1px solid #E1E4EB;
    border-radius: 14px;
    padding: 1.05rem 1.1rem 0.4rem;
    box-shadow: 0 1px 2px rgba(26, 29, 38, 0.04);
  }
  [data-testid="stExpander"] {
    background: #fff;
    border: 1px solid #E1E4EB;
    border-radius: 12px;
    margin-bottom: 0.5rem;
  }
  div[data-testid="stMetric"] {
    background: #fff;
    border: 1px solid #E1E4EB;
    border-radius: 12px;
    padding: 0.75rem 0.9rem;
    box-shadow: 0 1px 2px rgba(26, 29, 38, 0.04);
  }
  [data-testid="stTextInput"] input,
  [data-testid="stTextArea"] textarea,
  [data-testid="stNumberInput"] input {
    background: #F7F8FA !important;
    color: #1A1D26 !important;
    border-radius: 8px !important;
  }

  .stButton button, div[data-testid="stFormSubmitButton"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
  }
  div[data-testid="stFormSubmitButton"] button {
    background: #3D4A73 !important;
    color: #fff !important;
    border: none !important;
  }
  div[data-testid="stFormSubmitButton"] button:hover {
    background: #323C60 !important;
  }

  [data-testid="stProgressBar"] > div { border-radius: 99px; }
  [data-testid="stChatMessage"] {
    background: #fff;
    border: 1px solid #E1E4EB;
    border-radius: 12px;
  }

  .brand-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.15rem 0.15rem 0.35rem;
  }
  .brand-mark {
    width: 38px; height: 38px;
    border-radius: 10px;
    background: #3D4A73;
    color: #fff;
    font-weight: 700;
    font-size: 1.02rem;
    display: flex; align-items: center; justify-content: center;
    letter-spacing: -0.04em;
    flex-shrink: 0;
  }
  .brand-title { font-size: 1.08rem; font-weight: 700; margin: 0; color: #12151C; letter-spacing: -0.04em; }
  .brand-tag { font-size: 0.76rem; color: #6B7080; margin: 0.1rem 0 0; }

  .page-head { margin: 0 0 1.15rem; }
  .page-kicker {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: #6B7080;
    margin: 0 0 0.28rem;
  }
  .page-title {
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -0.04em;
    margin: 0;
    color: #12151C;
    line-height: 1.15;
  }
  .page-sub { color: #5C6170; font-size: 0.95rem; margin: 0.35rem 0 0; }

  .section-kicker {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #6B7080;
    margin: 0 0 0.45rem;
  }
  .section-title { font-size: 1.02rem; font-weight: 650; margin: 0 0 0.7rem; letter-spacing: -0.03em; }

  .muted { color: #6B7080; font-size: 0.82rem; }

  .pill {
    display: inline-block;
    font-size: 0.72rem;
    padding: 0.12rem 0.5rem;
    border-radius: 999px;
    background: #EEF0F5;
    color: #3A3F4D;
    margin-right: 0.28rem;
    font-weight: 500;
  }
  .pill.ok { background: #E4F0E8; color: #245A38; }
  .pill.warn { background: #F4EDE0; color: #6A4B12; }
  .pill.low { background: #F3E6E6; color: #6B3030; }
  .pill.done { background: #EEF0F5; color: #6B7080; }

  .empty-state {
    background: #fff;
    border: 1px dashed #CDD1DB;
    border-radius: 14px;
    padding: 1.85rem 1.2rem;
    text-align: center;
    color: #6B7080;
  }
  .empty-state .empty-icon {
    width: 36px; height: 36px; margin: 0 auto 0.55rem;
    border-radius: 10px;
    background: #EEF0F5;
    color: #3D4A73;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
  }
  .empty-state .empty-title { color: #12151C; font-weight: 650; margin: 0 0 0.25rem; }
  .empty-state .empty-hint { margin: 0; font-size: 0.88rem; }

  .day-card, .exam-card, .snap-card {
    background: #fff;
    border: 1px solid #E1E4EB;
    border-radius: 14px;
    padding: 0.9rem 0.95rem;
    margin-bottom: 0.65rem;
    box-shadow: 0 1px 2px rgba(26, 29, 38, 0.04);
  }
  .day-card { min-height: 210px; }
  .day-top { display: flex; align-items: center; gap: 0.55rem; margin-bottom: 0.45rem; }
  .day-num {
    width: 26px; height: 26px;
    border-radius: 7px;
    background: #EEF0F5;
    color: #3D4A73;
    font-size: 0.75rem;
    font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .day-card .day-subject { font-size: 0.96rem; font-weight: 650; margin: 0; line-height: 1.25; }
  .day-card .day-hours { font-size: 0.76rem; color: #3D4A73; margin: 0 0 0.5rem; font-weight: 600; }
  .day-card ul { margin: 0; padding-left: 1.05rem; font-size: 0.84rem; color: #3A3F4D; }
  .day-card li { margin-bottom: 0.22rem; }

  .exam-card.completed { opacity: 0.58; background: #F7F8FA; }
  .exam-card.completed h4 { text-decoration: line-through; }
  .exam-card h4 { margin: 0 0 0.35rem; font-size: 1rem; letter-spacing: -0.02em; }
  .exam-meta { font-size: 0.8rem; color: #6B7080; margin-bottom: 0.55rem; }
  .conf-track { height: 6px; background: #EEF0F5; border-radius: 99px; overflow: hidden; }
  .conf-fill { height: 100%; background: #3D4A73; border-radius: 99px; }
  .conf-fill.warn { background: #C4923A; }
  .conf-fill.low { background: #B45A5A; }
  .conf-fill.ok { background: #3D8A5A; }
  .conf-caption { font-size: 0.72rem; color: #6B7080; margin-top: 0.28rem; }

  .quiz-result-ok { color: #245A38; font-weight: 650; margin: 0 0 0.25rem; font-size: 0.78rem; letter-spacing: 0.04em; text-transform: uppercase; }
  .quiz-result-miss { color: #6B3030; font-weight: 650; margin: 0 0 0.25rem; font-size: 0.78rem; letter-spacing: 0.04em; text-transform: uppercase; }

  .snap-card { padding: 0.85rem 0.9rem 0.35rem; }
  .snap-row { margin-bottom: 0.7rem; }
  .snap-label { font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.12em; color: #6B7080; margin-bottom: 0.12rem; }
  .snap-value { font-size: 0.88rem; color: #12151C; line-height: 1.35; font-weight: 500; }

  hr { margin: 1.1rem 0 !important; }
</style>
"""


def inject_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", kicker: str = "") -> None:
    kicker_html = f'<p class="page-kicker">{security.escape_html(kicker)}</p>' if kicker else ""
    sub_html = f'<p class="page-sub">{security.escape_html(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="page-head">
          {kicker_html}
          <p class="page-title">{security.escape_html(title)}</p>
          {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, kicker: str = "") -> None:
    bits = []
    if kicker:
        bits.append(f'<p class="section-kicker">{security.escape_html(kicker)}</p>')
    bits.append(f'<p class="section-title">{security.escape_html(title)}</p>')
    st.markdown("".join(bits), unsafe_allow_html=True)


def quiet_label(text: str) -> None:
    st.markdown(f'<p class="section-kicker">{security.escape_html(text)}</p>', unsafe_allow_html=True)


def empty_state(title: str, hint: str, icon: str = "○") -> None:
    st.markdown(
        f"""
        <div class="empty-state">
          <div class="empty-icon">{security.escape_html(icon)}</div>
          <p class="empty-title">{security.escape_html(title)}</p>
          <p class="empty-hint">{security.escape_html(hint)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str, kind: str = "") -> str:
    cls = f"pill {kind}".strip()
    return f'<span class="{cls}">{security.escape_html(text)}</span>'


def metric_row(items: list[tuple[str, str]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)


def pretty_dt(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%d %b · %H:%M")
    except ValueError:
        return value[:16]


def pretty_date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        if "T" in value:
            return pretty_dt(value).split(" · ")[0]
        d = date.fromisoformat(value[:10])
        return d.strftime("%d %b %Y")
    except ValueError:
        return value[:10]


def activity_streak(task_rows: list) -> int:
    """Consecutive calendar days (ending today) with any saved task. Uses existing task timestamps only."""
    dates: set[str] = set()
    for row in task_rows:
        created = row["created_at"] if row["created_at"] else ""
        if created:
            dates.add(created[:10])
    if not dates:
        return 0
    cursor = date.today()
    n = 0
    while cursor.isoformat() in dates:
        n += 1
        cursor -= timedelta(days=1)
    return n


def confidence_kind(score: float | None, scale: int = 10) -> str:
    try:
        val = float(score or 0)
    except (TypeError, ValueError):
        val = 0
    ratio = val / scale if scale else 0
    if ratio >= 0.75:
        return "ok"
    if ratio >= 0.45:
        return "warn"
    return "low"


def render_week_grid(days: list, hours_per_day: str | None = None) -> None:
    """One card per plan day: subject (focus) and hours separated from the task list."""
    if not days:
        empty_state("No days in this plan", "Generate a plan to see a weekly layout.", "▦")
        return
    hours_label = f"{hours_per_day}h / day" if hours_per_day else "Focus block"
    for start in range(0, len(days), 4):
        chunk = days[start : start + 4]
        cols = st.columns(len(chunk), gap="small")
        for col, day in zip(cols, chunk):
            tasks = day.get("tasks") or []
            items = "".join(f"<li>{security.escape_html(t)}</li>" for t in tasks) or "<li>No tasks listed</li>"
            day_no = str(day.get("day", "?"))
            with col:
                st.markdown(
                    f"""
                    <div class="day-card">
                      <div class="day-top">
                        <div class="day-num">{security.escape_html(day_no)}</div>
                        <p class="day-subject">{security.escape_html(str(day.get("focus") or "Study"))}</p>
                      </div>
                      <div class="day-hours">{security.escape_html(hours_label)}</div>
                      <ul>{items}</ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_exam_card(row, completed: bool = False) -> None:
    conf = int(row["confidence_score"] or 0)
    kind = "done" if completed else confidence_kind(conf, 10)
    cls = "exam-card completed" if completed else "exam-card"
    due = pretty_date(row["due_date"])
    width = min(max(conf * 10, 0), 100)
    bar = ""
    if not completed:
        bar = (
            f'<div class="conf-track"><div class="conf-fill {kind}" style="width:{width}%"></div></div>'
            f'<div class="conf-caption">Confidence {conf}/10</div>'
        )
    st.markdown(
        f"""
        <div class="{cls}">
          <h4>{security.escape_html(row["title"])}</h4>
          <div class="exam-meta">
            {pill(row["subject"] or "Subject")}
            {pill(f"{conf}/10", kind)}
            {pill("Completed" if completed else due, "done" if completed else "")}
          </div>
          {bar}
        </div>
        """,
        unsafe_allow_html=True,
    )


def snapshot_item(label: str, value: str | None, fallback: str) -> None:
    shown = (value or "").strip()
    if not shown or shown == "none":
        shown = fallback
    if len(shown) > 160:
        shown = shown[:157] + "…"
    st.markdown(
        f"""
        <div class="snap-row">
          <div class="snap-label">{security.escape_html(label)}</div>
          <div class="snap-value">{security.escape_html(shown)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
