import ast
import os
import re
import streamlit as st

from api_calls import delete_session_document, upload_session_document
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from time import sleep
from session_database import insert_chat_history
from uuid import uuid4

load_dotenv()

def validate_credentials(username, password):
    auth_username = os.getenv("AUTH_USERNAME")
    auth_password = os.getenv("AUTH_PASSWORD")

    st.write()
    return username == auth_username and password == auth_password

def switch_page(page_name):
    sleep(0.1)
    st.session_state.current_page = page_name
    st.rerun()

def generate_uuid():
    new_uuid = str(uuid4())
    return new_uuid

def logout_and_redirect():
    end_login_session()
    switch_page("login")

def add_aligned_text(content, alignment="left", size=1):
    st.markdown(body=f"<div style='text-align: {alignment}; font-size: {size}rem;'><strong>{content}</strong></div>", unsafe_allow_html=True)
    
def add_student():
    switch_page("add_student")

def format_chat_history_for_openai(chat_history):
    formatted_history = []
    for message in chat_history:
        if message.get('role') == 'user':
            formatted_message = f"Instructor: {message.get('content', '')}"
        elif message.get('role') == 'assistant':
            formatted_message = f"Student: {message.get('content', '')}"
        formatted_history.append(formatted_message)

    return "\n".join(formatted_history)

async def generate_questions_with_openai(chat_history, num_questions=4):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, max_tokens=800)

    formatted_history = format_chat_history_for_openai(chat_history=chat_history)

    messages = [
            SystemMessage(
                content=f"""
                You are an expert conversational AI with a strong purpose to assist instructors in asking thoughtful, context-aware, and creative questions, to their students.
                
                Read the following chat history, line by line, thoroughly and help the instructor ask engaging questions to the student.

                Chat history between instructor and student: ```{formatted_history}```

                You must follow these instructions, carefully:

                - Generate EXACTLY 4 semantically unique, highly creative, and engaging questions for the instructor to ask the child.
                - The questions must be strictly related to the chat history and must be asked out of curiosity, for a meaningful dialogue.
                - If the chat history is empty, return 4 unique introductory questions that are friendly and open-ended.
                - Avoid questions that are personal, controversial, repetitive, or unrelated to the topic of the chat history.
                - Prioritize questions that encourage the child to reflect on their experiences, passions, and interactions with other students/instructors at Agastya International Foundation.
                - Ensure the tone of the questions is warm, child-friendly, and encouraging, fostering a safe space for dialogue.
                - Aim for questions that are clear, concise, and use simple language suitable for children.

                Take a moment to think deeply about the chat history, and then, compose questions that will add more value to the conversation.

                Respond ONLY with a Python list in this format: ["Question 1", "Question 2", "Question 3", "Question 4"].
                """
            )
        ]
    response = llm.invoke(messages)
    generated_text = response.content.strip()

    match = re.search(r'\[.*?\]', generated_text, re.DOTALL)
    questions = ast.literal_eval(match.group(0)) if match else []

    return questions[:num_questions]

def initialize_chat_history(current_chat_session, student_name, student_avatar):
    if not current_chat_session["chat_history"]:
        default_message = {
            "role": "assistant",
            "content": f"Hi, I'm {student_name} from Agastya International Foundation. What would you like to know about me?",
            "avatar": student_avatar,
        }
        current_chat_session["chat_history"].append(default_message)

async def initialize_chat_session(student_profile: dict):
    new_chat_session = {
        "chat_session_id": generate_uuid(),
        "chat_start_timestamp": datetime.now(),
        "chat_end_timestamp": None,
        "selected_student": student_profile,
        "confirm_end_chat": None,
        "chat_history": [],
        "next_questions": [],
        "recent_questions": []
    }
    st.session_state["login_sessions"]["chat_sessions"].append(new_chat_session)
    st.session_state["login_sessions"]["active_chat_session"] = new_chat_session["chat_session_id"]

    document_name = student_profile['name'].lower().replace(" ", "-")
    document_path = f"information/{document_name}.docx"

    upload_session_document(chat_session_id=new_chat_session["chat_session_id"], file_path=document_path)

    insert_chat_history(
        chat_session_id=new_chat_session["chat_session_id"],
        user_input="Hello, I'm here to chat with you",
        ai_output=f"Hi, I'm {student_profile['name']} from Agastya International Foundation. What would you like to know about me?",
    )

    initial_questions = await generate_questions_with_openai(new_chat_session["chat_history"])
    new_chat_session["next_questions"] = initial_questions
    initialize_chat_history(current_chat_session=new_chat_session, student_name=student_profile["name"], student_avatar=student_profile["image"])

def end_login_session():
    for key in st.session_state:
        st.session_state.pop(key, default=None)

def end_chat_session(chat_session_id):
    delete_session_document(chat_session_id=chat_session_id)

def handle_end_chat_confirmation(current_chat_session):
    st.warning("Are you sure you want to end the current chat session?")
    cols = st.columns(9, gap="small")

    with cols[0]:
        if st.button("Confirm", use_container_width=True):
            current_chat_session["chat_end_timestamp"] = datetime.now()
            redirection_target = current_chat_session["confirm_end_chat"]
            st.session_state['login_sessions']["active_chat_session"] = None
            current_chat_session["confirm_end_chat"] = None
            switch_page(redirection_target)

    with cols[1]:
        if st.button("Cancel", type="primary", use_container_width=True):
            current_chat_session["confirm_end_chat"] = None
            st.rerun()