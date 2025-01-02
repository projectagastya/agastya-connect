import os
import pytz
import re
import streamlit as st

from api_calls import delete_session_document, upload_session_document
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from session_database import insert_chat_history
from uuid import uuid4

load_dotenv()
embedding_function = OpenAIEmbeddings()
timezone = pytz.timezone(os.getenv("TIMEZONE", "US/Central"))

def validate_credentials(username, password):
    auth_username = os.getenv("AUTH_USERNAME")
    auth_password = os.getenv("AUTH_PASSWORD")

    st.write()
    return username == auth_username and password == auth_password

def switch_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def generate_uuid():
    new_uuid = str(uuid4())
    return new_uuid

def logout_and_redirect():
    end_login_session()
    switch_page("login")

def add_student():
    switch_page("add_student")

def format_chat_history_for_openai(chat_history):
    return [
        HumanMessage(content=item["content"]) if item["role"] == "user" else AIMessage(content=item["content"])
        for item in chat_history
    ]

def generate_questions_with_openai(chat_history, num_questions=4):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=800)

    formatted_history = format_chat_history_for_openai(chat_history=chat_history)
    
    messages = [
        SystemMessage(
            content=f"""Read the following chat history line by line thoroughly.
                            
                        Chat history: ```{formatted_history}```

                        Follow these instructions:

                        - Generate EXACTLY 4 semantically distinct, context-aware questions using minimal words, that are appropriate to be posed to a child.
                        - The questions must be new and relevant to the chat history to build a fruitful conversation.
                        - If the chat history is empty, generate introductory questions by following all instructions
                        - Ignore irrelevant questions that diverge from the topic.
                        - Focus on asking questions about the student and their experience with Agastya International Foundation and their interests, passions, learnings etc.
                        - Avoid personal, controversial, or repetitive questions.
                        - Be mindful of the tone of the question as it is posed to a child.
                        - Take a deep breath and think step by step

                        Respond ONLY with a Python list in this format: ["question1", "question2", "question3", "question4"].
                    """
        )
    ]

    response = llm.invoke(messages)
    generated_text = response.content.strip()

    match = re.search(r'\[.*?\]', generated_text, re.DOTALL)
    questions = eval(match.group(0)) if match else []

    return questions[:num_questions]

def initialize_chat_history(current_chat_session, student_name, student_avatar):
    if not current_chat_session["chat_history"]:
        default_message = {
            "role": "assistant",
            "content": f"Hi, I'm {student_name} from Agastya International Foundation. What would you like to know about me?",
            "avatar": student_avatar,
        }
        current_chat_session["chat_history"].append(default_message)

def initialize_chat_session(student_profile: dict):
    new_chat_session = {
        "chat_session_id": generate_uuid(),
        "chat_start_timestamp": datetime.now(),
        "chat_end_timestamp": None,
        "selected_student": student_profile,
        "confirm_end_chat": None,
        "chat_history": [],
        "refresh_questions": True,
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

    initial_questions = generate_questions_with_openai(new_chat_session["chat_history"])
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