import streamlit as st
import pandas as pd
from Attendence.chatbot_utils import get_agent_for_df, AppState
from Attendence.clients import create_supabase_client

def show_chatbot_panel():
    st.header("🤖 Chat with Attendance Data")

    # --- Initialize Supabase ---
    try:
        supabase = create_supabase_client()
    except Exception:
        st.error("Failed to initialize Supabase client.")
        return

    # --- Step 1: Dropdown for Class Files from Supabase ---
    try:
        class_rows = supabase.table("classroom_settings").select("class_name").execute().data or []
        class_names = [entry["class_name"] for entry in class_rows]
    except Exception as e:
        st.error(f"Failed to fetch classes: {e}")
        return

    if not class_names:
        st.warning("No classes found in Supabase.")
        return

    selected_class = st.selectbox("Choose a classroom", class_names, key="chatbot_class_select")

    if selected_class:
        # --- Fetch Attendance Data for Selected Class ---
        try:
            records = (
                supabase.table("attendance")
                .select("*")
                .eq("class_name", selected_class)
                .order("date", desc=True)
                .execute()
                .data
            )
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
        # Note: We use selected_class as the identifier instead of filename
        if (
            "chat_agent" not in st.session_state
            or st.session_state.get("active_file") != selected_class
        ):
            st.session_state.chat_agent = get_agent_for_df(pivot_df)
            st.session_state.active_file = selected_class
            st.session_state.chat_history = []

        # --- Step 3: Chat Interface ---
        question = st.text_input("Ask a question about this class")

        if question:
            question = question.strip()
            with st.spinner("Thinking..."):
                result = st.session_state.chat_agent.invoke(AppState(question=question))
                # Avoid duplicate if user presses Enter multiple times quickly
                if (
                    not st.session_state.chat_history
                    or st.session_state.chat_history[-1] != ("You", question)
                ):
                    st.session_state.chat_history.append(("You", question))
                    st.session_state.chat_history.append(("Bot", result["answer"]))

        # --- Step 4: Chat Display ---
        for role, message in st.session_state.chat_history:
            if role == "You":
                st.markdown(f"**🧑 You:** {message}")
            else:
                st.markdown(f"**🤖 Bot:** {message}")
