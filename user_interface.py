import asyncio
import streamlit as st

from frontend.add_student_page import load_add_student_page
from frontend.chat_page import load_chat_page
from frontend.choice_page import load_choice_page
from frontend.login_page import load_login_page
from frontend.main_page import load_main_page
from frontend.previous_chats_page import load_previous_chats_page
from frontend.signup_page import load_signup_page
from frontend.password_reset_page import load_password_reset_page

all_pages = {
    "login": load_login_page,
    "signup": load_signup_page,
    "main": load_main_page,
    "previous_chats": load_previous_chats_page,
    "password_reset": load_password_reset_page,
    "choice": load_choice_page,
    "chat": load_chat_page,
    "add_student": load_add_student_page
}

st.set_page_config(page_title="Agastya Chatbot", page_icon="🏫", layout="wide", initial_sidebar_state="auto")
st.logo(image="frontend/images/logo.png", size="large", icon_image="frontend/images/logo.png", link="https://www.agastya.org/")

if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

asyncio.run(all_pages[st.session_state.current_page]())