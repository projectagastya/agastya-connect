import ast
import os
import re
import streamlit as st

from config.frontend.llm import (
    QUESTIONS_GENERATION_MODEL_ID,
    QUESTIONS_GENERATION_MODEL_TEMPERATURE,
    QUESTIONS_GENERATION_MODEL_MAX_TOKENS
)
from config.frontend.other import (
    APP_LOGO_URL,
    DEFAULT_PROFILE_IMAGE_URL,
    STUDENT_IMAGE_URL
)
from config.shared.timezone import get_current_datetime
from utils.frontend.api_calls import (
    chat,
    healthy,
    start_chat,
    get_active_sessions,
    get_chat_history_messages,
    end_all_chats
)
from prompts.frontend import SYSTEM_PROMPT_GENERATE_NEXT_QUESTIONS
from langchain_google_genai import ChatGoogleGenerativeAI
from urllib.parse import urlparse
from utils.shared.errors import get_user_error
from utils.shared.logger import frontend_logger
from utils.shared.translate import translate_text
from utils.shared.other import formatted
from uuid import uuid4

# Function to configure Streamlit page settings.
def setup_page(
        page_title="Agastya Connect",
        page_icon=APP_LOGO_URL.format(domain=urlparse(st.context.url).netloc),
        layout="wide",
        initial_sidebar_state="collapsed",
    ):
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout, initial_sidebar_state=initial_sidebar_state)

# Function to display text with custom formatting using Markdown.
def add_text(content, alignment="left", size=12, bold=False, italics=False, underline=False, color=None):
    rem_size = size / 16
    styles = []
    if bold:
        styles.append("font-weight: bold;")
    if italics:
        styles.append("font-style: italic;")
    if underline:
        styles.append("text-decoration: underline;")
    style = f"text-align: {alignment}; font-size: {rem_size}rem; " + " ".join(styles)
    if color:
        style += f"color: {color};"
    st.markdown(body=f"<div style='{style}'>{content}</div>", unsafe_allow_html=True)

# Function to generate a version 4 UUID.
def generate_uuid():
    new_uuid = str(uuid4())
    frontend_logger.info(f"Generated UUID: {new_uuid}")
    return new_uuid

# Function to initialize or resume a chat session in Streamlit session state.
async def initialize_chat_session(student_choice: dict):
    if "active_chat_session" not in st.session_state:
        st.session_state["active_chat_session"] = {
            "id": None,
            "chat_history": [],
            "next_questions": [],
            "recent_questions": [],
            "chat_start_timestamp": None,
            "chat_end_timestamp": None,
            "student_profile": None
        }

    user_email = getattr(st.user, "email")  
    login_session_id = getattr(st.user, "nonce")
    user_avatar = getattr(st.user, "picture", DEFAULT_PROFILE_IMAGE_URL.format(domain=urlparse(st.context.url).netloc))
    user_first_name = getattr(st.user, "given_name")
    user_last_name = getattr(st.user, "family_name")
    student_name = student_choice['student_name']
    student_avatar = STUDENT_IMAGE_URL.format(domain=urlparse(st.context.url).netloc, student_name=student_name)
    is_resuming = st.session_state["active_chat_session"]["id"] is not None
    
    chat_session_id = st.session_state["active_chat_session"]["id"] if is_resuming else generate_uuid()
    
    st.session_state["active_chat_session"]["id"] = chat_session_id
    st.session_state["active_chat_session"]["student_profile"] = student_choice
    st.session_state["active_chat_session"]["chat_start_timestamp"] = get_current_datetime() if not is_resuming else st.session_state["active_chat_session"]["chat_start_timestamp"]
    
    if is_resuming:
        frontend_logger.info(f"initialize_chat_session | Resuming chat with {student_name}, session id: {chat_session_id}")
        
        history_success, history_message, formatted_history = get_chat_history_formatted(
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_avatar=user_avatar,
            student_avatar=student_avatar
        )
        
        if not history_success:
            frontend_logger.error(f"initialize_chat_session | Failed to get chat history: {history_message}")
            st.error(get_user_error())
            st.stop()
            
        st.session_state["active_chat_session"]["chat_history"] = formatted_history
    else:
        st.session_state["active_chat_session"]["chat_history"] = []
        
        start_chat_success, start_chat_message, first_message = start_chat(
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            user_email=user_email,
            student_name=student_name,
            login_session_id=login_session_id,
            chat_session_id=chat_session_id
        )

        if not start_chat_success:
            frontend_logger.error(f"initialize_chat_session | start_chat failed: {start_chat_message}")
            st.error(get_user_error())
            st.stop()

        st.session_state["active_chat_session"]["chat_history"].append({
            "role": "assistant", 
            "content": first_message,
            "content-en": first_message,
            "avatar": student_avatar
        })

    st.session_state["active_chat_session"]["next_questions"] = await generate_next_questions(
        chat_history=st.session_state["active_chat_session"]["chat_history"],
        student_name=student_name
    )

# Function to retrieve chat history from the backend and format it for UI display.
def get_chat_history_formatted(login_session_id: str, chat_session_id: str, user_avatar: str, student_avatar: str) -> tuple[bool, str, list]:
    success = False
    message = ""
    data = []
    try:
        history_success, history_message, messages = get_chat_history_messages(
            login_session_id=login_session_id,
            chat_session_id=chat_session_id
        )
        
        if not history_success:
            message = get_user_error()
            frontend_logger.error(f"get_chat_history_formatted | Failed to retrieve chat history | Error: {history_message}")
            return False, message, []
            
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            avatar = user_avatar if role == "user" else student_avatar
            
            data.append({
                "role": role,
                "content": content,
                "content-en": content,
                "avatar": avatar
            })
            
        success = True
        message = "Retrieved and formatted chat history"
        frontend_logger.info(f"get_chat_history_formatted | {message}")
    except Exception as e:
        message = get_user_error()
        frontend_logger.error(f"get_chat_history_formatted | Error: {str(e)}")
    return success, message, data

# Function to check if a string contains Kannada characters.
def is_kannada(text: str) -> bool:
    if text is None:
        return False
    return any('\u0c80' <= ch <= '\u0cff' for ch in text)

# Function to render the chat subheader with the student's name.
def render_chat_subheader(student_name):
    add_text(content=f"Chat with {formatted(student_name)}", alignment="center", size=35, bold=True)

# Function to render the chat history messages in the Streamlit UI.
def render_chat_history(chat_history):
    for message in chat_history:
        display_message = message["content"]
        
        with st.chat_message(name=message["role"], avatar=message["avatar"]):
            if display_message.strip() == "":
                display_message = "Sorry, I'm unable to provide a response at this time. Please check in again with me later. Thanks for understanding!"
                frontend_logger.warning(f"render_chat_history | Empty response received from chat message: Login Session ID: {st.user.nonce}, Chat Session ID: {st.session_state['active_chat_session']['id']}")
                st.markdown(body=display_message)
                st.error(get_user_error())
                st.stop()
            else:
                st.markdown(body=display_message)

# Function to generate suggested next questions for the instructor using an LLM.
async def generate_next_questions(chat_history, student_name, num_questions=4):
    try:
        user_full_name = getattr(st.user, "given_name") + " " + getattr(st.user,"family_name")

        llm = ChatGoogleGenerativeAI(
            model=QUESTIONS_GENERATION_MODEL_ID, 
            temperature=QUESTIONS_GENERATION_MODEL_TEMPERATURE,
            max_tokens=QUESTIONS_GENERATION_MODEL_MAX_TOKENS
        )

        formatted_history = []
        for message in chat_history:
            if message.get('role') == 'user':
                formatted_message = f"{user_full_name}: {message.get('content-en', '')}"
            elif message.get('role') == 'assistant':
                formatted_message = f"{formatted(student_name)}: {message.get('content-en', '')}"
            formatted_history.append(formatted_message)
        formatted_history = "\n".join(formatted_history)

        generate_next_questions_prompt = SYSTEM_PROMPT_GENERATE_NEXT_QUESTIONS.format(
            student=formatted(student_name),
            formatted_history=formatted_history
        )
        response = await llm.ainvoke(generate_next_questions_prompt)
        generated_text = response.content.strip()

        match = re.search(r'\[.*?\]', generated_text, re.DOTALL)
        questions = ast.literal_eval(match.group(0)) if match else []

        return questions[:num_questions]
    except Exception as e:
        message = get_user_error()
        frontend_logger.error(f"generate_next_questions | Error: {str(e)}")
        return []

# Function to render the suggested next questions as buttons in the UI.
async def render_next_questions(next_questions):
    current_chat_session = st.session_state["active_chat_session"]
    student_profile = current_chat_session["student_profile"]
    student_name = student_profile["student_name"]
    student_avatar = STUDENT_IMAGE_URL.format(domain=urlparse(st.context.url).netloc, student_name=student_name)
    
    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        add_text(content="You may also ask:", alignment="center", size=24, bold=True)
        st.markdown("<br>", unsafe_allow_html=True)
    for question in next_questions:
        if st.sidebar.button(label=question, use_container_width=True):
            await handle_user_input(
                user_input=question,
                current_chat_session=current_chat_session,
                student_name=student_name,
                student_avatar=student_avatar,
                input_type="button"
            )

# Function to handle user input (manual text or button click), interact with the backend chat API, and update session state.
async def handle_user_input(user_input: str, current_chat_session: dict, student_name: str, student_avatar: str, input_type: str):
    user_image = getattr(st.user, "picture", DEFAULT_PROFILE_IMAGE_URL.format(domain=urlparse(st.context.url).netloc))
    user_login_session_id = getattr(st.user, "nonce")
    user_full_name = getattr(st.user, "given_name", " ") + " " + getattr(st.user, "family_name", " ")

    if input_type == "manual-kannada":
        try:
            question_for_api = translate_text(text=user_input, source_language="kn", target_language="en")
        except Exception as e:
            message = get_user_error()
            frontend_logger.error(f"handle_user_input | Error: {str(e)}")
            st.error(get_user_error())
            st.stop()
    else:
        question_for_api = user_input

    with st.chat_message(name="user", avatar=user_image):
        st.markdown(body=user_input)

    spinner_message = f"{formatted(text=student_name).split(' ')[0]} is typing..."
    with st.spinner(spinner_message):
        success, message, answer = chat(
            login_session_id=user_login_session_id,
            chat_session_id=current_chat_session["id"],
            question=question_for_api,
            question_kannada=user_input if input_type == "manual-kannada" else None,
            input_type=input_type,
            user_full_name=user_full_name,
            student_name=student_name
        )

        if not success:
            frontend_logger.error(f"handle_user_input | Getting chat response failed: {message}")
            st.error(get_user_error())
            st.stop()
        
        current_chat_session["chat_history"].append({"role": "user", "content": user_input if input_type == "manual-kannada" else question_for_api, "content-en": question_for_api, "avatar": user_image})
        current_chat_session["chat_history"].append({"role": "assistant", "content": answer, "content-en": answer, "avatar": student_avatar})
        
        chat_history = current_chat_session["chat_history"]

        generated_questions = await generate_next_questions(
            chat_history=chat_history,
            student_name=student_name,
            num_questions=4
        )

        current_chat_session["next_questions"] = generated_questions
        st.rerun()

# Function to check if the user is authenticated via Streamlit.
def authenticated():
    if getattr(st.user, "is_logged_in"):
        return True
    else:
        return False

# Function to perform security checks (authentication, backend health).
def security_check():
    if not healthy():
        frontend_logger.error("security_check | Health check failed")
        st.error(get_user_error())
        st.stop()
    elif not authenticated():
        st.switch_page(page="pages/login.py")

# Function to reset the session state, ending active chats.
def reset_session_state():
    if "active_chat_session" not in st.session_state:
        st.session_state["active_chat_session"] = {}
    if "id" not in st.session_state["active_chat_session"]:
        st.session_state["active_chat_session"]["id"] = None
    if "chat_history" not in st.session_state["active_chat_session"]:
        st.session_state["active_chat_session"]["chat_history"] = []
    if "chat_start_timestamp" not in st.session_state["active_chat_session"]:
        st.session_state["active_chat_session"]["chat_start_timestamp"] = None
    if "chat_end_timestamp" not in st.session_state["active_chat_session"]:
        st.session_state["active_chat_session"]["chat_end_timestamp"] = None
    if "student_profile" not in st.session_state["active_chat_session"]:
        st.session_state["active_chat_session"]["student_profile"] = None

    if "student_choice" not in st.session_state:
        st.session_state["student_choice"] = None
    if "next_questions" not in st.session_state:
        st.session_state["next_questions"] = []
    if "recent_questions" not in st.session_state:
        st.session_state["recent_questions"] = []
    if "loading_page" not in st.session_state:
        st.session_state["loading_page"] = False

if __name__ == "__main__":
    pass