import os
import requests
import streamlit as st

from dotenv import load_dotenv

load_dotenv()

model = os.getenv('GENERATION_MODEL_ID', "gpt-4o-mini")
app_url = os.getenv("APPLICATION_URL", "http://localhost:8000")

def get_api_response(question, chat_session_id):
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = {"question": question, "model": model, "chat_session_id": chat_session_id}
    response = requests.post(f"{app_url}/chat", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API request failed with status code {response.status_code}.")
        return None
    
def upload_session_document(chat_session_id: str, file_path: str):
    with open(file_path, "rb") as file:
        files = {"file": (os.path.basename(file_path), file, "application/octet-stream")}
        response = requests.post(f"{app_url}/upload-session-doc", params={"chat_session_id": chat_session_id}, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text, "status_code": response.status_code}

def list_session_document(chat_session_id: str):
    response = requests.get(f"{app_url}/list-session-doc", params={"chat_session_id": chat_session_id})
    if response.status_code == 200:
        return response.json()
    else:
        return []

def delete_session_document(chat_session_id):
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = {"chat_session_id": chat_session_id}
    response = requests.post(f"{app_url}/delete-session-doc", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to delete document. Error: {response.status_code} - {response.text}")
        return None