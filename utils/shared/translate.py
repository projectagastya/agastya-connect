from config.shared.translate import GCP_CREDENTIALS
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from utils.shared.logger import backend_logger, frontend_logger
from typing import Optional

def get_translate_client() -> Optional[translate.Client]:
    try:
        credentials = service_account.Credentials.from_service_account_info(GCP_CREDENTIALS)
    except Exception as e:
        backend_logger.error(f"Failed to initialize credentials: {str(e)}")
        frontend_logger.error(f"Failed to initialize credentials: {str(e)}")
        return None
    return translate.Client(credentials=credentials)

def translate_text(text: str, source_language: str, target_language: str):
    if not text:
        return ""
    
    translate_client = get_translate_client()
    if not translate_client:
        backend_logger.error("Google Cloud Translation client could not be initialized. Check your credentials.")
        frontend_logger.error("Google Cloud Translation client could not be initialized. Check your credentials.")
        return ""
    
    if isinstance(text, bytes):
        text = text.decode("utf-8")
        
    result = translate_client.translate(text, source_language=source_language, target_language=target_language)
    return result["translatedText"]