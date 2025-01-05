import asyncio
import streamlit as st

from add_student import load_add_student_page
from chat import load_chat_page
from choice import load_choice_page
from login import load_login_page
from main import load_main_page
from previous_chats import load_previous_chats_page
from signup import load_signup_page

all_pages = {
    "login": load_login_page,
    "signup": load_signup_page,
    "main": load_main_page,
    "previous_chats": load_previous_chats_page,
    "choice": load_choice_page,
    "chat": load_chat_page,
    "add_student": load_add_student_page
}

st.set_page_config(page_title="Agastya Chatbot", page_icon="🏫", layout="wide", initial_sidebar_state="auto")

if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

if st.session_state.current_page == "chat":
    asyncio.run(load_chat_page())
else:
    all_pages[st.session_state.current_page]()
