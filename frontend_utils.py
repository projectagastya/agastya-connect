import ast
import re
import streamlit as st

from configure_logger import frontend_logger
from datetime import datetime
from frontend_api_calls import (
    chat,
    end_chat,
    healthy,
    start_chat,
    resume_chat,
    export_chats,
    get_active_sessions,
    get_chat_history_messages,
    end_all_chats
)
from frontend_prompts import SYSTEM_PROMPT_GENERATE_NEXT_QUESTIONS, SYSTEM_PROMPT_LANGUAGE_TRANSLATION
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI
from uuid import uuid4

client = OpenAI(api_key=st.secrets.LLM.OPENAI_API_KEY)

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

    if hasattr(st.experimental_user, "email"):
        user_email = getattr(st.experimental_user, "email")
    else:
        frontend_logger.error("initialize_chat_session | User email not found in st.experimental_user")
        st.error("Sorry, we're facing an unexpected issue while setting up your chat session. Please try again later.")
        st.stop()
        
    if hasattr(st.experimental_user, "nonce"):
        login_session_id = getattr(st.experimental_user, "nonce")
    else:
        frontend_logger.error("initialize_chat_session | User nonce not found in st.experimental_user")
        st.error("Sorry, we're facing an unexpected issue while setting up your chat session. Please try again later.")
        st.stop()
    
    if hasattr(st.experimental_user, "picture"):
        user_avatar = getattr(st.experimental_user, "picture", "static/silhouette.png")
    else:
        user_avatar = "static/silhouette.png"
    
    student_name = student_choice['student_name']
    student_avatar = student_choice['student_image']
    is_resuming = st.session_state["active_chat_session"]["id"] is not None
    
    chat_session_id = st.session_state["active_chat_session"]["id"] if is_resuming else generate_uuid()
    
    st.session_state["active_chat_session"]["id"] = chat_session_id
    st.session_state["active_chat_session"]["student_profile"] = student_choice
    st.session_state["active_chat_session"]["chat_start_timestamp"] = datetime.now() if not is_resuming else st.session_state["active_chat_session"]["chat_start_timestamp"]
    
    if is_resuming:
        frontend_logger.info(f"initialize_chat_session | Resuming chat with {student_name}, session id: {chat_session_id}")
        
        resume_chat_success, resume_chat_message, _ = resume_chat(
            user_first_name=getattr(st.experimental_user, "given_name"),
            user_last_name=getattr(st.experimental_user, "family_name"),
            user_email=user_email,
            student_name=student_name,
            login_session_id=login_session_id,
            chat_session_id=chat_session_id
        )
        
        if not resume_chat_success:
            frontend_logger.error(f"initialize_chat_session | Failed to resume chat: {resume_chat_message}")
            st.error("Sorry, we're facing an unexpected issue resuming your chat. Please try again.")
            st.stop()
            
        history_success, history_message, formatted_history = get_chat_history_formatted(
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_avatar=user_avatar,
            student_avatar=student_avatar
        )
        
        if not history_success:
            frontend_logger.error(f"initialize_chat_session | Failed to get chat history: {history_message}")
            st.error("Sorry, we're facing an unexpected issue retrieving chat history. Please try again.")
            st.stop()
            
        st.session_state["active_chat_session"]["chat_history"] = formatted_history
    else:
        st.session_state["active_chat_session"]["chat_history"] = []
        
        start_chat_success, start_chat_message, first_message = start_chat(
            user_first_name=getattr(st.experimental_user, "given_name"),
            user_last_name=getattr(st.experimental_user, "family_name"),
            user_email=user_email,
            student_name=student_name,
            login_session_id=login_session_id,
            chat_session_id=chat_session_id
        )

        if not start_chat_success:
            frontend_logger.error(f"initialize_chat_session | start_chat failed: {start_chat_message}")
            st.error("Sorry, we're facing an unexpected issue while setting up your chat session. Please try again.")
            st.stop()

        st.session_state["active_chat_session"]["chat_history"].append({
            "role": "assistant", 
            "content": first_message,
            "content-en": first_message,
            "avatar": student_choice["student_image"]
        })

    st.session_state["active_chat_session"]["next_questions"] = await generate_next_questions(
        chat_history=st.session_state["active_chat_session"]["chat_history"],
        student_name=student_name
    )

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
            message = f"Failed to retrieve chat history: {history_message}"
            frontend_logger.error(f"get_chat_history_formatted | {message}")
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
        message = f"Retrieved and formatted {len(data)} messages"
        frontend_logger.info(f"get_chat_history_formatted | {message}")
    except Exception as e:
        message = str(e)
        frontend_logger.error(f"get_chat_history_formatted | {message}")
    return success, message, data

def is_kannada(text: str) -> bool:
    if text is None:
        return False
    return any('\u0c80' <= ch <= '\u0cff' for ch in text)

def cleanup_chat_session(user_email, chat_session_id, student_name):
    if hasattr(st.experimental_user, "nonce"):
        user_login_session_id = getattr(st.experimental_user, "nonce")
    else:
        frontend_logger.error("cleanup_chat_session | User nonce not found in st.experimental_user")
        st.error("Sorry, we're facing an unexpected issue while ending your chat session. Please try again later.")
        st.stop()

    success, message = end_chat(
        user_first_name=getattr(st.experimental_user, "given_name"),
        user_last_name=getattr(st.experimental_user, "family_name"),
        user_email=user_email,
        login_session_id=user_login_session_id,
        chat_session_id=chat_session_id,
        student_name=student_name
    )
    if not success:
        frontend_logger.error(f"cleanup_chat_session | end_chat failed: {message}")
        st.error("Sorry, we're facing an unexpected issue while ending your chat session. Please try again later.")
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
        st.error("Sorry, we're facing an unexpected issue on our end. Please try again later.")
        st.stop()

    user_email = getattr(st.experimental_user, "email")
    add_aligned_text(content=f"This will end your current chat session with {formatted_name(student_name=student_name).split(' ')[0]}.", size=16, bold=True)
    st.markdown("<br>", unsafe_allow_html=True)
    button_cols = st.columns(spec=[1,1], gap="small")

    with button_cols[0]:
        if st.button(label="Confirm", type="primary", icon=":material/check:", use_container_width=True):
            cleanup_chat_session(
                user_email=user_email,
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
    add_aligned_text(content=f"Chat with {formatted_name(student_name)}", alignment="center", size=35, bold=True)

def render_chat_history(chat_history):
    for message in chat_history:
        display_message = message["content"]
        
        with st.chat_message(name=message["role"], avatar=message["avatar"]):
            if display_message.strip() == "":
                display_message = "Sorry, I'm unable to provide a response at this time. Please check in again with me later. Thanks for understanding!"
                frontend_logger.warning(f"render_chat_history | Empty response received from chat message: Login Session ID: {st.experimental_user.nonce}, Chat Session ID: {st.session_state['active_chat_session']['id']}")
                st.markdown(body=display_message)
                st.error("Sorry, we're facing an unexpected issue on our end. Please try again later.")
                st.stop()
            else:
                st.markdown(body=display_message)

async def generate_next_questions(chat_history, student_name, num_questions=4):
    if hasattr(st.experimental_user, "given_name") and hasattr(st.experimental_user, "family_name"):
        user_full_name = getattr(st.experimental_user, "given_name") + " " + getattr(st.experimental_user,"family_name")
    else:
        frontend_logger.error("generate_next_questions | User first name or last name not found in st.experimental_user")
        st.error("Sorry, we're facing an unexpected issue on our end. Please try again later.")
        st.stop()

    if hasattr(st.secrets, "LLM") and hasattr(st.secrets.LLM, "QUESTIONS_GENERATION_MODEL_ID") and hasattr(st.secrets.LLM, "QUESTIONS_GENERATION_MODEL_TEMPERATURE") and hasattr(st.secrets.LLM, "QUESTIONS_GENERATION_MODEL_MAX_TOKENS") and hasattr(st.secrets.LLM, "API_KEY"):
        llm = ChatGoogleGenerativeAI(
            model=st.secrets.LLM.QUESTIONS_GENERATION_MODEL_ID, 
            temperature=st.secrets.LLM.QUESTIONS_GENERATION_MODEL_TEMPERATURE,
            max_tokens=st.secrets.LLM.QUESTIONS_GENERATION_MODEL_MAX_TOKENS,
            api_key=st.secrets.LLM.API_KEY
        )
    else:
        frontend_logger.error("generate_next_questions | LLM secrets not found in st.secrets")
        st.error("Sorry, we're facing an unexpected issue on our end. Please try again later.")
        st.stop()

    formatted_history = []
    for message in chat_history:
        if message.get('role') == 'user':
            formatted_message = f"{user_full_name}: {message.get('content-en', '')}"
        elif message.get('role') == 'assistant':
            formatted_message = f"{formatted_name(student_name)}: {message.get('content-en', '')}"
        formatted_history.append(formatted_message)
    formatted_history = "\n".join(formatted_history)

    generate_next_questions_prompt = SYSTEM_PROMPT_GENERATE_NEXT_QUESTIONS.format(
        student=formatted_name(student_name),
        formatted_history=formatted_history
    )
    response = await llm.ainvoke(generate_next_questions_prompt)
    generated_text = response.content.strip()

    match = re.search(r'\[.*?\]', generated_text, re.DOTALL)
    questions = ast.literal_eval(match.group(0)) if match else []

    return questions[:num_questions]

def translate(text: str, target_lang: str) -> str:
    direction = "English" if target_lang == "en" else "Kannada"
    prompt = f"Translate the following text to {direction}:\n\n{text}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT_LANGUAGE_TRANSLATION.format(target_lang=target_lang)
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()

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
                student_name=student_profile["student_name"],
                student_avatar=student_profile["student_image"],
                input_type="button"
            )

async def handle_user_input(user_input: str, current_chat_session: dict, student_name: str, student_avatar: str, input_type: str):
    if hasattr(st.experimental_user, "picture"):
        user_image = getattr(st.experimental_user, "picture")
    else:
        frontend_logger.error("handle_user_input | User picture not found in st.experimental_user")
        st.error("Sorry, we're facing an unexpected internal error. Please contact support")
        st.stop()
    
    if hasattr(st.experimental_user, "nonce"):
        user_login_session_id = getattr(st.experimental_user, "nonce")
    else:
        frontend_logger.error("handle_user_input | User nonce not found in st.experimental_user")
        st.error("Sorry, we're facing an unexpected internal error. Please contact support")
        st.stop()

    if hasattr(st.experimental_user, "given_name") and hasattr(st.experimental_user, "family_name"):
        user_full_name = getattr(st.experimental_user, "given_name", " ") + " " + getattr(st.experimental_user, "family_name", " ")
    else:
        frontend_logger.error("handle_user_input | User given_name or family_name not found in st.experimental_user")
        st.error("Sorry, we're facing an unexpected internal error. Please contact support")
        st.stop()

    original_question = user_input
    if input_type == "manual-kannada":
        question_for_api = translate(original_question, "en")
        with st.chat_message(name="user", avatar=user_image):
            st.markdown(body=original_question + " (Translated: " + question_for_api + ")")
    else:
        question_for_api = original_question
        with st.chat_message(name="user", avatar=user_image):
            st.markdown(body=original_question)

    spinner_message = f"{formatted_name(student_name=student_name).split(' ')[0]} is typing..."
    with st.spinner(spinner_message):
        success, message, answer = chat(
            login_session_id=user_login_session_id,
            chat_session_id=current_chat_session["id"],
            question=question_for_api,
            input_type=input_type,
            user_full_name=user_full_name,
            student_name=student_name
        )

        if not success:
            frontend_logger.error(f"handle_user_input | Getting chat response failed: {message}")
            st.error("Sorry, we're facing an unexpected issue on our end while processing your request. Please try again later.")
            st.stop()
        
        if input_type == "manual-kannada":
            answer_to_show = translate(answer, "kn")
        else:
            answer_to_show = answer
        
        if input_type == "manual-kannada":
            current_chat_session["chat_history"].append({"role": "user", "content": original_question + " (Translated: " + question_for_api + ")", "content-en": question_for_api, "avatar": user_image})
            current_chat_session["chat_history"].append({"role": "assistant", "content": answer_to_show + " (Translated: " + answer + ")", "content-en": answer, "avatar": student_avatar})
        else:
            current_chat_session["chat_history"].append({"role": "user", "content": original_question, "content-en": question_for_api, "avatar": user_image})
            current_chat_session["chat_history"].append({"role": "assistant", "content": answer_to_show, "content-en": answer, "avatar": student_avatar})
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
        user_email = getattr(st.experimental_user, "email")
        if user_email not in st.secrets.SECURITY.ALLOWED_EMAILS:
            frontend_logger.critical(f"authorize_user | Unauthorized user logged in: {user_email}")
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
        frontend_logger.error("security_check | Health check failed")
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