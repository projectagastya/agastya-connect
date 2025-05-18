import requests
import streamlit as st

from utils.shared.logger import frontend_logger

# Backend API URL and Key loaded from Streamlit secrets.
backend_api_url = st.secrets.BACKEND.API_URL
backend_api_key = st.secrets.BACKEND.API_KEY

# Headers including the API key for backend requests.
headers = {
    "X-API-Key": backend_api_key
}

# Function to check the health of the backend API.
def healthy() -> bool:
    response = requests.get(f"{backend_api_url}/health", headers=headers)
    return response.status_code == 200

# Function to fetch student profiles from the backend API (/get-student-profiles).
@st.cache_resource(ttl=3600, show_spinner=False)
def get_student_profiles(count: int) -> tuple[bool, str, list]:
    success = False
    message = ""
    data = []
    try:
        payload = {
            "count": count
        }
        response = requests.post(f"{backend_api_url}/get-student-profiles", json=payload, headers=headers)

        if response.status_code == 200:
            success = True
            message = response.json()["message"]
            data = response.json()["data"]
            frontend_logger.info(f"get_student_profiles | {message}")
        elif response.status_code == 422:
            message = f"Invalid count: {count} sent in the API request"
            frontend_logger.error(f"get_student_profiles | {message}")
        elif response.status_code == 500:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"get_student_profiles | {message}")
        else:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"get_student_profiles | {message}")

    except Exception as e:
        message = str(e)
        frontend_logger.error(f"get_student_profiles | {message}")
    return success, message, data

# Function to initialize a new chat session via the backend API (/start-chat).
def start_chat(user_first_name: str, user_last_name: str, user_email: str, login_session_id: str, chat_session_id: str, student_name: str) -> tuple[bool, str, str]:
    success = False
    message = ""
    data = ""
    try:
        payload = {
            "user_first_name": user_first_name,
            "user_last_name": user_last_name,
            "user_email": user_email,
            "login_session_id": login_session_id,
            "chat_session_id": chat_session_id,
            "student_name": student_name
        }
        response = requests.post(f"{backend_api_url}/start-chat", json=payload, headers=headers)

        if response.status_code == 500:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"start_chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 422:
            message = f"Invalid format for email: {user_email} or student name: {student_name} or login session id: {login_session_id} or chat session id: {chat_session_id} sent in the API request"
            frontend_logger.error(f"start_chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 400:
            message = f"Login session id: {login_session_id} or chat session id: {chat_session_id} already exists"
            frontend_logger.error(f"start_chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 404:
            message = f"Invalid email: {user_email} or student name: {student_name} sent in the API request"
            frontend_logger.error(f"start_chat | {message} | Response Status Code: {response.status_code}")
        else:
            success = True
            message = response.json()["message"]
            data = response.json()["data"]
            frontend_logger.info(f"start_chat | {message} | Response Status Code: {response.status_code}")
    except Exception as e:
        success = False
        message = str(e)
        frontend_logger.error(f"start_chat | {message} | Response Status Code: {response.status_code}")
    return success, message, data

# Function to send a chat message and get a response from the backend API (/chat).
def chat(login_session_id: str, chat_session_id: str, question: str, question_kannada: str | None, input_type: str, user_full_name: str, student_name: str) -> tuple[bool, str, str]:
    success = False
    message = ""
    data = ""
    
    try:
        payload = {
            "login_session_id": login_session_id,
            "chat_session_id": chat_session_id,
            "question": question,
            "question_kannada": question_kannada,
            "input_type": input_type,
            "user_full_name": user_full_name,
            "student_name": student_name
        }
        response = requests.post(f"{backend_api_url}/chat", json=payload, headers=headers)

        if response.status_code == 500:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 422:
            message = f"Invalid format for login session id: {login_session_id} or chat session id: {chat_session_id} or question: {question} or question in Kannada: {question_kannada} or input type: {input_type} sent in the API request"
            frontend_logger.error(f"chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 404:
            message = f"Invalid login session id: {login_session_id} or chat session id: {chat_session_id} sent in the API request or chat history not found"
            frontend_logger.error(f"chat | {message} | Response Status Code: {response.status_code}")
        else:
            success = True
            message = response.json()["message"]
            data = response.json()["data"]
            frontend_logger.info(f"chat | {message} | Response Status Code: {response.status_code}")
    except Exception as e:
        message = str(e)
        frontend_logger.error(f"chat | {message}")
    return success, message, data

# Function to resume an existing chat session via the backend API (/resume-chat).
def resume_chat(user_first_name: str, user_last_name: str, user_email: str, login_session_id: str, chat_session_id: str, student_name: str) -> tuple[bool, str, str]:
    success = False
    message = ""
    data = ""
    try:
        payload = {
            "user_first_name": user_first_name,
            "user_last_name": user_last_name,
            "user_email": user_email,
            "login_session_id": login_session_id,
            "chat_session_id": chat_session_id,
            "student_name": student_name
        }
        response = requests.post(f"{backend_api_url}/resume-chat", json=payload, headers=headers)

        if response.status_code == 500:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"resume_chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 422:
            message = f"Invalid format for email: {user_email} or student name: {student_name} or login session id: {login_session_id} or chat session id: {chat_session_id} sent in the API request"
            frontend_logger.error(f"resume_chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 404:
            message = f"Invalid email: {user_email} or student name: {student_name} sent in the API request"
            frontend_logger.error(f"resume_chat | {message} | Response Status Code: {response.status_code}")
        else:
            success = True
            message = response.json()["message"]
            data = response.json().get("data", "")
            frontend_logger.info(f"resume_chat | {message} | Response Status Code: {response.status_code}")
    except Exception as e:
        success = False
        message = str(e)
        frontend_logger.error(f"resume_chat | {message}")
    return success, message, data

# Function to end all active chat sessions for a user login via the backend API (/end-all-chats).
def end_all_chats(user_email: str, login_session_id: str) -> tuple[bool, str]:
    success = False
    message = ""
    try:
        payload = {
            "user_email": user_email,
            "login_session_id": login_session_id
        }
        response = requests.post(f"{backend_api_url}/end-all-chats", json=payload, headers=headers)

        if response.status_code == 200:
            success = True
            message = "Successfully ended all active chat sessions"
            frontend_logger.info(f"end_all_chats | {message}")
        else:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"end_all_chats | {message} | Response Status Code: {response.status_code}")
    except Exception as e:
        message = str(e)
        frontend_logger.error(f"end_all_chats | {message}")
    return success, message

# Function to retrieve active chat sessions for a user login from the backend API (/get-active-sessions).
@st.cache_resource(ttl=300, show_spinner=False)
def get_active_sessions(user_email: str, login_session_id: str) -> tuple[bool, str, list]:
    success = False
    message = ""
    data = []
    try:
        payload = {
            "user_email": user_email,
            "login_session_id": login_session_id
        }
        response = requests.post(f"{backend_api_url}/get-active-sessions", json=payload, headers=headers)

        if response.status_code == 200:
            success = True
            message = response.json()["message"]
            data = response.json()["data"]
            frontend_logger.info(f"get_active_sessions | {message}")
        else:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"get_active_sessions | {message} | Response Status Code: {response.status_code}")

    except Exception as e:
        message = str(e)
        frontend_logger.error(f"get_active_sessions | {message}")
    return success, message, data

# Function to get the chat history messages for a specific session from the backend API (/get-chat-history).
def get_chat_history_messages(login_session_id: str, chat_session_id: str) -> tuple[bool, str, list]:
    success = False
    message = ""
    data = []
    try:
        payload = {
            "login_session_id": login_session_id,
            "chat_session_id": chat_session_id
        }
        response = requests.post(f"{backend_api_url}/get-chat-history", json=payload, headers=headers)

        if response.status_code == 200:
            success = True
            message = response.json()["message"]
            data = response.json()["data"]
            frontend_logger.info(f"get_chat_history_messages | {message}")
        else:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"get_chat_history_messages | {message} | Response Status Code: {response.status_code}")

    except Exception as e:
        message = str(e)
        frontend_logger.error(f"get_chat_history_messages | {message}")
    return success, message, data