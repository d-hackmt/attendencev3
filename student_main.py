# student_main.py
import streamlit as st
from Attendence.components.student_ui import show_student_panel, show_view_attendance_panel
from Attendence.services.class_service import get_all_classes
from Attendence.services.attendance_service import fetch_attendance_records
import pandas as pd

st.set_page_config(
    page_title="Student Portal",
    layout="centered",
    page_icon="🎓"
)

st.markdown("""
<h1 style='text-align: center; color: #4B8BBE;'>🎓 Student Attendance Portal</h1>
<hr style='border-top: 1px solid #bbb;' />
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📥 Mark Attendance", "📅 View My Attendance"])

with tab1:
    show_student_panel()

with tab2:
    show_view_attendance_panel()
