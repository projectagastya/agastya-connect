import asyncio
import streamlit as st

from dotenv import load_dotenv
from frontend_utils import handle_end_chat_confirmation, handle_user_input, render_chat_history, render_chat_subheader, render_sidebar_buttons, display_predefined_questions

load_dotenv()

st.set_page_config(page_title="Agastya Envision", page_icon=":school:", layout="wide", initial_sidebar_state="auto")
st.logo(image="./images/logo.png", size="large", icon_image="images/logo.png", link="https://www.agastya.org/")

if "login_sessions" not in st.session_state:
    st.error("You must log in to access this page.")
    if st.button(label="Log in", icon=":material/login:", type="primary"):
        st.switch_page(page="pages/login.py")
    st.stop()

if not st.session_state["login_sessions"]["chat_sessions"]:
    st.error("No active chat session found.")

current_chat_session = st.session_state["login_sessions"]["chat_sessions"][-1]
student_name = current_chat_session["selected_student"]["name"]
student_avatar = current_chat_session["selected_student"]["image"]
chat_history = current_chat_session["chat_history"]
sidebar_buttons_config = [{"label": "Back to Home Page", "destination": "pages/home.py", "icon": ":material/home:", "type": "primary"}, {"label": "Start new session", "destination": "pages/selection.py", "icon": ":material/arrow_outward:", "type": "secondary"}]

asyncio.run(render_chat_subheader(student_name))

if current_chat_session["confirm_end_chat"]:
    asyncio.run(handle_end_chat_confirmation(current_chat_session=current_chat_session))
    st.stop()

asyncio.run(render_sidebar_buttons(current_chat_session=current_chat_session, buttons_config=sidebar_buttons_config))

asyncio.run(render_chat_history(chat_history=chat_history))

user_input = st.chat_input(placeholder="Enter your message")

if user_input:
    print(f"User input: {user_input}")
    asyncio.run(handle_user_input(user_input=user_input, current_chat_session=current_chat_session, student_name=student_name, student_avatar=student_avatar))
    st.rerun()
    
asyncio.run(display_predefined_questions(current_chat_session=current_chat_session, student_name=student_name, student_avatar=student_avatar))