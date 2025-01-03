import asyncio
import streamlit as st

from api_calls import get_api_response
from dotenv import load_dotenv
from utils import handle_end_chat_confirmation, end_chat_session, generate_questions_with_openai

load_dotenv()

def render_chat_subheader(student_name):
    cols = st.columns([2, 4, 2], gap="small")
    with cols[1]:
        st.subheader(body=f"Chat session with {student_name}", anchor=False)

def render_chat_history(chat_history):
    for message in chat_history:
        with st.chat_message(name=message["role"], avatar=message["avatar"]):
            st.markdown(message["content"])

def display_predefined_questions(current_chat_session, student_name, student_avatar):
    with st.sidebar:
        st.markdown("---")
        cols = st.columns([0.5, 3, 0.5])
        with cols[1]:
            st.title("""You may also ask\n""")
            st.write("")

    if "next_questions" not in current_chat_session or current_chat_session["refresh_questions"]==True:
        chat_history = current_chat_session["chat_history"]
        if len(chat_history) > 1:
            with st.sidebar:
                with st.spinner("Loading questions..."):
                    generated_questions = asyncio.run(generate_questions_with_openai(chat_history=chat_history, num_questions=4))
                    current_chat_session["next_questions"] = generated_questions
        current_chat_session["refresh_questions"] = False

    for question in current_chat_session["next_questions"]:
        if st.sidebar.button(question, icon=":material/forum:", use_container_width=True):
            handle_user_input(user_input=question, current_chat_session=current_chat_session, student_name=student_name, student_avatar=student_avatar)

def render_sidebar_buttons(current_chat_session, buttons_config):
    for button in buttons_config:
        if st.sidebar.button(label=button["label"], icon=button["icon"], use_container_width=True, type=button["type"]):
            current_chat_session["confirm_end_chat"] = button["action"]
            end_chat_session(chat_session_id=current_chat_session["chat_session_id"])
            st.rerun()

def handle_user_input(user_input, current_chat_session, student_name, student_avatar):
    add_message_to_history(current_chat_session=current_chat_session, role="user", content=user_input, avatar="user")
    current_chat_session["refresh_questions"] = True
    response = get_api_response_with_spinner(user_input, current_chat_session, student_name)
    add_message_to_history(current_chat_session=current_chat_session, role="assistant", content=response.get('answer', 'Unexpected error. Please contact support'), avatar=student_avatar)

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
    chat_history = current_chat_session["chat_history"]
    sidebar_buttons_config = [{"label": "Back to Main Page", "action": "main", "icon": ":material/arrow_back:", "type": "primary"}, {"label": "Start new session", "action": "choice", "icon": ":material/arrow_outward:", "type": "secondary"}]

    render_chat_subheader(student_name)

    if current_chat_session["confirm_end_chat"]:
        st.sidebar.write("")
        handle_end_chat_confirmation(current_chat_session=current_chat_session)
        return
    
    render_sidebar_buttons(current_chat_session=current_chat_session, buttons_config=sidebar_buttons_config)

    render_chat_history(chat_history=chat_history)
    user_input = st.chat_input(placeholder="Enter your message")
    display_predefined_questions(current_chat_session=current_chat_session, student_name=student_name, student_avatar=student_avatar)

    if user_input:
        handle_user_input(user_input=user_input, current_chat_session=current_chat_session, student_name=student_name, student_avatar=student_avatar)
