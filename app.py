import streamlit as st
import pandas as pd
from db import DatabaseManager
from enroll import register_student_without_camera, seed_demo_class
import datetime
import time
import re
import html as html_lib
from notifications import run_irregularity_check

st.set_page_config(
    page_title="Campus AI · Attendance",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

    :root {
        --bg: #0d1117;
        --surface: #161b22;
        --surface-hover: #21262d;
        --border: #30363d;
        --text: #c9d1d9;
        --text-strong: #f0f6fc;
        --muted: #8b949e;
        --accent: #58a6ff;
        --success: #3fb950;
        --danger: #f85149;
    }

    html, body, .stApp, .stMarkdown, p, label, input {
        font-family: 'Inter', sans-serif;
    }

    span[data-testid="stIconMaterial"],
    .material-symbols-rounded,
    .material-symbols-outlined,
    .material-icons {
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        line-height: 1 !important;
        font-size: 22px !important;
        font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24;
    }

    .stApp {
        background-color: var(--bg);
        color: var(--text);
    }

    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }

    footer { visibility: hidden; }

    header[data-testid="stHeader"] {
        background-color: var(--bg);
        visibility: visible !important;
        opacity: 1 !important;
    }

    #MainMenu,
    [data-testid="stMainMenu"],
    [data-testid="stToolbar"] {
        visibility: visible !important;
        opacity: 1 !important;
    }

    #MainMenu button,
    [data-testid="stMainMenu"] button,
    [data-testid="stToolbar"] button {
        color: var(--text-strong) !important;
    }

    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: fixed;
        top: 0.7rem;
        left: 0.7rem;
        z-index: 999999;
        color: var(--text-strong) !important;
        background-color: var(--surface) !important;
        border: 1px solid var(--border);
        border-radius: 8px;
    }

    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"] {
        background-color: var(--surface) !important;
        color: var(--text);
    }

    section[data-testid="stSidebar"] {
        background-color: var(--surface) !important;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] .brand-mark {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.4rem;
        padding-bottom: 1.1rem;
        border-bottom: 1px solid var(--border);
    }
    [data-testid="stSidebar"] .brand-logo {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: linear-gradient(145deg, #58a6ff, #1f6feb);
        color: #fff;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
    }
    [data-testid="stSidebar"] .brand-name {
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--text-strong);
        letter-spacing: -0.03em;
        line-height: 1.2;
    }
    [data-testid="stSidebar"] .brand-sub {
        font-size: 0.72rem;
        color: var(--muted);
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] small {
        color: var(--text) !important;
    }

    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: var(--muted) !important;
        border-top: 1px solid var(--border);
        padding-top: 0.85rem;
        margin-top: 1rem;
    }

    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.28rem;
        background: transparent !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 0.58rem 0.75rem !important;
        color: var(--text) !important;
        font-weight: 500;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: var(--surface-hover);
        border-color: var(--border);
    }

    [data-testid="stSidebar"] .stRadio label:has(input:checked) {
        background-color: rgba(88, 166, 255, 0.12);
        border-color: rgba(88, 166, 255, 0.45);
        color: var(--accent) !important;
        font-weight: 600;
    }

    .page-header { margin-bottom: 1.6rem; }
    .eyebrow {
        color: var(--accent);
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    .hero-title {
        color: var(--text-strong);
        font-size: 2rem;
        margin: 0 0 0.4rem 0;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.15;
    }
    .sub-title {
        color: var(--muted);
        font-size: 0.98rem;
        font-weight: 400;
        margin: 0;
        line-height: 1.5;
    }

    .metric-card {
        background: linear-gradient(180deg, #1c2330 0%, var(--surface) 100%);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 22px 20px;
        text-align: left;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }
    .metric-value {
        font-size: 2.4rem;
        font-weight: 800;
        color: var(--text-strong);
        margin: 6px 0 0 0;
        letter-spacing: -0.04em;
        line-height: 1.1;
    }
    .metric-label {
        font-size: 0.72rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }

    .panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 22px 24px;
    }
    .panel-kiosk {
        background: radial-gradient(120% 80% at 50% 0%, rgba(63,185,80,0.12), var(--surface) 55%);
        border: 1px solid #238636;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(63,185,80,0.12);
        color: var(--success);
        border: 1px solid rgba(63,185,80,0.35);
        border-radius: 999px;
        padding: 4px 12px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--success);
        box-shadow: 0 0 0 4px rgba(63,185,80,0.18);
    }
    .panel h3 {
        color: var(--text-strong) !important;
        font-size: 1.15rem !important;
        margin: 0 0 8px 0 !important;
    }
    .panel p { color: var(--muted); margin: 0; line-height: 1.55; }

    .alert-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        border-radius: 10px;
        padding: 16px 18px;
        color: var(--text);
    }
    .alert-card.warn { border-left-color: var(--danger); }
    .irregular-row {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 4px solid var(--danger);
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 8px;
        color: var(--text);
    }

    h2, h3, .stSubheader { color: var(--text-strong) !important; }

    [data-testid="stDataFrame"], .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border);
    }

    .table-wrap {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
        margin: 0.35rem 0 1.25rem 0;
    }
    .data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }
    .data-table thead th {
        background: #21262d;
        color: var(--muted);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        text-align: left;
        padding: 11px 16px;
        border-bottom: 1px solid var(--border);
    }
    .data-table tbody td {
        padding: 13px 16px;
        color: var(--text-strong);
        border-bottom: 1px solid var(--border);
        vertical-align: middle;
    }
    .data-table tbody tr:last-child td { border-bottom: none; }
    .data-table tbody tr:hover td { background: var(--surface-hover); }
    .cell-id {
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        color: var(--accent);
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(88,166,255,0.1);
        padding: 3px 8px;
        border-radius: 6px;
    }
    .cell-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        color: var(--text);
        font-variant-numeric: tabular-nums;
        font-size: 0.86rem;
    }
    .badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 3px 10px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .badge-open {
        background: rgba(88,166,255,0.12);
        color: var(--accent);
        border: 1px solid rgba(88,166,255,0.28);
    }
    .badge-done {
        background: rgba(63,185,80,0.12);
        color: var(--success);
        border: 1px solid rgba(63,185,80,0.28);
    }
    .badge-ok {
        background: rgba(63,185,80,0.12);
        color: var(--success);
        border: 1px solid rgba(63,185,80,0.28);
    }
    .badge-low {
        background: rgba(248,81,73,0.12);
        color: var(--danger);
        border: 1px solid rgba(248,81,73,0.28);
    }
    .empty-table {
        padding: 32px 16px;
        text-align: center;
        color: var(--muted);
        font-size: 0.92rem;
    }
    .section-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
        margin: 1.4rem 0 0.65rem 0;
    }
    .section-row h3 {
        margin: 0 !important;
        font-size: 1.1rem !important;
        color: var(--text-strong) !important;
    }
    .count-chip {
        color: var(--muted);
        font-size: 0.75rem;
        font-weight: 600;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 3px 10px;
    }

    .status-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 0 0 1.35rem 0;
    }
    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 8px 14px;
        font-size: 0.82rem;
        color: var(--text);
        font-weight: 600;
    }
    .status-chip .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .status-chip.online .dot {
        background: var(--success);
        box-shadow: 0 0 0 4px rgba(63,185,80,0.18);
    }
    .status-chip.offline .dot {
        background: var(--danger);
        box-shadow: 0 0 0 4px rgba(248,81,73,0.18);
    }
    .status-chip .chip-label {
        color: var(--muted);
        font-weight: 600;
        font-size: 0.68rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-right: 2px;
    }

    .feed {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 6px 0;
        margin: 0 0 1.2rem 0;
    }
    .feed-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 16px;
        border-bottom: 1px solid var(--border);
    }
    .feed-item:last-child { border-bottom: none; }
    .feed-action {
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        border-radius: 6px;
        padding: 3px 8px;
        min-width: 42px;
        text-align: center;
    }
    .feed-action.in {
        background: rgba(63,185,80,0.12);
        color: var(--success);
        border: 1px solid rgba(63,185,80,0.3);
    }
    .feed-action.out {
        background: rgba(88,166,255,0.12);
        color: var(--accent);
        border: 1px solid rgba(88,166,255,0.3);
    }
    .feed-name { color: var(--text-strong); font-weight: 600; flex: 1; }
    .feed-meta { color: var(--muted); font-size: 0.8rem; font-variant-numeric: tabular-nums; }
    .feed-item.fresh {
        animation: row-flash 2.4s ease;
    }

    .checkin-toast {
        position: fixed !important;
        right: 28px;
        bottom: 28px;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 260px;
        max-width: 360px;
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #3fb950;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.45);
        animation: toast-in-out 4.2s ease forwards;
        pointer-events: none;
    }
    .checkin-toast.out {
        border-left-color: #58a6ff;
    }
    .checkin-toast .toast-title {
        color: #f0f6fc;
        font-weight: 700;
        font-size: 0.95rem;
        margin: 0;
    }
    .checkin-toast .toast-sub {
        color: #8b949e;
        font-size: 0.78rem;
        margin: 2px 0 0 0;
    }

    @keyframes toast-in-out {
        0% { opacity: 0; transform: translateY(18px) scale(0.98); }
        10% { opacity: 1; transform: translateY(0) scale(1); }
        78% { opacity: 1; transform: translateY(0) scale(1); }
        100% { opacity: 0; transform: translateY(8px) scale(0.98); visibility: hidden; }
    }
    @keyframes row-flash {
        0% { background: rgba(63,185,80,0.16); }
        100% { background: transparent; }
    }

    .report-letterhead {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 22px 24px 18px 24px;
        margin-bottom: 1.4rem;
        border-top: 3px solid var(--accent);
    }
    .report-school {
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--text-strong);
        letter-spacing: -0.03em;
        margin: 0 0 4px 0;
    }
    .report-doc {
        color: var(--accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .report-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 22px;
        color: var(--muted);
        font-size: 0.86rem;
    }
    .report-meta b { color: var(--text); font-weight: 600; }

    @media print {
        header, footer, #MainMenu, [data-testid="stSidebar"],
        [data-testid="stToolbar"], [data-testid="stMainMenu"],
        .stButton, .stDownloadButton, .stRadio {
            display: none !important;
        }
        .stApp, .block-container {
            background: #fff !important;
            color: #111 !important;
            max-width: 100% !important;
        }
        .report-letterhead {
            background: #fff !important;
            border: none !important;
            border-bottom: 2px solid #111 !important;
            border-radius: 0 !important;
            border-top: none !important;
        }
        .report-school, .hero-title, h3 { color: #111 !important; }
        .report-doc { color: #333 !important; }
        .data-table thead th { background: #eee !important; color: #333 !important; }
        .table-wrap { border-color: #ccc !important; }
    }

    .stButton>button, .stDownloadButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.62rem 1.1rem !important;
        border: 1px solid var(--border) !important;
        background: var(--surface-hover) !important;
        color: var(--text-strong) !important;
        transition: all 0.15s ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }
    .stButton>button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(180deg, #58a6ff, #1f6feb) !important;
        color: #fff !important;
        border: 1px solid #1f6feb !important;
        box-shadow: 0 6px 16px rgba(31,111,235,0.28);
    }
    .stButton>button[kind="primary"]:hover {
        filter: brightness(1.06);
        color: #fff !important;
    }

    .stTextInput input, .stSelectbox [data-baseweb="select"] > div,
    [data-baseweb="input"] {
        background-color: #0d1117 !important;
        color: var(--text-strong) !important;
        border-color: var(--border) !important;
        border-radius: 8px !important;
    }
    .stSelectbox label, .stTextInput label {
        color: var(--muted) !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.02em;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: transparent;
        border-bottom: 1px solid var(--border);
    }
    div[data-testid="stTabs"] [data-baseweb="tab"],
    div[data-testid="stTabs"] [data-baseweb="tab"] *,
    div[data-testid="stTabs"] button,
    div[data-testid="stTabs"] button *,
    [data-testid="stTab"],
    [data-testid="stTab"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab"]:hover,
    div[data-testid="stTabs"] [data-baseweb="tab"]:hover *,
    div[data-testid="stTabs"] button:hover,
    div[data-testid="stTabs"] button:hover *,
    [data-testid="stTab"]:hover,
    [data-testid="stTab"]:hover * {
        color: #f85149 !important;
        fill: #f85149 !important;
    }
    div[data-testid="stTabs"] [aria-selected="true"],
    div[data-testid="stTabs"] [aria-selected="true"] *,
    [data-testid="stTab"][aria-selected="true"],
    [data-testid="stTab"][aria-selected="true"] * {
        color: #58a6ff !important;
        fill: #58a6ff !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #58a6ff !important;
    }

    div[data-testid="stAlert"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text) !important;
    }

    hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

db_manager = DatabaseManager()


def page_header(eyebrow, title, subtitle):
    st.markdown(
        f"""
        <div class="page-header">
            <div class="eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}</div>
            <p class="sub-title">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _format_cell(col, val):
    raw = "" if val is None or (isinstance(val, float) and pd.isna(val)) else val
    text = html_lib.escape(str(raw))
    if col in ("ID", "Student ID"):
        return f'<span class="cell-id">{text}</span>'
    if col == "Time In":
        return f'<span class="cell-mono">{text}</span>'
    if col == "Time Out":
        if str(raw).strip() in ("-", "", "None", "nan"):
            return '<span class="badge badge-open">On campus</span>'
        return f'<span class="badge badge-done">{text}</span>'
    if col == "Attendance %":
        try:
            num = float(raw)
        except (TypeError, ValueError):
            num = 0
        cls = "badge-ok" if num >= 75 else "badge-low"
        return f'<span class="badge {cls}">{num:g}%</span>'
    if col in ("Days Present", "Days Absent"):
        return f'<span class="cell-mono">{text}</span>'
    if col == "Status":
        low = str(raw).strip().lower()
        if low in ("on campus", "present"):
            return '<span class="badge badge-ok">Present</span>' if low == "present" else '<span class="badge badge-open">On campus</span>'
        if low in ("checked out", "left"):
            return '<span class="badge badge-done">Checked out</span>'
        if low == "absent":
            return '<span class="badge badge-low">Absent</span>'
        return text
    return text


def render_table(df, empty_message="No records yet."):
    if df is None or df.empty:
        st.markdown(
            f'<div class="table-wrap"><div class="empty-table">{html_lib.escape(empty_message)}</div></div>',
            unsafe_allow_html=True,
        )
        return
    headers = list(df.columns)
    thead = "".join(f"<th>{html_lib.escape(str(h))}</th>" for h in headers)
    body = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{_format_cell(col, row[col])}</td>" for col in headers)
        body.append(f"<tr>{cells}</tr>")
    st.markdown(
        f"""
        <div class="table-wrap">
            <table class="data-table">
                <thead><tr>{thead}</tr></thead>
                <tbody>{''.join(body)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def filter_table(df, query, columns):
    if df is None or df.empty:
        return df
    q = (query or "").strip().lower()
    if not q:
        return df
    mask = False
    for col in columns:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.lower().str.contains(q, na=False, regex=False)
    return df[mask]


def relative_checkin_label(logs):
    best = None
    best_dt = None
    for log in logs or []:
        date = log.get("date") or today_str
        stamp = log.get("out_time") if log.get("out_time") not in (None, "-", "") else log.get("in_time")
        if not stamp or stamp == "-":
            continue
        try:
            dt = datetime.datetime.strptime(f"{date} {stamp}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if best_dt is None or dt > best_dt:
            best_dt = dt
            best = log
    if not best or not best_dt:
        return "No check-ins yet"
    student = db_manager.get_student_by_id(best.get("student_id"))
    name = student["name"] if student else best.get("student_id")
    delta = datetime.datetime.now() - best_dt
    secs = max(0, int(delta.total_seconds()))
    if secs < 60:
        ago = "just now"
    elif secs < 3600:
        mins = secs // 60
        ago = f"{mins} min ago"
    elif secs < 86400:
        hrs = secs // 3600
        ago = f"{hrs} hr ago"
    else:
        days = secs // 86400
        ago = f"{days}d ago"
    return f"{name} · {ago}"


def detect_scanner():
    try:
        import cv2
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cam.isOpened():
            cam.release()
            cam = cv2.VideoCapture(0)
        online = bool(cam.isOpened())
        if online:
            ret, _ = cam.read()
            online = bool(ret)
        cam.release()
        return online
    except Exception:
        return False


def latest_log_per_student(logs):
    latest = {}
    for log in logs or []:
        sid = log.get("student_id")
        prev = latest.get(sid)
        if prev is None or str(log.get("in_time", "")) >= str(prev.get("in_time", "")):
            latest[sid] = log
    return latest


SCHOOL_NAME = "Campus AI Academy"


def build_activity_feed(limit=10):
    names = {s["student_id"]: s["name"] for s in (db_manager.get_all_students() or [])}
    records = db_manager.get_all_attendance_records() or db_manager.get_attendance_logs() or []
    events = []
    for rec in records:
        sid = rec.get("student_id")
        name = names.get(sid, sid)
        date = rec.get("date", "")
        in_time = rec.get("in_time")
        out_time = rec.get("out_time")
        if in_time and in_time != "-":
            events.append({
                "name": name,
                "action": "IN",
                "time": in_time,
                "date": date,
                "sort_key": f"{date} {in_time}",
            })
        if out_time and out_time not in ("-", "", None):
            events.append({
                "name": name,
                "action": "OUT",
                "time": out_time,
                "date": date,
                "sort_key": f"{date} {out_time}",
            })
    events.sort(key=lambda e: e["sort_key"], reverse=True)
    return events[:limit]


def render_activity_feed(events):
    st.markdown(
        """
        <div class="section-row">
            <h3>Activity feed</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not events:
        st.markdown(
            '<div class="table-wrap"><div class="empty-table">No check-ins yet. Scanner activity will appear here.</div></div>',
            unsafe_allow_html=True,
        )
        return
    items = []
    for i, ev in enumerate(events):
        action = ev.get("action", "IN")
        cls = "in" if action == "IN" else "out"
        t = str(ev.get("time", ""))[:5]
        fresh = " fresh" if i == 0 else ""
        items.append(
            f"""<div class="feed-item{fresh}">
                <span class="feed-action {cls}">{html_lib.escape(action)}</span>
                <span class="feed-name">{html_lib.escape(str(ev.get("name", "")))}</span>
                <span class="feed-meta">{html_lib.escape(t)} · {html_lib.escape(str(ev.get("date", "")))}</span>
            </div>"""
        )
    st.markdown(f'<div class="feed">{"".join(items)}</div>', unsafe_allow_html=True)


def queue_checkin_toast(student_id, msg):
    student = db_manager.get_student_by_id(student_id)
    name = student["name"] if student else student_id
    action = "OUT" if "OUT" in msg.upper() else "IN"
    if "Waiting" in msg or "recently" in msg.lower():
        action = "IN"
    clock = msg.split(" at ")[-1].strip() if " at " in msg else datetime.datetime.now().strftime("%H:%M:%S")
    short = clock[:5] if len(clock) >= 5 else clock
    st.session_state.flash_toast = {"name": name, "action": action, "time": short}


with st.sidebar:
    st.markdown(
        """
        <div class="brand-mark">
            <div class="brand-logo">CA</div>
            <div>
                <div class="brand-name">Campus AI</div>
                <div class="brand-sub">Attendance Manager</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    menu = ["Overview", "Live Attendance", "Student Directory", "AI Training Center", "Reports"]
    choice = st.radio("Navigation", menu, label_visibility="collapsed")
    st.caption("v2.0 · MongoDB · Local")

flash = st.session_state.pop("flash_toast", None)
if flash:
    if isinstance(flash, dict):
        name = html_lib.escape(str(flash.get("name", "")))
        action = html_lib.escape(str(flash.get("action", "IN")))
        clock = html_lib.escape(str(flash.get("time", "")))
        kind = "out" if action == "OUT" else "in"
        label = "Checked out" if action == "OUT" else "Checked in"
    else:
        text = html_lib.escape(str(flash))
        name, action, clock, kind, label = text, "IN", "", "in", "Update"
    st.markdown(
        f"""
        <div class="checkin-toast {kind}">
            <span class="feed-action {kind}">{action}</span>
            <div>
                <p class="toast-title">{name}</p>
                <p class="toast-sub">{label} · {clock}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

today_str = db_manager.get_today_str()
all_students = db_manager.get_all_students() or []
today_logs = db_manager.get_attendance_logs(today_str) or []
latest_today = latest_log_per_student(today_logs)
present_ids = set(latest_today.keys())
total_students = len(all_students)
present_today = len(present_ids)
absent = max(total_students - present_today, 0)

if choice == "Overview":
    page_header("Dashboard", "Overview", "Enrollment and attendance snapshot for today.")

    if "scanner_online" not in st.session_state:
        st.session_state.scanner_online = detect_scanner()
    scanner_online = st.session_state.scanner_online
    last_label = relative_checkin_label(today_logs or db_manager.get_attendance_logs())
    scanner_class = "online" if scanner_online else "offline"
    scanner_text = "Online" if scanner_online else "Offline · no webcam"

    st.markdown(
        f"""
        <div class="status-bar">
            <div class="status-chip">
                <span class="chip-label">Last check-in</span>
                {html_lib.escape(last_label)}
            </div>
            <div class="status-chip {scanner_class}">
                <span class="dot"></span>
                <span class="chip-label">Scanner</span>
                {html_lib.escape(scanner_text)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Total Enrolled</div>
            <div class='metric-value'>{total_students}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Present Today</div>
            <div class='metric-value' style='color: #3fb950;'>{present_today}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Absent Today</div>
            <div class='metric-value' style='color: #f85149;'>{absent}</div>
        </div>
        """, unsafe_allow_html=True)

    render_activity_feed(build_activity_feed(8))

    present_rows = []
    absent_rows = []
    for student in all_students:
        sid = student["student_id"]
        name = student.get("name", "Unknown")
        log = latest_today.get(sid)
        if log:
            status = "On campus" if str(log.get("out_time", "-")).strip() in ("-", "", "None") else "Checked out"
            present_rows.append({
                "ID": sid,
                "Name": name,
                "Time In": log.get("in_time", "-"),
                "Status": status,
            })
        else:
            absent_rows.append({"ID": sid, "Name": name, "Status": "Absent"})

    if absent_rows:
        pcol, acol = st.columns(2)
        with pcol:
            st.markdown(
                f"""
                <div class="section-row">
                    <h3>Present today</h3>
                    <span class="count-chip">{len(present_rows)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_table(pd.DataFrame(present_rows) if present_rows else None, "Nobody has checked in yet.")
        with acol:
            st.markdown(
                f"""
                <div class="section-row">
                    <h3>Absent today</h3>
                    <span class="count-chip">{len(absent_rows)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_table(pd.DataFrame(absent_rows))
    else:
        st.markdown(
            f"""
            <div class="section-row">
                <h3>Present today</h3>
                <span class="count-chip">{len(present_rows)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_table(pd.DataFrame(present_rows) if present_rows else None, "Nobody has checked in yet.")
        
    st.markdown(
        f"""
        <div class="section-row">
            <h3>Today's Attendance Log</h3>
            <span class="count-chip">{len(today_logs)} record{"s" if len(today_logs) != 1 else ""}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    log_query = st.text_input("Search log", placeholder="Name or student ID", key="log_search", label_visibility="collapsed")
    if today_logs:
        for log in today_logs:
            student = db_manager.get_student_by_id(log["student_id"])
            log["Student Name"] = student["name"] if student else "Unknown"

        df = pd.DataFrame(today_logs)
        df = df[["student_id", "Student Name", "in_time", "out_time"]]
        df.columns = ["ID", "Name", "Time In", "Time Out"]
        filtered = filter_table(df, log_query, ["ID", "Name"])
        if filtered is None or filtered.empty:
            render_table(None, "No log rows match that search.")
        else:
            render_table(filtered)
    else:
        render_table(None, "No check-ins today. Use Live Attendance to log a student.")
    # --- Auto irregularity check, runs at most once per day ---
    last_check = db_manager.get_last_check_date("auto_notify")
    if last_check != today_str:
        with st.spinner("Running daily attendance health check..."):
            alert_sent, check_msg, flagged_count = run_irregularity_check(db_manager)
            db_manager.set_last_check_date("auto_notify")
        if alert_sent:
            st.warning(f"Daily check: {check_msg}")
        else:
            st.caption("Daily attendance check completed — no irregularities found.")

elif choice == "Live Attendance":
    page_header("Kiosk", "Live Attendance", "Verify faces at the door, or check in a student from the roster.")

    st.markdown(
        """
        <div class="panel panel-kiosk">
            <div class="status-pill"><span class="status-dot"></span> Scanner ready</div>
            <h3>Biometric check-in</h3>
            <p>Activate the camera. The student should look at the lens until access is granted.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Activate scanner", use_container_width=True, type="primary"):
        st.info("Scanner opened in a separate window. It closes after verification.")
        with st.spinner("Analyzing faces..."):
            try:
                from ml_utils import recognize_faces_and_mark_attendance
                success, msg = recognize_faces_and_mark_attendance()
            except Exception as e:
                success, msg = False, str(e)
        if success:
            st.success(f"Verified: {msg}")
            match = re.search(r"(STU-\d+)", str(msg))
            if match:
                queue_checkin_toast(match.group(1), str(msg))
                st.rerun()
        else:
            st.error(f"Scan failed: {msg}")

    render_activity_feed(build_activity_feed(8))

elif choice == "Student Directory":
    page_header("Roster", "Student Directory", "Enroll profiles and manage the student database. Biometric data is stored in the dataset folder.")
    
    tab1, tab2 = st.tabs(["Enrolled Students", "Register New Profile"])
    
    with tab1:
        # --- re-fetch fresh data every time this tab renders ---
        current_students = db_manager.get_all_students()
        dir_query = st.text_input(
            "Search directory",
            placeholder="Search by name or student ID",
            key="directory_search",
        )
        if current_students:
            df = pd.DataFrame(current_students)
            df = df[["student_id", "name", "registered_at"]]
            df.columns = ["Student ID", "Full Name", "Registration Date"]
            filtered = filter_table(df, dir_query, ["Student ID", "Full Name"])
            if filtered is None or filtered.empty:
                render_table(None, "No students match that search.")
            else:
                render_table(filtered)
        else:
            render_table(None, "No enrollments yet. Register a student or load the demo class.")

    with tab2:
        st.subheader("New Enrollment Profile")

        auto_id = db_manager.generate_student_id()

        # Clear the field BEFORE the widget is created, if flagged
        if st.session_state.get("clear_name_field", False):
            st.session_state.new_student_name = ""
            st.session_state.clear_name_field = False

        c1, c2 = st.columns(2)

        with c1:
            student_id = st.text_input(
                "System ID (Auto-generated)",
                value=auto_id,
                disabled=True
            )

        with c2:
            student_name = st.text_input(
                "Student Full Name",
                key="new_student_name"
            )

        st.markdown(
            "Ensure the student is in a well-lit area and facing the camera before starting the biometric capture."
        )

        # Only one button
        capture_clicked = st.button(
            "Capture Biometrics",
            type="primary",
            use_container_width=True
        )

        if capture_clicked:
            if student_name:
                st.info(
                    "Camera initializing... Please instruct the student to look at the camera."
                )

                with st.spinner("Capturing and processing 100 face vectors..."):
                    try:
                        from utils import capture_images
                        success, msg = capture_images(
                            student_id,
                            student_name
                        )
                    except Exception as e:
                        success, msg = False, str(e)

                if success:
                    st.success(
                        f"{student_name} successfully enrolled with ID: {student_id}"
                    )

                    # Allow user to read the success message
                    time.sleep(2)

                    # Clear name field
                    st.session_state.clear_name_field = True
                    st.rerun()

                else:
                    st.error(f"Capture failed: {msg}")

            else:
                st.warning(
                    "Please provide a name for the student profile."
                )

elif choice == "AI Training Center":
    page_header("Model", "AI Training Center", "Rebuild the classifier after new enrollments.")

    st.markdown(
        """
        <div class="alert-card">
            <b>When to train</b><br>
            Retrain after each new student. Training reads face images from the dataset folder and writes the model to disk.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    
    if total_students < 2:
        st.error(f"Insufficient Data: The model requires at least 2 distinct student profiles to train. Currently enrolled: {total_students}")
    else:
        st.success(f"System Ready: {total_students} profiles available for compilation.")
        
        if st.button("Initialize Training Pipeline", type="primary"):
            with st.spinner("Training Neural Network... This may take a few moments depending on dataset size."):
                try:
                    from ml_utils import train_model
                    success, msg = train_model()
                except Exception as e:
                    success, msg = False, str(e)
                
                if success:
                    st.success(f"SUCCESS: {msg}")
                else:
                    st.error(f"ERROR: {msg}")

elif choice == "Reports":
    page_header("Analytics", "Attendance Reports", "Presence rates, students at risk, and daily trend.")

    dates = db_manager.get_distinct_attendance_dates()
    if dates:
        range_label = dates[0] if len(dates) == 1 else f"{dates[0]}  —  {dates[-1]}"
    else:
        range_label = today_str
    generated_at = datetime.datetime.now(db_manager.tz).strftime("%d %b %Y, %I:%M %p PKT")

    st.markdown(
        f"""
        <div class="report-letterhead">
            <div class="report-doc">Official attendance report</div>
            <div class="report-school">{html_lib.escape(SCHOOL_NAME)}</div>
            <div class="report-meta">
                <span><b>Date range</b> {html_lib.escape(range_label)}</span>
                <span><b>Generated</b> {html_lib.escape(generated_at)}</span>
                <span><b>Students</b> {total_students}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Print-friendly: use the browser menu → Print (Ctrl+P) to save as PDF. Sidebar is hidden on print.")

    summary_data = db_manager.get_attendance_summary_per_student()
    trend_data = db_manager.get_daily_attendance_trend()

    if not summary_data:
        st.info("No attendance data recorded yet.")
    else:
        df_summary = pd.DataFrame(summary_data)
        df_summary = df_summary.sort_values("attendance_percentage", ascending=True)
        df_display = df_summary[["student_id", "name", "days_present", "days_absent", "attendance_percentage"]]
        df_display.columns = ["ID", "Name", "Days Present", "Days Absent", "Attendance %"]
        st.markdown(
            f"""
            <div class="section-row">
                <h3>Per-student summary</h3>
                <span class="count-chip">{len(df_display)} students</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_table(df_display)

        # --- CSV export ---
        csv = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Report as CSV",
            data=csv,
            file_name=f"attendance_report_{today_str}.csv",
            mime="text/csv"
        )

        st.divider()

        # --- Most irregular / most absent list ---
        st.subheader("Most Irregular Attendance")
        irregular = df_summary[df_summary["attendance_percentage"] < 75].head(10)
        if not irregular.empty:
            for _, row in irregular.iterrows():
                st.markdown(f"""
                <div class='irregular-row'>
                    <b>{row['name']}</b> ({row['student_id']}) —
                    <span style='color: #f85149; font-weight: 700;'>{row['attendance_percentage']}%</span>
                    <span style='color: #8b949e;'> · {row['days_present']}/{row['total_days'] if 'total_days' in row else row['days_present'] + row['days_absent']} days present</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No students below 75% attendance.")

        st.divider()

        # --- Trend chart ---
        st.subheader("Daily Attendance Trend")
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            df_trend["date"] = pd.to_datetime(df_trend["date"])
            df_trend = df_trend.set_index("date")
            st.line_chart(df_trend["present_count"])
        else:
            st.info("Not enough data yet for a trend chart.")

        st.divider()
        st.subheader("Send Manual Alert Check")
        st.caption("Manually trigger the irregularity check and email the admin if any students are flagged.")

        if st.button("Run Irregularity Check & Notify", type="primary"):
            with st.spinner("Checking attendance patterns and sending alerts if needed..."):
                alert_sent, check_msg, flagged_count = run_irregularity_check(db_manager)

            if alert_sent:
                st.success(check_msg)
            else:
                st.info(check_msg)