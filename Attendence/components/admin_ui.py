# Attendence/components/admin_ui.py
import streamlit as st
import pandas as pd
from Attendence.services import auth_service, class_service, attendance_service, github_service
from Attendence.core.logger import get_logger
from Attendence.core.utils import current_ist_date

logger = get_logger(__name__)

def show_admin_panel():
    st.set_page_config(page_title="Admin Panel", layout="wide", page_icon="👩‍🏫")
    st.markdown("""
        <h1 style='text-align: center; color: #4B8BBE;'>👩‍🏫 Admin Control Panel</h1>
        <hr style='border-top: 1px solid #bbb;' />
    """, unsafe_allow_html=True)

    # Login
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("🔐 Login"):
                if auth_service.authenticate_admin(username, password):
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return

    # Sidebar
    with st.sidebar:
        st.markdown("## ➕ Create Class")
        class_input = st.text_input("New Class Name")
        if st.button("➕ Add Class"):
            if class_input.strip():
                success, msg = class_service.create_class(class_input)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)

        if st.button("🚪 Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

        st.markdown("## 🗑️ Delete Class")
        delete_target = st.text_input("Enter class to delete")
        
        if "confirm_delete" not in st.session_state:
            st.session_state.confirm_delete = None

        if st.button("Delete This Class"):
            if delete_target.strip():
                st.session_state.confirm_delete = delete_target
            else:
                st.warning("Please enter a class name.")

        if st.session_state.confirm_delete == delete_target and delete_target:
            st.warning(f"Are you sure you want to delete '{delete_target}'? This cannot be undone.")
            confirmation = st.text_input("Type DELETE to confirm", key="delete_confirm_input")
            
            if st.button("⚠️ CONFIRM DELETE"):
                if confirmation == "DELETE":
                    try:
                        class_service.delete_class(delete_target)
                        st.success(f"Class '{delete_target}' deleted.")
                        st.session_state.confirm_delete = None
                        st.rerun()
                    except Exception:
                        st.error("Failed to delete class.")
                else:
                    st.error("Verification failed. Type DELETE exactly.")
        elif st.session_state.confirm_delete:
            # Clear if user changed the input
            st.session_state.confirm_delete = None

    # Class Controls
    try:
        classes = class_service.get_all_classes()
    except Exception:
        st.error("Failed to fetch classes.")
        return

    if not classes:
        st.warning("No classes found.")
        return

    class_names = [c["class_name"] for c in classes]
    
    # Persist selection across reruns
    if "admin_selected_class" not in st.session_state:
        st.session_state.admin_selected_class = class_names[0] if class_names else None

    # Ensure selected class is still valid
    if st.session_state.admin_selected_class not in class_names and class_names:
        st.session_state.admin_selected_class = class_names[0]
        
    current_index = 0
    if st.session_state.admin_selected_class in class_names:
        current_index = class_names.index(st.session_state.admin_selected_class)

    selected_class_name = st.selectbox(
        "📚 Select a Class", 
        class_names, 
        index=current_index
    )
    
    # Update state
    st.session_state.admin_selected_class = selected_class_name
    config = next((c for c in classes if c["class_name"] == selected_class_name), None)

    st.markdown(f"**Current Code:** `{config['code']}`")
    st.markdown(f"**Current Limit:** `{config['daily_limit']}`")

    is_open = config.get("is_open", False)
    other_open = [c["class_name"] for c in classes if c.get("is_open") and c["class_name"] != selected_class_name]

    st.subheader("🛠️ Attendance Controls")
    st.info(f"Status: {'OPEN' if is_open else 'CLOSED'}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Open Attendance"):
            if other_open:
                st.warning(f"Close other open classes: {', '.join(other_open)}")
            else:
                class_service.update_class_status(selected_class_name, True)
                st.rerun()
    with col2:
        if st.button("❌ Close Attendance"):
            class_service.update_class_status(selected_class_name, False)
            st.rerun()

    with st.expander("🔄 Update Code & Limit"):
        new_code = st.text_input("New Code", value=config["code"])
        new_limit = st.number_input("New Limit", min_value=1, value=config["daily_limit"], step=1)
        if st.button("📏 Save Settings"):
            class_service.update_class_settings(selected_class_name, new_code, new_limit)
            st.success("✅ Settings updated.")
            st.rerun()

    # Matrix & Push
    try:
        records = attendance_service.fetch_attendance_records(selected_class_name)
    except Exception:
        st.error("Failed to fetch records.")
        return

    if records:
        df = pd.DataFrame(records)
        df["status"] = "P"
        pivot_df = df.pivot_table(index=["roll_number", "name"], columns="date", values="status", aggfunc="first", fill_value="A").reset_index()
        pivot_df["roll_number"] = pd.to_numeric(pivot_df["roll_number"], errors="coerce")
        pivot_df = pivot_df.dropna(subset=["roll_number"])
        pivot_df["roll_number"] = pivot_df["roll_number"].astype(int)
        pivot_df = pivot_df.sort_values("roll_number")

        def highlight(val):
            return "background-color:#d4edda;color:green" if val == "P" else "background-color:#f8d7da;color:red"

        styled = pivot_df.style.map(highlight, subset=pivot_df.columns[2:])
        st.dataframe(styled, width="stretch")

        csv_data = pivot_df.to_csv(index=False)
        st.download_button("⬇️ Download CSV", csv_data.encode(), f"{selected_class_name}_matrix.csv", "text/csv")

        if st.button("🚀 Push to GitHub"):
            success, msg = github_service.push_attendance_matrix(selected_class_name, csv_data)
            if success:
                st.success(msg)
            else:
                st.error(msg)
    else:
        st.info("No attendance data yet.")
