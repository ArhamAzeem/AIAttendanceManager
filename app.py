import streamlit as st
import pandas as pd
from db import DatabaseManager
from utils import capture_images
from ml_utils import train_model, recognize_faces_and_mark_attendance
import datetime
import time

st.set_page_config(
    page_title="AI Attendance System",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
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

    .stApp {
        background-color: var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    header[data-testid="stHeader"] {
        background-color: transparent;
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

    [data-testid="stSidebar"] h2 {
        color: var(--accent) !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] small {
        color: var(--text) !important;
    }

    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: var(--muted) !important;
        border-top: 1px solid var(--border);
        padding-top: 0.85rem;
        margin-top: 0.5rem;
    }

    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.35rem;
    }

    [data-testid="stSidebar"] .stRadio label {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 0.55rem 0.7rem !important;
        color: var(--text) !important;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: var(--surface-hover);
        border-color: var(--border);
    }

    [data-testid="stSidebar"] .stRadio label:has(input:checked) {
        background-color: rgba(88, 166, 255, 0.12);
        border-color: var(--accent);
        color: var(--accent) !important;
        font-weight: 600;
    }

    [data-testid="stSidebar"] [data-baseweb="radio"] div:first-child {
        border-color: var(--border) !important;
    }

    h1, h2, h3 {
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .hero-title {
        color: var(--accent);
        font-size: 3.5rem;
        margin-bottom: 0.5rem;
        font-weight: 800;
    }
    .sub-title {
        color: var(--muted);
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: var(--accent);
    }
    .metric-value {
        font-size: 3rem;
        font-weight: 800;
        color: var(--text-strong);
        margin: 10px 0;
    }
    .metric-label {
        font-size: 1rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stDataFrame {
        border-radius: 12px;
        border: 1px solid var(--border);
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
</style>
""", unsafe_allow_html=True)

db_manager = DatabaseManager()

with st.sidebar:
    st.markdown("## Campus AI")
    menu = ["Overview", "Live Attendance", "Student Directory", "AI Training Center", "Reports"]
    choice = st.radio("Navigation", menu, label_visibility="collapsed")
    st.caption("AI Attendance Manager v2.0")

today_str = datetime.datetime.now().strftime("%Y-%m-%d")
all_students = db_manager.get_all_students()
today_logs = db_manager.get_attendance_logs(today_str)
total_students = len(all_students) if all_students else 0
present_today = len(today_logs) if today_logs else 0

if choice == "Overview":
    st.markdown("<div class='hero-title'>Dashboard Overview</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Real-time insights and attendance metrics for today.</div>", unsafe_allow_html=True)
    
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
        absent = total_students - present_today if total_students > 0 else 0
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Absent Today</div>
            <div class='metric-value' style='color: #f85149;'>{absent}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.subheader("Today's Attendance Log")
    
    if today_logs:
        for log in today_logs:
            student = db_manager.get_student_by_id(log["student_id"])
            log["Student Name"] = student["name"] if student else "Unknown"
            
        df = pd.DataFrame(today_logs)
        df = df[["student_id", "Student Name", "in_time", "out_time"]]
        df.columns = ["ID", "Name", "Time In", "Time Out"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No students have been scanned in today. Go to 'Live Attendance' to start scanning.")

elif choice == "Live Attendance":
    st.markdown("<div class='hero-title'>Live Attendance Kiosk</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Start the biometric scanner to log arrivals and departures.</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
        <div style='background: #161b22; padding: 30px; border-radius: 15px; border: 1px solid #3fb950; text-align: center;'>
            <h3 style='color: #3fb950;'>Scanner Ready</h3>
            <p style='color: #8b949e;'>Click below to activate the camera. Look directly into the lens until access is granted.</p>
        </div>
        <br>
        """, unsafe_allow_html=True)
        
        if st.button("ACTIVATE AI SCANNER", use_container_width=True, type="primary"):
            st.info("Scanner started in a secure window. It will automatically close upon verification.")
            with st.spinner("Neural Engine Active... Analyzing faces..."):
                success, msg = recognize_faces_and_mark_attendance()
            
            if success:
                st.success(f"VERIFIED: {msg}")
            else:
                st.error(f"SCAN FAILED: {msg}")

elif choice == "Student Directory":
    st.markdown("<div class='hero-title'>Student Directory</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Manage enrollments and register new biometric profiles.</div>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Enrolled Students", "Register New Profile"])
    
    with tab1:
        # --- re-fetch fresh data every time this tab renders ---
        current_students = db_manager.get_all_students()  # use whatever your actual fetch method is called
        if current_students:
            df = pd.DataFrame(current_students)
            df = df[["student_id", "name", "registered_at"]]
            df.columns = ["Student ID", "Full Name", "Registration Date"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No active enrollments found.")
            
    with tab2:
        st.subheader("New Enrollment Profile")
        auto_id = db_manager.generate_student_id()
        
       # --- clear the field BEFORE the widget is created, if flagged ---
        if st.session_state.get("clear_name_field", False):
            st.session_state.new_student_name = ""
            st.session_state.clear_name_field = False
        # --------------------------------------------------------------
        
        c1, c2 = st.columns(2)
        with c1:
            student_id = st.text_input("System ID (Auto-generated)", value=auto_id, disabled=True)
        with c2:
            student_name = st.text_input("Student Full Name", key="new_student_name")
            
        st.markdown("Important: Before scanning, ensure the student is in a well-lit area and facing the camera.")
        
        if st.button("Capture Biometrics", type="primary"):
            if student_name:
                st.info("Camera initializing... Please instruct the student to look at the camera.")
                with st.spinner("Capturing and processing 100 face vectors..."):
                    success, msg = capture_images(student_id, student_name)
                
                if success:
                    st.success(f"{student_name} successfully enrolled with ID: {student_id}")
                    # --- clear the name field and force a refresh ---
                    time.sleep(2)
                    st.session_state.clear_name_field = True
                    st.rerun()
                else:
                    st.error(f"Capture failed: {msg}")
            else:
                st.warning("Please provide a name for the student profile.")

elif choice == "AI Training Center":
    st.markdown("<div class='hero-title'>AI Training Center</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Compile and optimize the Convolutional Neural Network.</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: #161b22; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff;'>
        <h4>System Status</h4>
        <p>The neural network must be re-trained whenever a new student is registered. 
        Training processes all collected face vectors into a highly optimized classification model.</p>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    if total_students < 2:
        st.error(f"Insufficient Data: The model requires at least 2 distinct student profiles to train. Currently enrolled: {total_students}")
    else:
        st.success(f"System Ready: {total_students} profiles available for compilation.")
        
        if st.button("Initialize Training Pipeline", type="primary"):
            with st.spinner("Training Neural Network... This may take a few moments depending on dataset size."):
                success, msg = train_model()
                
                if success:
                    st.success(f"SUCCESS: {msg}")
                else:
                    st.error(f"ERROR: {msg}")

elif choice == "Reports":
    st.markdown("<div class='hero-title'>Attendance Reports</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Historical patterns, absenteeism, and trends.</div>", unsafe_allow_html=True)

    summary_data = db_manager.get_attendance_summary_per_student()
    trend_data = db_manager.get_daily_attendance_trend()

    if not summary_data:
        st.info("No attendance data recorded yet.")
    else:
        # --- Attendance % table, sorted worst-attendance-first ---
        st.subheader("Per-Student Attendance Summary")
        df_summary = pd.DataFrame(summary_data)
        df_summary = df_summary.sort_values("attendance_percentage", ascending=True)
        df_display = df_summary[["student_id", "name", "days_present", "days_absent", "attendance_percentage"]]
        df_display.columns = ["ID", "Name", "Days Present", "Days Absent", "Attendance %"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

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
                <div style='background: #161b22; padding: 15px; border-radius: 10px; border-left: 4px solid #f85149; margin-bottom: 10px;'>
                    <b>{row['name']}</b> ({row['student_id']}) — 
                    <span style='color: #f85149;'>{row['attendance_percentage']}% attendance</span> 
                    ({row['days_present']}/{row['total_days'] if 'total_days' in row else row['days_present'] + row['days_absent']} days)
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