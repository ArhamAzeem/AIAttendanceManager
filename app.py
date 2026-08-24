import streamlit as st
import pandas as pd
from db import DatabaseManager
from utils import capture_images
from ml_utils import train_model, recognize_faces_and_mark_attendance
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="AI Attendance Manager", layout="wide", page_icon="🎓")

# --- Custom CSS for Premium Aesthetics ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    /* Stylish Title */
    .main-title {
        background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0px;
    }
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #FF416C;
    }
    /* Custom Dataframe borders */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

db_manager = DatabaseManager()

# --- Sidebar Navigation ---
st.sidebar.markdown("### 🎓 AI Attendance System")
menu = ["Dashboard - Attendance", "Dashboard - Students", "Register Student", "Train Model", "Take Attendance"]
choice = st.sidebar.radio("Navigation", menu)

if choice == "Dashboard - Attendance":
    st.markdown("<h1 class='main-title'>Attendance Records</h1>", unsafe_allow_html=True)
    st.markdown("View all time-in and time-out logs.")
    
    selected_date = st.date_input("Filter by Date", datetime.datetime.now())
    selected_date_str = selected_date.strftime("%Y-%m-%d")
    
    logs = db_manager.get_attendance_logs(selected_date_str)
    
    if logs:
        for log in logs:
            student = db_manager.get_student_by_id(log["student_id"])
            log["Name"] = student["name"] if student else "Unknown"
            
        df = pd.DataFrame(logs)
        df = df[["student_id", "Name", "date", "in_time", "out_time"]]
        df.columns = ["Student ID", "Name", "Date", "In-Time", "Out-Time"]
        
        # Display Metrics
        col1, col2 = st.columns(2)
        col1.metric("Total Present Today", len(df))
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No attendance records found for the selected date.")

elif choice == "Dashboard - Students":
    st.markdown("<h1 class='main-title'>Student Directory</h1>", unsafe_allow_html=True)
    st.markdown("Manage all registered students.")
    
    students = db_manager.get_all_students()
    if students:
        df = pd.DataFrame(students)
        st.metric("Total Enrolled Students", len(df))
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No students registered yet.")

elif choice == "Register Student":
    st.markdown("<h1 class='main-title'>Register New Student</h1>", unsafe_allow_html=True)
    st.markdown("Capture biometric facial data for a new student.")
    
    # Auto-assign ID
    auto_id = db_manager.generate_student_id()
    
    col1, col2 = st.columns(2)
    with col1:
        student_id = st.text_input("Student ID (Auto-assigned)", value=auto_id, disabled=True)
        student_name = st.text_input("Student Name")
    
    if st.button("Start Facial Scan", type="primary"):
        if student_name:
            st.info("Initializing webcam... A window will pop up. Please look directly at the camera.")
            
            with st.spinner("Recording facial biometrics..."):
                success, msg = capture_images(student_id, student_name)
            
            if success:
                st.success(f"✅ {student_name} ({student_id}) has been successfully registered!")
                st.balloons()
            else:
                st.error(msg)
        else:
            st.warning("Please enter the Student Name.")

elif choice == "Train Model":
    st.markdown("<h1 class='main-title'>Train AI Model</h1>", unsafe_allow_html=True)
    st.markdown("Compile the latest biometric data into the Convolutional Neural Network.")
    
    students = db_manager.get_all_students()
    if len(students) < 2:
        st.warning("⚠️ You need at least 2 registered students to train the classification model.")
    else:
        st.info(f"{len(students)} students registered and ready for training.")
        if st.button("Initialize Training Pipeline", type="primary"):
            with st.spinner("Training Neural Network in progress... Please wait."):
                success, msg = train_model()
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

elif choice == "Take Attendance":
    st.markdown("<h1 class='main-title'>Smart Attendance</h1>", unsafe_allow_html=True)
    st.markdown("Step in front of the camera to log your In-Time or Out-Time.")
    
    if st.button("Start AI Scanner", type="primary"):
        st.info("Scanner started in a new window. It will automatically close when verified.")
        
        with st.spinner("AI Scanner active..."):
            success, msg = recognize_faces_and_mark_attendance()
        
        if success:
            st.success(f"✅ SUCCESS: {msg}")
        else:
            st.error(f"❌ ERROR: {msg}")
