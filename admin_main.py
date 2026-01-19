# admin_main.py
import streamlit as st
from Attendence.components.admin_ui import show_admin_panel
from Attendence.components.analytics_ui import show_analytics_panel
from Attendence.components.chatbot_ui import show_chatbot_panel

st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="🧠",
    layout="wide"
)

st.markdown(
    """
    <h1 style='text-align: center; color: #4B8BBE;'>🧠 Admin Dashboard</h1>
    <hr style='border-top: 1px solid #bbb;'/></br>
    """,
    unsafe_allow_html=True
)

# Initialize session state for login if not present
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

admin_tab, analytics_tab , chatbot_tab = st.tabs(["🧑‍🏫 Admin Panel", "📊 Analytics", "🤖 Chatbot"])

with admin_tab:
    show_admin_panel()

with analytics_tab:
    if st.session_state.admin_logged_in:
        show_analytics_panel()
    else:
        st.info("🔒 Please login in the 'Admin Panel' tab to view Analytics.")

with chatbot_tab:
    if st.session_state.admin_logged_in:
        show_chatbot_panel()
    else:
        st.info("🔒 Please login in the 'Admin Panel' tab to use the Chatbot.")
