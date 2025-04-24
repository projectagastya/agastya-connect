import os
import json
from typing import Optional

from dotenv import load_dotenv
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from shared.logger import backend_logger, frontend_logger

load_dotenv()

def get_translate_client() -> Optional[translate.Client]:
    GCP_TYPE = os.getenv("GCP_TYPE")
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_PRIVATE_KEY_ID = os.getenv("GCP_PRIVATE_KEY_ID")
    GCP_PRIVATE_KEY = os.getenv("GCP_PRIVATE_KEY")
    GCP_CLIENT_EMAIL = os.getenv("GCP_CLIENT_EMAIL")
    GCP_CLIENT_ID = os.getenv("GCP_CLIENT_ID")
    GCP_AUTH_URI = os.getenv("GCP_AUTH_URI")
    GCP_TOKEN_URI = os.getenv("GCP_TOKEN_URI")
    GCP_AUTH_PROVIDER_X509_CERT_URL = os.getenv("GCP_AUTH_PROVIDER_X509_CERT_URL")
    GCP_CLIENT_X509_CERT_URL = os.getenv("GCP_CLIENT_X509_CERT_URL")
    GCP_UNIVERSE_DOMAIN = os.getenv("GCP_UNIVERSE_DOMAIN")
    
    credentials_dict = {
        "type": GCP_TYPE,
        "project_id": GCP_PROJECT_ID,
        "private_key_id": GCP_PRIVATE_KEY_ID,
        "private_key": GCP_PRIVATE_KEY,
        "client_email": GCP_CLIENT_EMAIL,
        "client_id": GCP_CLIENT_ID,
        "auth_uri": GCP_AUTH_URI,
        "token_uri": GCP_TOKEN_URI,
        "auth_provider_x509_cert_url": GCP_AUTH_PROVIDER_X509_CERT_URL,
        "client_x509_cert_url": GCP_CLIENT_X509_CERT_URL,
        "universe_domain": GCP_UNIVERSE_DOMAIN
    }
    try:
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    except Exception as e:
        backend_logger.error(f"Failed to initialize credentials: {str(e)}")
        frontend_logger.error(f"Failed to initialize credentials: {str(e)}")
        return None
    return translate.Client(credentials=credentials)

def translate_kannada_to_english(text):
    if not text:
        return ""
    
    translate_client = get_translate_client()
    if not translate_client:
        backend_logger.error("Google Cloud Translation client could not be initialized. Check your credentials.")
        frontend_logger.error("Google Cloud Translation client could not be initialized. Check your credentials.")
        return ""
    
    if isinstance(text, bytes):
        text = text.decode("utf-8")
        
    result = translate_client.translate(text, source_language="kn", target_language="en")
    return result["translatedText"]

def translate_english_to_kannada(text):
    if not text:
        return ""
    
    translate_client = get_translate_client()
    if not translate_client:
        backend_logger.error("Google Cloud Translation client could not be initialized. Check your credentials.")
        frontend_logger.error("Google Cloud Translation client could not be initialized. Check your credentials.")
        return ""
    
    if isinstance(text, bytes):
        text = text.decode("utf-8")
        
    result = translate_client.translate(text, source_language="en", target_language="kn")
    return result["translatedText"]