import requests
import streamlit as st

from utils.shared.errors import get_user_error
from utils.shared.logger import frontend_logger

# Backend API URL and Key loaded from Streamlit secrets.
backend_api_url = st.secrets.BACKEND.API_URL
backend_api_key = st.secrets.BACKEND.API_KEY

# Headers including the API key for backend requests.
headers = {
    "X-API-Key": backend_api_key
}

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
            message = get_user_error()
            frontend_logger.error(f"get_student_profiles | Invalid count: {count} sent in the API request")
        elif response.status_code == 500:
            message = get_user_error()
            frontend_logger.error(f"get_student_profiles | Server error | Response Status Code: {response.status_code}")
        else:
            message = get_user_error()
            frontend_logger.error(f"get_student_profiles | Unknown error | Response Status Code: {response.status_code}")

    except Exception as e:
        message = get_user_error()
        frontend_logger.error(f"get_student_profiles | Error: {str(e)}")
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
            message = get_user_error()
            frontend_logger.error(f"start_chat | Server error | Response Status Code: {response.status_code}")
        elif response.status_code == 422:
            message = get_user_error()
            frontend_logger.error(f"start_chat | Invalid format for parameters sent in the API request | Response Status Code: {response.status_code}")
        elif response.status_code == 400:
            message = get_user_error()
            frontend_logger.error(f"start_chat | Login session id: {login_session_id} or chat session id: {chat_session_id} already exists | Response Status Code: {response.status_code}")
        elif response.status_code == 404:
            message = get_user_error()
            frontend_logger.error(f"start_chat | Invalid parameters sent in the API request | Response Status Code: {response.status_code}")
        else:
            success = True
            message = response.json()["message"]
            data = response.json()["data"]
            frontend_logger.info(f"start_chat | {message} | Response Status Code: {response.status_code}")
    except Exception as e:
        success = False
        message = get_user_error()
        frontend_logger.error(f"start_chat | Server error | Error: {str(e)}")
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
            message = get_user_error()
            frontend_logger.error(f"chat | Server error | Response Status Code: {response.status_code}")
        elif response.status_code == 422:
            message = get_user_error()
            frontend_logger.error(f"chat | Invalid parameters sent in the API request | Response Status Code: {response.status_code}")
        elif response.status_code == 404:
            message = get_user_error()
            frontend_logger.error(f"chat | Invalid parameters sent in the API request | Response Status Code: {response.status_code}")
        else:
            success = True
            message = response.json()["message"]
            data = response.json()["data"]
            frontend_logger.info(f"chat | {message} | Response Status Code: {response.status_code}")
    except Exception as e:
        message = get_user_error()
        frontend_logger.error(f"chat | Server error | Error: {str(e)}")
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
            message = get_user_error()
            frontend_logger.error(f"end_all_chats | Invalid parameters sent in the API request | Response Status Code: {response.status_code}")
    except Exception as e:
        message = get_user_error()
        frontend_logger.error(f"end_all_chats | Server error | Error: {str(e)}")
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
            message = get_user_error()
            frontend_logger.error(f"get_active_sessions | Server error | Response Status Code: {response.status_code}")

    except Exception as e:
        message = get_user_error()
        frontend_logger.error(f"get_active_sessions | Server error | Error: {str(e)}")
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
            message = get_user_error()
            frontend_logger.error(f"get_chat_history_messages | Server error | Response Status Code: {response.status_code}")

    except Exception as e:
        message = get_user_error()
        frontend_logger.error(f"get_chat_history_messages | Server error | Error: {str(e)}")
    return success, message, data