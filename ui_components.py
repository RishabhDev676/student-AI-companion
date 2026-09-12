"""Shared Streamlit UI helpers — presentation only, no data or AI logic."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import streamlit as st

import security

# Modern Glassmorphism + Plus Jakarta Sans. Smooth gradients, soft shadows, rounded corners, and animations.
APP_CSS = """
<style>
  @import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");

  html, body, [data-testid="stAppViewContainer"], .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6 {
    font-family: "Plus Jakarta Sans", ui-sans-serif, system-ui, sans-serif !important;
  }

  /* Global background with a subtle ambient gradient */
  .stApp { 
    background: #F8FAFC;
    background-image: 
      radial-gradient(at 0% 0%, hsla(253,16%,7%,0.03) 0, transparent 50%), 
      radial-gradient(at 50% 0%, hsla(225,39%,30%,0.03) 0, transparent 50%), 
      radial-gradient(at 100% 0%, hsla(339,49%,30%,0.03) 0, transparent 50%);
    color: #0F172A;
  }
  
  [data-testid="stHeader"] { background: transparent; }
  .stAppDeployButton, [data-testid="stToolbar"], #MainMenu { display: none !important; }
  footer { visibility: hidden; }

  .block-container {
    padding: 2rem 2.5rem 4rem;
    max-width: 1200px;
  }

  /* Sidebar styling */
  [data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(12px);
    border-right: 1px solid rgba(226, 232, 240, 0.8);
  }
  [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #475569; }

  /* Sidebar navigation */
  [data-testid="stSidebar"] [data-testid="stRadio"] > label { display: none; }
  [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
    gap: 0.3rem;
    display: flex;
    flex-direction: column;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: transparent;
    border-radius: 10px;
    padding: 0.6rem 0.8rem !important;
    border: 1px solid transparent;
    transition: all 0.2s ease;
    cursor: pointer;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(241, 245, 249, 0.8);
    transform: translateX(4px);
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: #FFFFFF;
    border-color: #E2E8F0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
    font-weight: 700;
    color: #6366F1;
  }

  /* Headings */
  h1, h2, h3 { font-weight: 700; letter-spacing: -0.04em; color: #0F172A; }
  
  /* Animations */
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  /* Forms & Inputs */
  div[data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 16px;
    padding: 1.2rem 1.2rem 0.6rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
    transition: box-shadow 0.3s ease;
    animation: fadeUp 0.4s ease-out forwards;
  }
  div[data-testid="stForm"]:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
  }
  [data-testid="stExpander"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    margin-bottom: 0.6rem;
    transition: all 0.2s ease;
    animation: fadeUp 0.4s ease-out forwards;
  }
  [data-testid="stExpander"]:hover {
    border-color: #CBD5E1;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
  }
  div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 1rem 1.2rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
    transition: all 0.2s ease;
    animation: fadeUp 0.4s ease-out forwards;
  }
  div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
  }
  [data-testid="stTextInput"] input,
  [data-testid="stTextArea"] textarea,
  [data-testid="stNumberInput"] input,
  [data-testid="stDateInput"] input {
    background: #F8FAFC !important;
    color: #0F172A !important;
    border-radius: 10px !important;
    border: 1px solid #E2E8F0 !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
  }
  [data-testid="stTextInput"] input:focus,
  [data-testid="stTextArea"] textarea:focus,
  [data-testid="stNumberInput"] input:focus,
  [data-testid="stDateInput"] input:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
  }

  /* Buttons */
  .stButton button, div[data-testid="stFormSubmitButton"] button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    transition: all 0.2s ease !important;
  }
  /* Form Submit Button (Primary Action) */
  div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
  }
  div[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4) !important;
    transform: translateY(-1px);
  }
  /* Regular Buttons */
  .stButton button {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    color: #475569 !important;
  }
  .stButton button:hover {
    border-color: #CBD5E1 !important;
    color: #0F172A !important;
    background: #F8FAFC !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02) !important;
  }

  [data-testid="stProgressBar"] > div { border-radius: 99px; background: linear-gradient(90deg, #6366F1, #8B5CF6); }
  [data-testid="stChatMessage"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  }

  /* Branding */
  .brand-row {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.25rem 0.15rem 0.5rem;
  }
  .brand-mark {
    width: 42px; height: 42px;
    border-radius: 12px;
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
    color: #FFFFFF;
    font-weight: 800;
    font-size: 1.2rem;
    display: flex; align-items: center; justify-content: center;
    letter-spacing: -0.04em;
    flex-shrink: 0;
    box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
  }
  .brand-title { font-size: 1.15rem; font-weight: 800; margin: 0; color: #0F172A; letter-spacing: -0.04em; }
  .brand-tag { font-size: 0.78rem; color: #64748B; margin: 0.1rem 0 0; font-weight: 500;}

  /* Headers */
  .page-head { margin: 0 0 1.5rem; }
  .page-kicker {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: #64748B;
    margin: 0 0 0.4rem;
    font-weight: 600;
  }
  .page-title {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    margin: 0;
    color: #0F172A;
    line-height: 1.2;
    background: linear-gradient(90deg, #0F172A, #334155);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .page-sub { color: #64748B; font-size: 1rem; margin: 0.4rem 0 0; }

  .section-kicker {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: #64748B;
    margin: 0 0 0.5rem;
    font-weight: 600;
  }
  .section-title { font-size: 1.15rem; font-weight: 700; margin: 0 0 0.8rem; letter-spacing: -0.03em; color: #1E293B; }

  .muted { color: #64748B; font-size: 0.85rem; }

  /* Pills */
  .pill {
    display: inline-block;
    font-size: 0.75rem;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    background: #F1F5F9;
    color: #475569;
    margin-right: 0.3rem;
    font-weight: 600;
    border: 1px solid #E2E8F0;
  }
  .pill.ok { background: #ECFDF5; color: #059669; border-color: #D1FAE5; }
  .pill.warn { background: #FFFBEB; color: #D97706; border-color: #FEF3C7; }
  .pill.low { background: #FEF2F2; color: #DC2626; border-color: #FEE2E2; }
  .pill.done { background: #F1F5F9; color: #64748B; border-color: #E2E8F0; }

  /* Empty States */
  .empty-state {
    background: rgba(255, 255, 255, 0.6);
    border: 1px dashed #CBD5E1;
    border-radius: 16px;
    padding: 2.5rem 1.5rem;
    text-align: center;
    color: #64748B;
    transition: all 0.2s ease;
  }
  .empty-state:hover {
    border-color: #94A3B8;
    background: rgba(255, 255, 255, 0.9);
  }
  .empty-state .empty-icon {
    width: 42px; height: 42px; margin: 0 auto 0.7rem;
    border-radius: 12px;
    background: #F1F5F9;
    color: #6366F1;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
  }
  .empty-state .empty-title { color: #0F172A; font-weight: 700; margin: 0 0 0.3rem; }
  .empty-state .empty-hint { margin: 0; font-size: 0.9rem; }

  /* Cards */
  .day-card, .exam-card, .snap-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
    transition: all 0.3s ease;
    animation: fadeUp 0.4s ease-out forwards;
  }
  .day-card:hover, .exam-card:hover, .snap-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 20px -8px rgba(0, 0, 0, 0.1);
    border-color: #CBD5E1;
  }
  .day-card { min-height: 220px; }
  .day-top { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem; }
  .day-num {
    width: 28px; height: 28px;
    border-radius: 8px;
    background: #EEF2FF;
    color: #4F46E5;
    font-size: 0.8rem;
    font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .day-card .day-subject { font-size: 1rem; font-weight: 700; margin: 0; line-height: 1.25; color: #1E293B; }
  .day-card .day-hours { font-size: 0.8rem; color: #6366F1; margin: 0 0 0.6rem; font-weight: 600; }
  .day-card ul { margin: 0; padding-left: 1.2rem; font-size: 0.88rem; color: #475569; }
  .day-card li { margin-bottom: 0.3rem; }

  /* Exam Card */
  .exam-card.completed { opacity: 0.6; background: #F8FAFC; }
  .exam-card.completed h4 { text-decoration: line-through; color: #64748B; }
  .exam-card h4 { margin: 0 0 0.4rem; font-size: 1.05rem; letter-spacing: -0.02em; color: #0F172A; }
  .exam-meta { font-size: 0.85rem; color: #64748B; margin-bottom: 0.65rem; }
  .conf-track { height: 8px; background: #F1F5F9; border-radius: 99px; overflow: hidden; margin-top: 0.5rem;}
  .conf-fill { height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6); border-radius: 99px; transition: width 0.5s ease; }
  .conf-fill.warn { background: linear-gradient(90deg, #F59E0B, #D97706); }
  .conf-fill.low { background: linear-gradient(90deg, #EF4444, #DC2626); }
  .conf-fill.ok { background: linear-gradient(90deg, #10B981, #059669); }
  .conf-caption { font-size: 0.75rem; color: #64748B; margin-top: 0.35rem; font-weight: 500; }

  /* Quiz Results */
  .quiz-result-ok { color: #059669; font-weight: 700; margin: 0 0 0.3rem; font-size: 0.8rem; letter-spacing: 0.05em; text-transform: uppercase; }
  .quiz-result-miss { color: #DC2626; font-weight: 700; margin: 0 0 0.3rem; font-size: 0.8rem; letter-spacing: 0.05em; text-transform: uppercase; }

  /* Snapshots */
  .snap-card { padding: 1rem 1.1rem 0.5rem; }
  .snap-row { margin-bottom: 0.85rem; }
  .snap-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.15em; color: #64748B; margin-bottom: 0.15rem; font-weight: 600; }
  .snap-value { font-size: 0.95rem; color: #0F172A; line-height: 1.4; font-weight: 500; }

  hr { border-color: #E2E8F0 !important; margin: 1.5rem 0 !important; }
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


import requests
from streamlit_lottie import st_lottie

@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def empty_state(title: str, hint: str, icon: str = "○", lottie_url: str = None) -> None:
    if lottie_url:
        lottie_json = load_lottieurl(lottie_url)
        if lottie_json:
            st_lottie(lottie_json, height=160, key=f"lottie_{title.replace(' ', '_')}")
            st.markdown(
                f"<div style='text-align: center;'><p class='empty-title'>{security.escape_html(title)}</p><p class='empty-hint' style='color:#64748B;'>{security.escape_html(hint)}</p></div>", 
                unsafe_allow_html=True
            )
            return

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


def circular_progress(value: int, title: str, color: str = "#6366F1") -> None:
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); transition: transform 0.3s ease; animation: fadeUp 0.4s ease-out forwards;">
      <svg viewBox="0 0 36 36" style="width: 80px; height: 80px; margin: 0 auto;">
        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#E2E8F0" stroke-width="3" />
        <path stroke-dasharray="{value}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" />
        <text x="18" y="20.8" style="font-family: 'Plus Jakarta Sans'; font-size: 8.5px; font-weight: 800; fill: #0F172A;" text-anchor="middle">{value}%</text>
      </svg>
      <p style="font-size: 0.85rem; color: #64748B; font-weight: 700; margin: 8px 0 0; text-transform: uppercase; letter-spacing: 0.05em;">{title}</p>
    </div>
    """, unsafe_allow_html=True)
