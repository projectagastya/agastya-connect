import ast
import re
import streamlit as st

from configure_logger import frontend_logger
from datetime import datetime
from frontend_api_calls import (
    chat,
    end_chat,
    healthy,
    start_chat
)
from langchain_google_genai import ChatGoogleGenerativeAI
from uuid import uuid4

def setup_page(
        page_title="Agastya AI",
        page_icon=":school:",
        layout="wide",
        initial_sidebar_state="auto",
        logo_image="static/logo.png",
        logo_size="large",
        logo_link="https://agastya.org",
        logo_icon_image="static/logo.png"
    ):
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout, initial_sidebar_state=initial_sidebar_state)
    st.logo(image=logo_image, size=logo_size, link=logo_link, icon_image=logo_icon_image)

def formatted_name(student_name: str):
    return student_name.replace('-', ' ').title()
    
def generate_uuid():
    new_uuid = str(uuid4())
    frontend_logger.info(f"Generated UUID: {new_uuid}")
    return new_uuid

def add_aligned_text(content, alignment="left", size=12, bold=False, italics=False, underline=False, color=None):
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

async def initialize_chat_session(student_choice: dict):
    if "active_chat_session" in st.session_state:
        st.session_state["active_chat_session"] = {
            "id": None,
            "chat_history": [],
            "next_questions": [],
            "recent_questions": [],
            "chat_start_timestamp": None,
            "chat_end_timestamp": None,
            "student_profile": None
        }

    if hasattr(st.experimental_user, "email"):
        email = getattr(st.experimental_user, "email")
    else:
        frontend_logger.error("initialize_chat_session | User email not found in st.experimental_user")
        st.warning("Unexpected internal error has occured. Please contact support")
        st.stop()
        
    if hasattr(st.experimental_user, "nonce"):
        login_session_id = getattr(st.experimental_user, "nonce")
    else:
        frontend_logger.error("initialize_chat_session | User nonce not found in st.experimental_user")
        st.warning("Unexpected internal error has occured. Please contact support")
        st.stop()
    
    chat_session_id = generate_uuid()
    student_name = student_choice['name']
    
    st.session_state["active_chat_session"]["id"] = chat_session_id
    st.session_state["active_chat_session"]["chat_history"] = []
    st.session_state["active_chat_session"]["next_questions"] = []
    st.session_state["active_chat_session"]["recent_questions"] = []
    st.session_state["active_chat_session"]["chat_start_timestamp"] = datetime.now()
    st.session_state["active_chat_session"]["chat_end_timestamp"] = None
    st.session_state["active_chat_session"]["student_profile"] = student_choice

    start_chat_success, start_chat_message, first_message = start_chat(
        email=email,
        student_name=student_name,
        login_session_id=login_session_id,
        chat_session_id=chat_session_id
    )

    if not start_chat_success:
        st.error(start_chat_message)
        st.stop()

    st.session_state["active_chat_session"]["chat_history"].append({"role": "assistant", "content": first_message, "avatar": student_choice["image"]})
    st.session_state["active_chat_session"]["next_questions"] = await generate_next_questions(
        chat_history=st.session_state["active_chat_session"]["chat_history"],
        student_name=student_name
    )

def cleanup_chat_session(email, chat_session_id, student_name):
    if hasattr(st.experimental_user, "nonce"):
        user_login_session_id = getattr(st.experimental_user, "nonce")
    else:
        frontend_logger.error("cleanup_chat_session | User nonce not found in st.experimental_user")
        st.warning("Unexpected internal error has occured. Please contact support")
        st.stop()

    success, message = end_chat(
        email=email,
        login_session_id=user_login_session_id,
        chat_session_id=chat_session_id,
        student_name=student_name
    )
    if not success:
        st.error(message)
        st.stop()
    else:
        st.session_state["active_chat_session"] = {
            "id": None,
            "chat_history": [],
            "next_questions": [],
            "recent_questions": [],
            "chat_start_timestamp": None,
            "chat_end_timestamp": None,
            "student_profile": None
        }

@st.dialog(title="Are you sure?", width="small")
def end_chat_dialog(current_chat_session: dict, student_name: str):
    if not hasattr(st.experimental_user, "email"):
        frontend_logger.error("end_chat_dialog | User email not found in st.experimental_user")
        st.warning("Unexpected internal error has occured. Please contact support")
        st.stop()

    user_email = getattr(st.experimental_user, "email")
    add_aligned_text(content=f"This will end your current chat session with {formatted_name(student_name=student_name).split(' ')[0]}.", size=16, bold=True)
    st.markdown("<br>", unsafe_allow_html=True)
    button_cols = st.columns(spec=[1,1], gap="small")

    with button_cols[0]:
        if st.button(label="Confirm", type="primary", icon=":material/check:", use_container_width=True):
            cleanup_chat_session(
                email=user_email,
                chat_session_id=current_chat_session["id"],
                student_name=student_name
            )
            st.session_state["end_chat_dialog"] = False
            st.switch_page(page="pages/home.py")
            
    with button_cols[1]:
        if st.button(label="Cancel", type="secondary", icon=":material/close:", use_container_width=True):
            st.session_state["end_chat_dialog"] = False
            st.rerun()

def render_chat_subheader(student_name):
    add_aligned_text(content=f"Chat with {student_name}", alignment="center", size=35, bold=True)

def render_chat_history(chat_history):
    for message in chat_history:
        with st.chat_message(name=message["role"], avatar=message["avatar"]):
            st.markdown(body=message["content"])

async def generate_next_questions(chat_history, student_name, num_questions=4):
    if hasattr(st.secrets, "LLM") and hasattr(st.secrets.LLM, "QUESTIONS_GENERATION_MODEL_ID") and hasattr(st.secrets.LLM, "QUESTIONS_GENERATION_MODEL_TEMPERATURE") and hasattr(st.secrets.LLM, "QUESTIONS_GENERATION_MODEL_MAX_TOKENS") and hasattr(st.secrets.LLM, "API_KEY"):
        llm = ChatGoogleGenerativeAI(
            model=st.secrets.LLM.QUESTIONS_GENERATION_MODEL_ID, 
            temperature=st.secrets.LLM.QUESTIONS_GENERATION_MODEL_TEMPERATURE,
            max_tokens=st.secrets.LLM.QUESTIONS_GENERATION_MODEL_MAX_TOKENS,
            api_key=st.secrets.LLM.API_KEY
        )
    else:
        frontend_logger.error("generate_next_questions | LLM secrets not found in st.secrets")
        st.warning("Unexpected internal error has occured. Please contact support")
        st.stop()

    formatted_history = []
    for message in chat_history:
        if message.get('role') == 'user':
            formatted_message = f"Instructor: {message.get('content', '')}"
        elif message.get('role') == 'assistant':
            formatted_message = f"Student: {message.get('content', '')}"
        formatted_history.append(formatted_message)
    formatted_history = "\n".join(formatted_history)

    if hasattr(st.experimental_user, "given_name") and hasattr(st.experimental_user, "family_name"):
        instructor_full_name = getattr(st.experimental_user, "given_name") + " " + getattr(st.experimental_user,"family_name")
    else:
        frontend_logger.error("generate_next_questions | User first name or last name not found in st.experimental_user")
        st.warning("Unexpected internal error has occured. Please contact support")
        st.stop()

    generate_next_questions_prompt = st.secrets.SYSTEM_PROMPTS.GENERATE_NEXT_QUESTIONS.format(
        instructor=instructor_full_name,
        student=student_name,
        formatted_history=formatted_history
    )
    response = await llm.ainvoke(generate_next_questions_prompt)
    generated_text = response.content.strip()

    match = re.search(r'\[.*?\]', generated_text, re.DOTALL)
    questions = ast.literal_eval(match.group(0)) if match else []

    return questions[:num_questions]

async def render_next_questions(next_questions):
    current_chat_session = st.session_state["active_chat_session"]
    student_profile = current_chat_session["student_profile"]

    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        add_aligned_text(content="You may also ask:", alignment="center", size=24, bold=True)
        st.markdown("<br>", unsafe_allow_html=True)
    for question in next_questions:
        if st.sidebar.button(label=question, use_container_width=True):
            await handle_user_input(
                user_input=question,
                current_chat_session=current_chat_session,
                student_name=student_profile["name"],
                student_avatar=student_profile["image"],
                input_type="button"
            )

async def handle_user_input(user_input: str, current_chat_session: dict, student_name: str, student_avatar: str, input_type: str):
    if hasattr(st.experimental_user, "picture"):
        user_image = getattr(st.experimental_user, "picture")
    else:
        frontend_logger.error("handle_user_input | User picture not found in st.experimental_user")
        st.warning("Unexpected internal error has occured. Please contact support")
        st.stop()
    
    if hasattr(st.experimental_user, "nonce"):
        user_login_session_id = getattr(st.experimental_user, "nonce")
    else:
        frontend_logger.error("handle_user_input | User nonce not found in st.experimental_user")
        st.warning("Unexpected internal error has occured. Please contact support")
        st.stop()

    with st.chat_message(name="user", avatar=user_image):
        st.markdown(body=user_input)

    spinner_message = f"{formatted_name(student_name=student_name).split(' ')[0]} is typing..."
    with st.spinner(spinner_message):
        success, message, answer = chat(
            login_session_id=user_login_session_id,
            chat_session_id=current_chat_session["id"],
            question=user_input,
            input_type=input_type
        )

        if not success:
            st.error(message)
            st.stop()
        
        current_chat_session["chat_history"].append({"role": "user", "content": user_input, "avatar": user_image})
        current_chat_session["chat_history"].append({"role": "assistant", "content": answer, "avatar": student_avatar})
        chat_history = current_chat_session["chat_history"]
        generated_questions = await generate_next_questions(
            chat_history=chat_history,
            student_name=student_name,
            num_questions=4
        )
        current_chat_session["next_questions"] = generated_questions
        st.rerun()

def authorize_user():
    if hasattr(st.experimental_user, "email"):
        email = getattr(st.experimental_user, "email")
        if email not in st.secrets.SECURITY.ALLOWED_EMAILS:
            frontend_logger.critical(f"authorize_user | Unauthorized user logged in: {email}")
            st.logout()
    else:
        st.switch_page(page="pages/login.py")

def authenticated():
    if getattr(st.experimental_user, "is_logged_in"):
        return True
    else:
        return False

def security_check():
    if not healthy():
        st.error("Sorry, we're facing an unexpected issue on our end. Please try again later.")
        st.stop()
    elif not authenticated():
        st.switch_page(page="pages/login.py")
    else:
        authorize_user()

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
    if "end_chat_dialog" not in st.session_state:
        st.session_state["end_chat_dialog"] = False
    if "loading_page" not in st.session_state:
        st.session_state["loading_page"] = False

if __name__ == "__main__":
    pass