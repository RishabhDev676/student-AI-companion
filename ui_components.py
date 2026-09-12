"""Shared Streamlit UI helpers — presentation only, no data or AI logic."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import streamlit as st

import security

# Premium dark-vibrant design — max colour impact via CSS injection
APP_CSS = """
<style>
  @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=block");

  /* ─── TOKENS ─────────────────────────────────────────────────── */
  :root {
    --bg:        #0D0F1A;
    --bg2:       #12152A;
    --surface:   #181C34;
    --surface2:  #1E2340;
    --border:    #2A2F52;
    --border2:   #353B62;

    --violet:    #7C3AED;
    --indigo:    #4F46E5;
    --cyan:      #06B6D4;
    --emerald:   #10B981;
    --amber:     #F59E0B;
    --rose:      #F43F5E;
    --pink:      #EC4899;

    --grad-main: linear-gradient(135deg, #7C3AED 0%, #4F46E5 50%, #06B6D4 100%);
    --grad-card: linear-gradient(135deg, #1E2340 0%, #23294A 100%);
    --grad-ok:   linear-gradient(135deg, #10B981, #059669);
    --grad-warn: linear-gradient(135deg, #F59E0B, #D97706);
    --grad-low:  linear-gradient(135deg, #F43F5E, #E11D48);

    --text-primary:   #F1F5F9;
    --text-secondary: #94A3B8;
    --text-muted:     #64748B;

    --radius-sm:  10px;
    --radius-md:  14px;
    --radius-lg:  20px;
    --radius-xl:  28px;

    --shadow-glow-violet: 0 0 30px rgba(124,58,237,0.25);
    --shadow-glow-cyan:   0 0 30px rgba(6,182,212,0.25);
    --shadow-card: 0 4px 24px rgba(0,0,0,0.4), 0 1px 4px rgba(0,0,0,0.3);
    --shadow-hover: 0 12px 40px rgba(0,0,0,0.5), 0 4px 12px rgba(0,0,0,0.4);
  }

  /* ─── GLOBAL TYPOGRAPHY ──────────────────────────────────────── */
  html, body, [data-testid="stAppViewContainer"], .stApp, .stMarkdown,
  p, h1, h2, h3, h4, h5, h6, input, textarea, select {
    font-family: "Inter", "Space Grotesk", ui-sans-serif, system-ui, sans-serif !important;
    -webkit-font-smoothing: antialiased;
  }

  /* ─── MATERIAL ICONS (CRITICAL: preserve icon font against overrides) ── */
  [data-testid="stIconMaterial"],
  .material-symbols-rounded,
  [translate="no"],
  span:has(> [data-testid="stIconMaterial"]),
  i.material-icons {
    font-family: "Material Symbols Rounded", sans-serif !important;
    font-weight: normal !important;
    font-style: normal !important;
    font-size: 1.25rem !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-block !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-smoothing: antialiased !important;
    vertical-align: middle !important;
  }

  .stApp {
    background: var(--bg) !important;
    background-image:
      radial-gradient(ellipse 80% 50% at 20% -10%, rgba(124,58,237,0.12) 0%, transparent 60%),
      radial-gradient(ellipse 60% 40% at 80% 110%, rgba(6,182,212,0.08) 0%, transparent 60%),
      radial-gradient(ellipse 40% 60% at 50% 50%, rgba(79,70,229,0.04) 0%, transparent 70%) !important;
    color: var(--text-primary) !important;
    min-height: 100vh;
  }

  /* ─── HEADER & TOOLBAR ───────────────────────────────────────── */
  [data-testid="stHeader"] {
    background: transparent !important;
    z-index: 100 !important;
  }
  [data-testid="stToolbar"] {
    background: transparent !important;
    visibility: visible !important;
  }
  .stAppDeployButton,
  #MainMenu,
  [data-testid="stToolbarActions"],
  [data-testid="stDecoration"] {
    display: none !important;
  }
  footer { visibility: hidden; }

  /* Sidebar toggle buttons (expand & collapse) */
  [data-testid="stSidebarCollapseButton"],
  [data-testid="stExpandSidebarButton"] {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
  }
  [data-testid="stSidebarCollapseButton"] button,
  [data-testid="stExpandSidebarButton"] button {
    background: #1E2340 !important;
    color: #F1F5F9 !important;
    border: 1px solid #353B62 !important;
    border-radius: 8px !important;
    width: 2rem !important;
    height: 2rem !important;
    min-width: 2rem !important;
    min-height: 2rem !important;
    padding: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3) !important;
    transition: all 0.2s ease !important;
  }
  [data-testid="stSidebarCollapseButton"] button:hover,
  [data-testid="stExpandSidebarButton"] button:hover {
    background: #7C3AED !important;
    border-color: #7C3AED !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 16px rgba(124, 58, 237, 0.5) !important;
    transform: scale(1.05) !important;
  }
  [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
  [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded", sans-serif !important;
    font-size: 1.25rem !important;
    color: #C4B5FD !important;
  }
  [data-testid="stSidebarCollapseButton"] button:hover [data-testid="stIconMaterial"],
  [data-testid="stExpandSidebarButton"] button:hover [data-testid="stIconMaterial"] {
    color: #FFFFFF !important;
  }

  .block-container {
    padding: 2rem 2.5rem 5rem !important;
    max-width: 1280px !important;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg2); }
  ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 99px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--violet); }

  /* ─── SIDEBAR ────────────────────────────────────────────────── */
  [data-testid="stSidebar"],
  [data-testid="stSidebarContent"] {
    background: #12152A !important;
    color: var(--text-primary) !important;
  }
  [data-testid="stSidebar"] {
    border-right: 1px solid var(--border) !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.4) !important;
  }
  [data-testid="stSidebarUserContent"] {
    padding-top: 1.25rem !important;
    padding-bottom: 2rem !important;
  }

  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--text-secondary) !important;
  }

  /* Sidebar nav pills */
  [data-testid="stSidebar"] [data-testid="stRadio"] > label { display: none !important; }
  [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
    gap: 0.35rem;
    display: flex;
    flex-direction: column;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioOption"] {
    margin-bottom: 0.1rem;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: transparent !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.65rem 0.9rem !important;
    border: 1px solid transparent !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
    color: var(--text-secondary) !important;
    display: flex !important;
    align-items: center !important;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label p,
  [data-testid="stSidebar"] [data-testid="stRadio"] label span {
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(124,58,237,0.14) !important;
    border-color: rgba(124,58,237,0.3) !important;
    transform: translateX(4px) !important;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:hover p,
  [data-testid="stSidebar"] [data-testid="stRadio"] label:hover span {
    color: #FFFFFF !important;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, rgba(124,58,237,0.25), rgba(79,70,229,0.2)) !important;
    border-color: rgba(124,58,237,0.55) !important;
    box-shadow: 0 0 16px rgba(124,58,237,0.25), inset 0 0 0 1px rgba(124,58,237,0.25) !important;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p,
  [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) span {
    color: #C4B5FD !important;
    font-weight: 800 !important;
  }

  /* Sidebar divider */
  [data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
    margin: 1rem 0 !important;
  }

  /* ─── TYPOGRAPHY ─────────────────────────────────────────────── */
  h1, h2, h3 {
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    color: var(--text-primary) !important;
  }
  h4, h5, h6 { color: var(--text-primary) !important; }
  p { color: var(--text-secondary) !important; }
  .stMarkdown p { color: var(--text-secondary) !important; }

  /* ─── ANIMATIONS ─────────────────────────────────────────────── */
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes glow-pulse {
    0%, 100% { box-shadow: 0 0 16px rgba(124,58,237,0.3); }
    50%       { box-shadow: 0 0 32px rgba(124,58,237,0.6); }
  }
  @keyframes shimmer {
    from { background-position: -200% center; }
    to   { background-position: 200% center; }
  }
  @keyframes border-spin {
    to { --angle: 360deg; }
  }

  /* ─── FORMS ──────────────────────────────────────────────────── */
  div[data-testid="stForm"] {
    background: var(--grad-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.4rem 1.4rem 0.8rem !important;
    box-shadow: var(--shadow-card) !important;
    transition: border-color 0.3s, box-shadow 0.3s !important;
    animation: fadeUp 0.4s ease-out forwards !important;
  }
  div[data-testid="stForm"]:hover {
    border-color: var(--border2) !important;
    box-shadow: var(--shadow-hover) !important;
  }

  /* Inputs */
  [data-testid="stTextInput"] input,
  [data-testid="stTextArea"] textarea,
  [data-testid="stNumberInput"] input,
  [data-testid="stDateInput"] input {
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
  }
  [data-testid="stTextInput"] input:focus,
  [data-testid="stTextArea"] textarea:focus,
  [data-testid="stNumberInput"] input:focus,
  [data-testid="stDateInput"] input:focus {
    border-color: var(--violet) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.25), var(--shadow-glow-violet) !important;
    background: var(--surface2) !important;
  }
  [data-testid="stTextInput"] label,
  [data-testid="stTextArea"] label,
  [data-testid="stNumberInput"] label,
  [data-testid="stDateInput"] label,
  [data-testid="stSelectbox"] label {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
  }
  [data-testid="stSelectbox"] [data-testid="stSelectboxContainer"] {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
  }

  /* Slider */
  [data-testid="stSlider"] [data-testid="stThumbValue"] { color: var(--text-primary) !important; }
  [data-testid="stSlider"] [role="slider"] {
    background: var(--violet) !important;
    box-shadow: 0 0 12px rgba(124,58,237,0.5) !important;
  }
  [data-testid="stSlider"] [data-baseweb="slider"] div[role="progressbar"] {
    background: var(--grad-main) !important;
  }

  /* ─── BUTTONS ────────────────────────────────────────────────── */
  /* Primary (form submit) */
  div[data-testid="stFormSubmitButton"] button {
    background: var(--grad-main) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.4), 0 0 0 0 rgba(124,58,237,0) !important;
    transition: all 0.25s ease !important;
  }
  div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(124,58,237,0.6), 0 0 40px rgba(124,58,237,0.25) !important;
    filter: brightness(1.1) !important;
  }
  div[data-testid="stFormSubmitButton"] button:active {
    transform: translateY(0) !important;
  }

  /* Regular buttons */
  .stButton > button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
  }
  .stButton > button:hover {
    background: var(--surface2) !important;
    border-color: var(--violet) !important;
    color: #C4B5FD !important;
    box-shadow: 0 0 16px rgba(124,58,237,0.2) !important;
    transform: translateY(-1px) !important;
  }

  /* Download buttons */
  [data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, rgba(6,182,212,0.15), rgba(79,70,229,0.15)) !important;
    border: 1px solid rgba(6,182,212,0.4) !important;
    color: #67E8F9 !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
  }
  [data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(135deg, rgba(6,182,212,0.25), rgba(79,70,229,0.25)) !important;
    box-shadow: var(--shadow-glow-cyan) !important;
    transform: translateY(-1px) !important;
  }

  /* ─── TABS ────────────────────────────────────────────────────── */
  [data-testid="stTabs"] [role="tablist"] {
    background: var(--surface) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    padding: 4px !important;
    gap: 4px !important;
    margin-bottom: 1.5rem !important;
  }
  [data-testid="stTabs"] button[role="tab"] {
    border-radius: var(--radius-sm) !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    padding: 0.5rem 1rem !important;
  }
  [data-testid="stTabs"] button[role="tab"]:hover {
    color: var(--text-secondary) !important;
    background: var(--surface2) !important;
  }
  [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: var(--grad-main) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 16px rgba(124,58,237,0.4) !important;
  }
  [data-testid="stTabs"] [role="tabpanel"] {
    animation: fadeUp 0.3s ease-out forwards !important;
  }
  /* Hide default bottom-border underline on tabs */
  [data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
  [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

  /* ─── EXPANDERS ──────────────────────────────────────────────── */
  [data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    margin-bottom: 0.6rem !important;
    transition: all 0.25s ease !important;
    animation: fadeUp 0.4s ease-out forwards !important;
    box-shadow: var(--shadow-card) !important;
  }
  [data-testid="stExpander"]:hover {
    border-color: var(--border2) !important;
    box-shadow: var(--shadow-hover) !important;
  }
  [data-testid="stExpander"] summary {
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
  }
  [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded", sans-serif !important;
    font-size: 1.25rem !important;
    color: var(--violet) !important;
  }

  /* ─── METRICS ────────────────────────────────────────────────── */
  div[data-testid="stMetric"] {
    background: var(--grad-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.2rem 1.4rem !important;
    box-shadow: var(--shadow-card) !important;
    transition: all 0.25s ease !important;
    animation: fadeUp 0.4s ease-out forwards !important;
    position: relative !important;
    overflow: hidden !important;
  }
  div[data-testid="stMetric"]::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--grad-main);
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }
  div[data-testid="stMetric"]:hover {
    transform: translateY(-4px) !important;
    box-shadow: var(--shadow-hover), 0 0 30px rgba(124,58,237,0.1) !important;
    border-color: var(--violet) !important;
  }
  [data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.8rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.1em; }
  [data-testid="stMetricValue"] { color: var(--text-primary) !important; font-weight: 800 !important; }
  [data-testid="stMetricDelta"] { font-weight: 600 !important; }

  /* ─── DATA TABLE ─────────────────────────────────────────────── */
  [data-testid="stDataFrame"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-card) !important;
    overflow: hidden !important;
  }

  /* ─── PROGRESS BAR ───────────────────────────────────────────── */
  [data-testid="stProgressBar"] > div {
    border-radius: 99px !important;
    background: var(--grad-main) !important;
    box-shadow: 0 0 10px rgba(124,58,237,0.5) !important;
  }
  [data-testid="stProgressBar"] {
    background: var(--surface2) !important;
    border-radius: 99px !important;
  }

  /* ─── CHAT ───────────────────────────────────────────────────── */
  [data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-card) !important;
    animation: fadeUp 0.3s ease-out forwards !important;
  }
  [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-color: rgba(124,58,237,0.35) !important;
    background: linear-gradient(135deg, rgba(124,58,237,0.06), rgba(79,70,229,0.04)) !important;
  }
  [data-testid="stChatInput"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
  }

  /* ─── TOAST ──────────────────────────────────────────────────── */
  [data-testid="stToast"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
  }

  /* ─── SPINNER ────────────────────────────────────────────────── */
  [data-testid="stSpinner"] > div { border-top-color: var(--violet) !important; }

  /* ─── CAPTIONS ───────────────────────────────────────────────── */
  [data-testid="stCaptionContainer"] p,
  .stCaption { color: var(--text-muted) !important; }

  /* ─── INFO / WARNING / ERROR ────────────────────────────────── */
  [data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
  }

  /* ─── DIVIDER ────────────────────────────────────────────────── */
  hr {
    border-color: var(--border) !important;
    margin: 1.75rem 0 !important;
    opacity: 0.6 !important;
  }

  /* ─── BRANDING ───────────────────────────────────────────────── */
  .brand-mark {
    width: 42px; height: 42px;
    border-radius: var(--radius-sm);
    background: var(--grad-main);
    color: #FFFFFF;
    font-weight: 900;
    font-size: 1.25rem;
    display: flex; align-items: center; justify-content: center;
    letter-spacing: -0.04em;
    flex-shrink: 0;
    box-shadow: 0 4px 16px rgba(124,58,237,0.5), 0 0 0 1px rgba(124,58,237,0.3);
    animation: glow-pulse 3s ease-in-out infinite;
  }
  .brand-title {
    font-size: 1.1rem; font-weight: 800; margin: 0;
    color: var(--text-primary) !important;
    letter-spacing: -0.04em;
    background: linear-gradient(90deg, #E2E8F0, #C4B5FD);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .brand-tag {
    font-size: 0.72rem; color: var(--text-muted); margin: 0.05rem 0 0;
    font-weight: 500;
  }

  /* ─── SECTION HEADERS ────────────────────────────────────────── */
  .section-kicker {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    color: var(--violet);
    margin: 0 0 0.4rem;
    font-weight: 700;
  }
  .section-title {
    font-size: 1.2rem; font-weight: 800; margin: 0 0 1rem;
    letter-spacing: -0.03em; color: var(--text-primary);
  }

  /* ─── PILLS ──────────────────────────────────────────────────── */
  .pill {
    display: inline-block;
    font-size: 0.72rem;
    padding: 0.18rem 0.65rem;
    border-radius: 999px;
    background: rgba(124,58,237,0.15);
    color: #C4B5FD;
    margin-right: 0.3rem;
    font-weight: 700;
    border: 1px solid rgba(124,58,237,0.3);
    letter-spacing: 0.02em;
  }
  .pill.ok   { background: rgba(16,185,129,0.15); color: #6EE7B7; border-color: rgba(16,185,129,0.3); }
  .pill.warn { background: rgba(245,158,11,0.15);  color: #FCD34D; border-color: rgba(245,158,11,0.3); }
  .pill.low  { background: rgba(244,63,94,0.15);   color: #FCA5A5; border-color: rgba(244,63,94,0.3); }
  .pill.done { background: rgba(100,116,139,0.15); color: var(--text-muted); border-color: rgba(100,116,139,0.2); }

  /* ─── EMPTY STATES ───────────────────────────────────────────── */
  .empty-state {
    background: var(--surface);
    border: 1px dashed var(--border2);
    border-radius: var(--radius-lg);
    padding: 3rem 2rem;
    text-align: center;
    color: var(--text-muted);
    transition: all 0.25s ease;
  }
  .empty-state:hover {
    border-color: rgba(124,58,237,0.4);
    background: linear-gradient(135deg, rgba(124,58,237,0.05), rgba(79,70,229,0.03));
  }
  .empty-state .empty-icon {
    width: 48px; height: 48px; margin: 0 auto 1rem;
    border-radius: var(--radius-sm);
    background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(79,70,229,0.1));
    color: #C4B5FD;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    border: 1px solid rgba(124,58,237,0.2);
  }
  .empty-state .empty-title { color: var(--text-secondary); font-weight: 700; margin: 0 0 0.4rem; font-size: 1rem; }
  .empty-state .empty-hint  { margin: 0; font-size: 0.88rem; color: var(--text-muted); }

  /* ─── CARDS ──────────────────────────────────────────────────── */
  .day-card, .exam-card, .snap-card {
    background: var(--grad-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.2rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-card);
    transition: all 0.3s ease;
    animation: fadeUp 0.4s ease-out forwards;
    position: relative;
    overflow: hidden;
  }
  .day-card::after, .exam-card::after {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--grad-main);
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  .day-card:hover::after, .exam-card:hover::after { opacity: 1; }
  .day-card:hover, .exam-card:hover, .snap-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-hover), 0 0 40px rgba(124,58,237,0.1);
    border-color: rgba(124,58,237,0.35);
  }
  .day-card { min-height: 220px; }
  .day-top { display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.55rem; }
  .day-num {
    width: 30px; height: 30px;
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(124,58,237,0.3), rgba(79,70,229,0.2));
    color: #C4B5FD;
    font-size: 0.8rem;
    font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    border: 1px solid rgba(124,58,237,0.3);
  }
  .day-card .day-subject { font-size: 1rem; font-weight: 700; margin: 0; line-height: 1.25; color: var(--text-primary); }
  .day-card .day-hours   { font-size: 0.78rem; color: var(--cyan); margin: 0 0 0.6rem; font-weight: 700; }
  .day-card ul { margin: 0; padding-left: 1.2rem; font-size: 0.86rem; color: var(--text-secondary); }
  .day-card li { margin-bottom: 0.3rem; }

  /* Exam Card */
  .exam-card.completed { opacity: 0.5; }
  .exam-card.completed h4 { text-decoration: line-through; color: var(--text-muted); }
  .exam-card h4         { margin: 0 0 0.45rem; font-size: 1.05rem; letter-spacing: -0.02em; color: var(--text-primary); }
  .exam-meta            { font-size: 0.83rem; color: var(--text-muted); margin-bottom: 0.65rem; }
  .conf-track           { height: 8px; background: var(--surface2); border-radius: 99px; overflow: hidden; margin-top: 0.6rem; }
  .conf-fill            { height: 100%; background: var(--grad-main); border-radius: 99px; transition: width 0.6s ease; box-shadow: 0 0 8px rgba(124,58,237,0.4); }
  .conf-fill.warn       { background: var(--grad-warn); box-shadow: 0 0 8px rgba(245,158,11,0.4); }
  .conf-fill.low        { background: var(--grad-low);  box-shadow: 0 0 8px rgba(244,63,94,0.4); }
  .conf-fill.ok         { background: var(--grad-ok);   box-shadow: 0 0 8px rgba(16,185,129,0.4); }
  .conf-caption         { font-size: 0.73rem; color: var(--text-muted); margin-top: 0.35rem; font-weight: 600; }

  /* Quiz Results */
  .quiz-result-ok   { color: #6EE7B7; font-weight: 700; margin: 0 0 0.3rem; font-size: 0.78rem; letter-spacing: 0.06em; text-transform: uppercase; }
  .quiz-result-miss { color: #FCA5A5; font-weight: 700; margin: 0 0 0.3rem; font-size: 0.78rem; letter-spacing: 0.06em; text-transform: uppercase; }

  /* Snapshots */
  .snap-card   { padding: 1rem 1.2rem 0.6rem; }
  .snap-row    { margin-bottom: 0.9rem; }
  .snap-label  { font-size: 0.67rem; text-transform: uppercase; letter-spacing: 0.18em; color: var(--violet); margin-bottom: 0.15rem; font-weight: 700; }
  .snap-value  { font-size: 0.92rem; color: var(--text-primary); line-height: 1.4; font-weight: 500; }

  /* ─── MUTED TEXT ─────────────────────────────────────────────── */
  .muted { color: var(--text-muted) !important; font-size: 0.85rem; }

  /* ─── BRAND ROW ──────────────────────────────────────────────── */
  .brand-row {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.25rem 0.15rem 0.5rem;
  }

  /* ─── PAGE HEADERS ───────────────────────────────────────────── */
  .page-head { margin: 0 0 1.75rem; }
  .page-kicker {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    color: var(--violet);
    margin: 0 0 0.4rem;
    font-weight: 700;
  }
  .page-title {
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: -0.05em;
    margin: 0;
    line-height: 1.15;
    background: linear-gradient(90deg, #E2E8F0 0%, #C4B5FD 50%, #67E8F9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .page-sub {
    color: var(--text-muted);
    font-size: 1rem;
    margin: 0.5rem 0 0;
    font-weight: 500;
  }

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
