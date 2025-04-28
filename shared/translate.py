from typing import Optional

from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from shared.config import GCP_CREDENTIALS
from shared.logger import backend_logger, frontend_logger

def get_translate_client() -> Optional[translate.Client]:
    try:
        credentials = service_account.Credentials.from_service_account_info(GCP_CREDENTIALS)
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