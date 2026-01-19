# Attendence/components/student_ui.py
import streamlit as st
from Attendence.services import class_service, attendance_service
from Attendence.core.utils import current_ist_date
from Attendence.core.logger import get_logger

logger = get_logger(__name__)

def show_student_panel():
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.title("🎓 Student Attendance Portal")
    with col_refresh:
        if st.button("🔄 Refresh"):
             class_service.get_open_classes.clear()
             st.rerun()

    try:
        class_list = class_service.get_open_classes()
    except Exception:
        st.error("Failed to fetch classes.")
        return

    if not class_list:
        st.warning("🚫 No classrooms are currently open for attendance.")
        st.stop()

    selected_class = st.selectbox("Select Your Class", class_list)

    # We need settings for the selected class to check code and limit
    # The optimized way is to fetch all classes and find the one.
    # Or add get_class_settings to service.
    # For now, let's just fetch all classes again or rely on class_service to provide a helper.
    # To keep it simple, I'll assume we can get class details.
    
    # Since class_service.get_all_classes() returns all data, we can use that.
    classes = class_service.get_all_classes()
    settings = next((c for c in classes if c["class_name"] == selected_class), None)
    
    if not settings:
        st.error("Class settings not found.")
        return

    required_code = settings["code"]
    daily_limit = settings["daily_limit"]

    roll_number_raw = st.text_input("Roll Number").strip()

    if not roll_number_raw:
        st.info("ℹ️ Please enter your roll number to continue.")
        return

    if not roll_number_raw.isdigit():
        st.error("❌ Roll number must be a number.")
        return

    roll_number = int(roll_number_raw)

    # Check roll map
    try:
        locked_name = attendance_service.fetch_roll_map(selected_class, roll_number)
    except Exception:
        st.error("Failed to check roll map.")
        return

    if locked_name:
        st.info(f"🔒 Name auto-filled for Roll {roll_number}: **{locked_name}**")
        name = locked_name
    else:
        name = st.text_input("Name (Will be locked after first time)").strip()

    code_input = st.text_input("Attendance Code")

    if st.button("✅ Submit Attendance"):
        today = current_ist_date()

        if code_input != required_code:
            st.error("❌ Incorrect attendance code.")
            st.stop()

        # Check existing
        if attendance_service.check_existing_attendance(selected_class, roll_number, today):
            st.error("❌ Attendance already marked today.")
            st.stop()
            return

        # Check limit
        count = attendance_service.get_daily_count(selected_class, today)
        if count >= daily_limit:
            st.warning("⚠️ Attendance limit for today has been reached.")
            st.stop()
            return

        # Lock roll map if needed
        if not locked_name:
            try:
                attendance_service.lock_roll_map(selected_class, roll_number, name)
            except Exception:
                 st.error("Failed to lock roll number.")
                 st.stop()
                 return
        elif locked_name != name:
             st.error("❌ Roll number already locked to a different name.")
             st.stop()
             return

        # Mark attendance
        try:
            attendance_service.submit_attendance(selected_class, roll_number, name, today)
            st.success("✅ Attendance submitted successfully!")
        except Exception:
            st.error("Failed to submit attendance.")

def show_view_attendance_panel():
    col_sub, col_ref = st.columns([4,1])
    with col_sub:
        st.subheader("📅 Check Your Attendance Record")
    with col_ref:
        if st.button("🔄 Refresh", key="refresh_view"):
            class_service.get_open_classes.clear()
            st.rerun()

    try:
        class_list = class_service.get_open_classes()
    except Exception:
        class_list = []

    # If no classes, stop
    if not class_list:
        st.info("No open classes found for viewing.")
        return

    with st.form("view_attendance_form"):
        selected_class = st.selectbox("Select Your Class", class_list)
        roll_number_input = st.text_input("Enter Your Roll Number").strip()
        submit = st.form_submit_button("🔍 Show My Attendance")

    if submit and roll_number_input:
        if not roll_number_input.isdigit():
            st.error("Roll number must be a number.")
            return
        
        roll_number = int(roll_number_input)

        try:
            # Fetch ALL records to get proper date range (to know absents)
            all_records = attendance_service.fetch_attendance_records(selected_class)
        except Exception:
            st.error("Failed to fetch records.")
            return

        if not all_records:
            st.info("No attendance records found for this class.")
            return

        import pandas as pd
        import matplotlib.pyplot as plt

        df = pd.DataFrame(all_records)

        # Coerce roll_number to ensure type match
        df["roll_number"] = pd.to_numeric(df["roll_number"], errors="coerce")
        df = df.dropna(subset=["roll_number"])
        df["roll_number"] = df["roll_number"].astype(int)
        
        # Identification of all unique dates for this class
        all_dates = sorted(df["date"].unique())
        total_classes = len(all_dates)

        # Filter for student
        my_records = df[df["roll_number"] == roll_number]
        
        # Robustly count present days (unique dates present)
        my_present_dates = my_records["date"].unique()
        present_count = len(my_present_dates)
        
        # Absent count is simply total - present
        absent_count = total_classes - present_count
        
        # Calculate percentage
        if total_classes > 0:
            percentage = (present_count / total_classes) * 100
        else:
            percentage = 0.0

        # --- Visualization ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Donut Chart
            if total_classes > 0:
                fig, ax = plt.subplots(figsize=(3, 3))
                ax.pie(
                    [present_count, absent_count], 
                    labels=["Present", "Absent"], 
                    colors=["#4CAF50", "#FF5252"],
                    autopct=None, 
                    startangle=90,
                    wedgeprops=dict(width=0.4), # Donut
                    textprops={'color': "white"}
                )
                ax.text(0, 0, f"{percentage:.0f}%", ha='center', va='center', fontsize=20, fontweight='bold', color="white")
                fig.patch.set_alpha(0)
                st.pyplot(fig, width="stretch")
            else:
                st.write("No class data.")

        with col2:
            st.markdown(f"### 👤 Student Roll: {roll_number}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Classes", total_classes)
            m2.metric("Days Present", present_count)
            m3.metric("Attendance %", f"{percentage:.1f}%")
        
        st.divider()
        st.subheader("📜 Detailed History")
        
        if present_count > 0:
            # We want to show ALL dates and status P/A
            # Create a dataframe of all dates
            history_data = []
            present_dates = set(my_records["date"].unique())
            
            for date in sorted(all_dates, reverse=True):
                status = "✅ Present" if date in present_dates else "❌ Absent"
                history_data.append({"Date": date, "Status": status})
            
            st.dataframe(pd.DataFrame(history_data), width="stretch")
        else:
            st.warning("You have not attended any classes yet.")
            # Still show absents?
            history_data = [{"Date": d, "Status": "❌ Absent"} for d in sorted(all_dates, reverse=True)]
            st.dataframe(pd.DataFrame(history_data), width="stretch")
