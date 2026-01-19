# Attendence/components/chatbot_ui.py
import streamlit as st
import pandas as pd
from Attendence.services import chatbot_service, class_service, attendance_service
from Attendence.services.chatbot_service import AppState

def show_chatbot_panel():
    st.header("🤖 Chat with Attendance Data")

    # --- Step 1: Dropdown for Class Files from Supabase ---
    try:
        class_names = [c["class_name"] for c in class_service.get_all_classes()]
    except Exception as e:
        st.error(f"Failed to fetch classes: {e}")
        return

    if not class_names:
        st.warning("No classes found.")
        return

    selected_class = st.selectbox("Choose a classroom", class_names, key="chatbot_class_select")

    if selected_class:
        # --- Fetch Attendance Data for Selected Class ---
        try:
            records = attendance_service.fetch_attendance_records(selected_class)
        except Exception as e:
            st.error(f"Failed to fetch attendance records: {e}")
            return

        if not records:
            st.warning(f"No attendance records found for {selected_class}.")
            return

        # --- Process Data into Pivot Table ---
        df = pd.DataFrame(records)
        df["status"] = "P"
        # Pivot: Rows=Students, Cols=Dates, Value=P/A
        pivot_df = df.pivot_table(
            index=["roll_number", "name"], 
            columns="date", 
            values="status", 
            aggfunc="first", 
            fill_value="A"
        ).reset_index()

        # Clean up roll numbers for consistent sorting/display
        pivot_df["roll_number"] = pd.to_numeric(pivot_df["roll_number"], errors="coerce")
        pivot_df = pivot_df.dropna(subset=["roll_number"])
        pivot_df["roll_number"] = pivot_df["roll_number"].astype(int)
        pivot_df = pivot_df.sort_values("roll_number")

        st.dataframe(pivot_df, width="stretch")

        # --- Step 2: Setup Chatbot Agent for Selected File ---
        if (
            "chat_agent" not in st.session_state
            or st.session_state.get("active_file") != selected_class
        ):
            st.session_state.chat_agent = chatbot_service.get_agent_for_df(pivot_df)
            st.session_state.active_file = selected_class
            st.session_state.chat_history = []

        # --- Step 3: Chat Display & Logic ---
        # Display existing history
        for role, message in st.session_state.chat_history:
            # Map role to streamlit avatar/role
            # "You" -> "user", "Bot" -> "assistant"
            st_role = "user" if role == "You" else "assistant"
            with st.chat_message(st_role):
                st.markdown(message)

        # Input for new question
        if question := st.chat_input("Ask a question about this class..."):
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(question)
            
            # Add to history
            st.session_state.chat_history.append(("You", question))

            # Process with spinner
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.chat_agent.invoke(AppState(question=question))
                    answer = result["answer"]
                except Exception as e:
                    answer = f"❌ Error: {str(e)}"
            
            # Display bot response
            with st.chat_message("assistant"):
                st.markdown(answer)
            
            # Add to history
            st.session_state.chat_history.append(("Bot", answer))
