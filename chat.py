import os
import streamlit as st

from api_calls import get_api_response
from dotenv import load_dotenv
from openai import OpenAI
from utils import handle_end_chat_confirmation, end_chat_session, generate_questions_with_openai

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def render_chat_subheader(student_name):
    cols = st.columns([2, 4, 2], gap="small")
    with cols[1]:
        st.subheader(f"Chat session with {student_name}", anchor=False)

def render_sidebar_header():
    cols = st.sidebar.columns([3, 5])
    with cols[1]:
        st.sidebar.header("""You may also ask:""")

def render_chat_history(chat_history):
    for message in chat_history:
        with st.chat_message(name=message["role"], avatar=message["avatar"]):
            st.markdown(message["content"])

def display_predefined_questions(current_chat_session, student_name, student_avatar):
    if "next_questions" not in current_chat_session or current_chat_session.get("refresh_questions"):
        chat_history = current_chat_session.get("chat_history", [])
        generated_questions = generate_questions_with_openai(chat_history)
        current_chat_session["next_questions"] = generated_questions if generated_questions else ["No more suggestions available."]
        current_chat_session["refresh_questions"] = False

    for question in current_chat_session["next_questions"]:
        if st.sidebar.button(question, icon=":material/forum:", use_container_width=True):
            handle_predefined_question(current_chat_session, question, student_name)

def handle_sidebar_button(label, action, icon, current_chat_session, type):
    if st.sidebar.button(label=label, icon=icon, use_container_width=True, type=type):
        current_chat_session["confirm_end_chat"] = action
        st.rerun()

def render_sidebar_buttons(current_chat_session, buttons_config):
    for button in buttons_config:
        if st.sidebar.button(label=button["label"], icon=button["icon"], use_container_width=True, type=button["type"]):
            current_chat_session["confirm_end_chat"] = button["action"]
            end_chat_session(chat_session_id=current_chat_session["chat_session_id"])
            st.rerun()

def handle_predefined_question(current_chat_session, question, student_name):
    handle_user_input(user_input=question, current_chat_session=current_chat_session, student_name=student_name)

def handle_user_input(user_input, current_chat_session, student_name):
    add_message_to_history(current_chat_session=current_chat_session, role="user", content=user_input, avatar="user")
    current_chat_session["refresh_questions"] = True
    response = get_api_response_with_spinner(user_input, current_chat_session, student_name)
    add_message_to_history(current_chat_session=current_chat_session, role="assistant", content=response.get('answer', 'Unexpected error. Please contact support'), avatar=current_chat_session["selected_student"]["image"])

def add_message_to_history(current_chat_session, role, content, avatar):
    if role == "user":
        with st.chat_message(name=role, avatar=avatar):
            st.markdown(content)
    current_chat_session["chat_history"].append({"role": role, "content": content, "avatar": avatar})
    if role == "assistant":
        st.rerun()

def get_api_response_with_spinner(user_input, current_chat_session, student_name, spinner_message=None):
    spinner_message = spinner_message or f"{student_name} is typing..."
    with st.spinner(spinner_message):
        return get_api_response(question=user_input, chat_session_id=current_chat_session["chat_session_id"])

def load_chat_page():
    if not st.session_state["login_sessions"]["chat_sessions"]:
        st.error("No active chat session found.")
        return

    current_chat_session = st.session_state["login_sessions"]["chat_sessions"][-1]
    student_name = current_chat_session["selected_student"]["name"]
    student_avatar = current_chat_session["selected_student"]["image"]

    with st.sidebar:
        st.write("")

    render_chat_subheader(student_name)

    if current_chat_session["confirm_end_chat"]:
        handle_end_chat_confirmation(current_chat_session=current_chat_session)
        return
    
    sidebar_buttons_config = [
        {"label": "Back to Main Page", "action": "main", "icon": ":material/arrow_back:", "type": "primary"},
        {"label": "Start new session", "action": "choice", "icon": ":material/arrow_outward:", "type": "secondary"}
    ]
    render_sidebar_buttons(current_chat_session, sidebar_buttons_config)

    render_sidebar_header()

    render_chat_history(current_chat_session["chat_history"])
    user_input = st.chat_input("Enter your message")
    display_predefined_questions(current_chat_session, student_name, student_avatar)

    if user_input:
        handle_user_input(user_input, current_chat_session, student_name)
