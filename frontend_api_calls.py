import requests
import streamlit as st

from configure_logger import frontend_logger

backend_api_url = st.secrets.BACKEND.API_URL
backend_api_key = st.secrets.BACKEND.API_KEY

headers = {
    "X-API-Key": backend_api_key
}

def healthy() -> bool:
    response = requests.get(f"{backend_api_url}/health", headers=headers)
    return response.status_code == 200

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

def start_chat(user_first_name: str, user_last_name: str, email: str, login_session_id: str, chat_session_id: str, student_name: str) -> tuple[bool, str, str]:
    success = False
    message = ""
    data = ""
    try:
        payload = {
            "user_first_name": user_first_name,
            "user_last_name": user_last_name,
            "email": email,
            "login_session_id": login_session_id,
            "chat_session_id": chat_session_id,
            "student_name": student_name
        }
        response = requests.post(f"{backend_api_url}/start-chat", json=payload, headers=headers)

        if response.status_code == 500:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"start_chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 422:
            message = f"Invalid format for email: {email} or student name: {student_name} or login session id: {login_session_id} or chat session id: {chat_session_id} sent in the API request"
            frontend_logger.error(f"start_chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 400:
            message = f"Login session id: {login_session_id} or chat session id: {chat_session_id} already exists"
            frontend_logger.error(f"start_chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 404:
            message = f"Invalid email: {email} or student name: {student_name} sent in the API request"
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

def chat(login_session_id: str, chat_session_id: str, question: str, input_type: str, instructor_name: str, student_name: str) -> tuple[bool, str, str]:
    success = False
    message = ""
    data = ""
    
    try:
        payload = {
            "login_session_id": login_session_id,
            "chat_session_id": chat_session_id,
            "question": question,
            "input_type": input_type,
            "instructor_name": instructor_name,
            "student_name": student_name
        }
        response = requests.post(f"{backend_api_url}/chat", json=payload, headers=headers)

        if response.status_code == 500:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"chat | {message} | Response Status Code: {response.status_code}")
        elif response.status_code == 422:
            message = f"Invalid format for login session id: {login_session_id} or chat session id: {chat_session_id} or question: {question} or input type: {input_type} sent in the API request"
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

def end_chat(user_first_name: str, user_last_name: str, email: str, login_session_id: str, chat_session_id: str, student_name: str) -> tuple[bool, str]:
    success = False
    message = ""
    try:
        payload = {
            "user_first_name": user_first_name,
            "user_last_name": user_last_name,
            "email": email,
            "login_session_id": login_session_id,
            "chat_session_id": chat_session_id,
            "student_name": student_name
        }
        response = requests.post(f"{backend_api_url}/end-chat", json=payload, headers=headers)

        if response.status_code != 200:
            message = "Sorry, we're facing an unexpected issue on our end. Please try again later."
            frontend_logger.error(f"end_chat | {message} | Response Status Code: {response.status_code}")
        else:
            success = True
            message = f"Successfully ended chat for email: {email}, login session id: {login_session_id}, chat session id: {chat_session_id}, student name: {student_name}"
            frontend_logger.info(f"end_chat | {message} | Response Status Code: {response.status_code}")
    except Exception as e:
        message = str(e)
        frontend_logger.error(f"end_chat | {message} | Response Status Code: {response.status_code}")
    return success, message