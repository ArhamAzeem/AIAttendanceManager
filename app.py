import streamlit as st
import pandas as pd
from db import DatabaseManager
from utils import capture_images
from ml_utils import train_model, recognize_faces_and_mark_attendance
import datetime
import time

st.set_page_config(page_title="AI Attendance System", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    h1, h2, h3 {
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .hero-title {
        color: #58a6ff;
        font-size: 3.5rem;
        margin-bottom: 0.5rem;
        font-weight: 800;
    }
    .sub-title {
        color: #8b949e;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #58a6ff;
    }
    .metric-value {
        font-size: 3rem;
        font-weight: 800;
        color: #f0f6fc;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 1rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stDataFrame {
        border-radius: 12px;
        border: 1px solid #30363d;
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
    menu = ["Overview", "Live Attendance", "Student Directory", "AI Training Center"]
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
