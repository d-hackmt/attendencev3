# admin_main.py
import streamlit as st
from Attendence.admin import show_admin_panel
from Attendence.analytics import show_analytics_panel
from core.chatbot import show_chatbot_panel

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

admin_tab, analytics_tab , chatbot_tab = st.tabs(["🧑‍🏫 Admin Panel", "📊 Analytics", "🤖 Chatbot"])

with admin_tab:
    show_admin_panel()

with analytics_tab:
    show_analytics_panel()

with chatbot_tab:
    show_chatbot_panel()
