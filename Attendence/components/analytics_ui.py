# Attendence/components/analytics_ui.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from Attendence.services import class_service, attendance_service
from Attendence.core.logger import get_logger

logger = get_logger(__name__)

def show_analytics_panel():
    st.subheader("📊 Attendance Analytics")

    try:
        class_list = [c["class_name"] for c in class_service.get_all_classes()]
    except Exception:
        st.error("Failed to fetch class list.")
        return

    if not class_list:
        st.warning("No classes found.")
        return

    selected_class = st.selectbox("Select Class", class_list)

    try:
        records = attendance_service.fetch_attendance_records(selected_class)
    except Exception:
        st.error("Failed to fetch attendance data.")
        return

    if not records:
        st.warning(f"No attendance data for class '{selected_class}'.")
        return

    df = pd.DataFrame(records)
    df["status"] = "P"
    pivot_df = df.pivot_table(index=["roll_number", "name"], columns="date", values="status", aggfunc="first", fill_value="A").reset_index()
    pivot_df.columns.name = None
    
    # Process numeric conversion if strictly needed, though analytics might just need counts.
    # But for consistency with admin:
    pivot_df["roll_number"] = pd.to_numeric(pivot_df["roll_number"], errors="coerce")
    pivot_df = pivot_df.dropna(subset=["roll_number"])
    pivot_df["roll_number"] = pivot_df["roll_number"].astype(int)
    pivot_df = pivot_df.sort_values("roll_number")

    st.dataframe(pivot_df, width="stretch")

    # The first 2 columns are roll_number and name. The rest are dates.
    date_cols = pivot_df.columns[2:]
    pivot_df["Present_Count"] = pivot_df[date_cols].apply(lambda row: sum(val == "P" for val in row), axis=1)
    
    # Avoid division by zero
    total_classes = len(date_cols)
    if total_classes > 0:
        pivot_df["Attendance %"] = (pivot_df["Present_Count"] / total_classes * 100).round(2)
    else:
        pivot_df["Attendance %"] = 0.0

    # --- Metrics ---
    total_students = len(pivot_df)
    total_classes = len(date_cols)
    avg_attendance = pivot_df["Attendance %"].mean()

    m1, m2, m3 = st.columns(3)
    m1.metric("👥 Total Students", total_students)
    m2.metric("📅 Total Classes", total_classes)
    m3.metric("📊 Avg Attendance", f"{avg_attendance:.2f}%")

    st.divider()

    # --- Charts Layout ---
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("📈 Attendance Count (Top 30)")
        top_df = pivot_df[["name", "Present_Count"]].nlargest(30, "Present_Count").set_index("name")
        st.bar_chart(top_df, color="#4B8BBE")

    with c2:
        st.subheader("🍰 Overall Distribution")
        try:
            flattened = pivot_df[date_cols].values.flatten()
            present = sum(val == "P" for val in flattened)
            absent = sum(val != "P" for val in flattened)

            if present + absent > 0:
                fig, ax = plt.subplots(figsize=(2, 2))  # Small size
                ax.pie(
                    [present, absent], 
                    labels=["Present", "Absent"], 
                    colors=["#4CAF50", "#FF5252"],
                    autopct="%1.0f%%", 
                    startangle=90,
                    textprops={'fontsize': 10, 'color': 'white'}
                )
                ax.axis("equal")
                # Transparent background
                fig.patch.set_alpha(0)
                st.pyplot(fig, width="content")
            else:
                st.info("No data")
        except Exception:
            logger.exception("Failed to render pie chart")

    st.divider()
    
    # --- Detailed Tables ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🏆 Top 3 Students")
        st.table(pivot_df.sort_values("Attendance %", ascending=False).head(3)[["name", "Attendance %"]])

    with col_b:
        st.subheader("⚠️ Bottom 3 Students")
        st.table(pivot_df.sort_values("Attendance %").head(3)[["name", "Attendance %"]])

    st.subheader("🎯 Filter by Attendance Range")
    min_val, max_val = float(pivot_df["Attendance %"].min()), float(pivot_df["Attendance %"].max())
    
    if min_val == max_val:
        st.info(f"All students have {min_val}% attendance.")
    else:
        selected_range = st.slider("Select range (%)", 0.0, 100.0, (min_val, max_val), step=1.0)
        filtered = pivot_df[(pivot_df["Attendance %"] >= selected_range[0]) & (pivot_df["Attendance %"] <= selected_range[1])]
        st.markdown(f"**{len(filtered)}** students in range:")
        st.dataframe(filtered[["name", "roll_number", "Present_Count", "Attendance %"]], width="stretch")
