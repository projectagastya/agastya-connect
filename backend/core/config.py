import os

from dotenv import load_dotenv
from shared.logger import backend_logger

load_dotenv()

def validate_env_var(var_name: str, required: bool = True, default: str = None, allowed_values: list = None) -> str:
    value = os.getenv(var_name)
    if not value or value.strip() == "" or not isinstance(value, str):
        if required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return default
    if allowed_values and value not in allowed_values:
        return default
    return value

def validate_int_env_var(var_name: str, required: bool = True, default: int = None) -> int:
    value = os.getenv(var_name)
    try:
        int_value = int(value)
        if not int_value and required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return int_value
    except (ValueError, TypeError):
        if required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return default

def validate_float_env_var(var_name: str, required: bool = True, default: float = None) -> float:
    value = os.getenv(var_name)
    try:
        float_value = float(value)
        if not float_value and required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return float_value
    except (ValueError, TypeError):
        if required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return default

MAIN_S3_BUCKET_NAME = validate_env_var("MAIN_S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = validate_env_var("AWS_ACCESS_KEY_ID") 
AWS_SECRET_ACCESS_KEY = validate_env_var("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = validate_env_var("AWS_DEFAULT_REGION")
AWS_REGION = validate_env_var("AWS_REGION", required=False, default=AWS_DEFAULT_REGION)

BACKEND_API_KEY = validate_env_var("BACKEND_API_KEY")
BACKEND_ORIGINS_STR = validate_env_var("BACKEND_ORIGINS", required=False)
BACKEND_ORIGINS = BACKEND_ORIGINS_STR.split(",") if BACKEND_ORIGINS_STR else ["*"]

CHAT_TRANSCRIPTS_FOLDER_PATH = validate_env_var("CHAT_TRANSCRIPTS_FOLDER_PATH")
DYNAMODB_STUDENT_TABLE_BILLING_MODE = validate_env_var(
    "DYNAMODB_STUDENT_TABLE_BILLING_MODE", 
    required=False,
    default="PAY_PER_REQUEST",
    allowed_values=["PAY_PER_REQUEST", "PROVISIONED"]
)
DYNAMODB_STUDENT_TABLE_NAME = validate_env_var("DYNAMODB_STUDENT_TABLE_NAME")
DYNAMODB_STUDENT_TABLE_READ_CAPACITY = max(1, validate_int_env_var("DYNAMODB_STUDENT_TABLE_READ_CAPACITY", required=False, default=1))
DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY = max(1, validate_int_env_var("DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY", required=False, default=1))

DYNAMODB_STUDENT_TABLE_KEY_SCHEMA = [{'AttributeName': 'student_name', 'KeyType': 'HASH'}]
DYNAMODB_STUDENT_TABLE_ATTRIBUTE_DEFINITIONS = [{'AttributeName': 'student_name', 'AttributeType': 'S'}]

DYNAMODB_STUDENT_TABLE_CONFIG = {
    'TableName': DYNAMODB_STUDENT_TABLE_NAME,
    'KeySchema': DYNAMODB_STUDENT_TABLE_KEY_SCHEMA,
    'AttributeDefinitions': DYNAMODB_STUDENT_TABLE_ATTRIBUTE_DEFINITIONS,
    'BillingMode': DYNAMODB_STUDENT_TABLE_BILLING_MODE
}

if DYNAMODB_STUDENT_TABLE_BILLING_MODE == "PROVISIONED":
    DYNAMODB_STUDENT_TABLE_CONFIG['ProvisionedThroughput'] = {
        'ReadCapacityUnits': DYNAMODB_STUDENT_TABLE_READ_CAPACITY,
        'WriteCapacityUnits': DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY
    }

DYNAMODB_CHAT_SESSIONS_TABLE_NAME = validate_env_var("DYNAMODB_CHAT_SESSIONS_TABLE_NAME")
DYNAMODB_CHAT_SESSIONS_TABLE_CONFIG = {
    'TableName': DYNAMODB_CHAT_SESSIONS_TABLE_NAME,
    'KeySchema': [
        {'AttributeName': 'global_session_id', 'KeyType': 'HASH'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'global_session_id', 'AttributeType': 'S'},
        {'AttributeName': 'user_email', 'AttributeType': 'S'},
        {'AttributeName': 'student_name', 'AttributeType': 'S'},
        {'AttributeName': 'last_updated_at', 'AttributeType': 'S'},
        {'AttributeName': 'started_at', 'AttributeType': 'S'},
        {'AttributeName': 'login_session_id', 'AttributeType': 'S'}
    ],
    'GlobalSecondaryIndexes': [
        {
            'IndexName': 'UserSessionsIndex',
            'KeySchema': [
                {'AttributeName': 'user_email', 'KeyType': 'HASH'},
                {'AttributeName': 'last_updated_at', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        },
        {
            'IndexName': 'StudentSessionsIndex',
            'KeySchema': [
                {'AttributeName': 'student_name', 'KeyType': 'HASH'},
                {'AttributeName': 'last_updated_at', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        },
        {
            'IndexName': 'LoginSessionIndex',
            'KeySchema': [
                {'AttributeName': 'login_session_id', 'KeyType': 'HASH'},
                {'AttributeName': 'started_at', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }
    ],
    'BillingMode': 'PAY_PER_REQUEST'
}

DYNAMODB_CHAT_MESSAGES_TABLE_NAME = validate_env_var("DYNAMODB_CHAT_MESSAGES_TABLE_NAME")
DYNAMODB_CHAT_MESSAGES_TABLE_CONFIG = {
    'TableName': DYNAMODB_CHAT_MESSAGES_TABLE_NAME,
    'KeySchema': [
        {'AttributeName': 'global_session_id', 'KeyType': 'HASH'},
        {'AttributeName': 'message_timestamp', 'KeyType': 'RANGE'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'global_session_id', 'AttributeType': 'S'},
        {'AttributeName': 'message_timestamp', 'AttributeType': 'S'}
    ],
    'BillingMode': 'PAY_PER_REQUEST'
}

GCP_TYPE = validate_env_var("GCP_TYPE")
GCP_PROJECT_ID = validate_env_var("GCP_PROJECT_ID")
GCP_PRIVATE_KEY_ID = validate_env_var("GCP_PRIVATE_KEY_ID")
GCP_PRIVATE_KEY = validate_env_var("GCP_PRIVATE_KEY")
GCP_CLIENT_EMAIL = validate_env_var("GCP_CLIENT_EMAIL")
GCP_CLIENT_ID = validate_env_var("GCP_CLIENT_ID")
GCP_AUTH_URI = validate_env_var("GCP_AUTH_URI")
GCP_TOKEN_URI = validate_env_var("GCP_TOKEN_URI")
GCP_AUTH_PROVIDER_X509_CERT_URL = validate_env_var("GCP_AUTH_PROVIDER_X509_CERT_URL")
GCP_CLIENT_X509_CERT_URL = validate_env_var("GCP_CLIENT_X509_CERT_URL")
GCP_UNIVERSE_DOMAIN = validate_env_var("GCP_UNIVERSE_DOMAIN")

GCP_CREDENTIALS = {
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

LOGS_FOLDER_PATH = validate_env_var("LOGS_FOLDER_PATH")
MAX_DOCS_TO_RETRIEVE = validate_int_env_var("RAG_MAX_DOC_RETRIEVE")
LOCAL_VECTORSTORES_DIRECTORY = validate_env_var("LOCAL_VECTORSTORES_DIRECTORY")
DOCUMENT_EMBEDDING_MODEL_ID = validate_env_var("DOCUMENT_EMBEDDING_MODEL_ID")
RESPONSE_GENERATION_MODEL_ID = validate_env_var("RESPONSE_GENERATION_MODEL_ID")
RESPONSE_GENERATION_MODEL_TEMPERATURE = validate_float_env_var("RESPONSE_GENERATION_MODEL_TEMPERATURE")
RESPONSE_GENERATION_MODEL_MAX_TOKENS = validate_int_env_var("RESPONSE_GENERATION_MODEL_MAX_TOKENS")
STUDENT_METADATA_FILE_NAME = validate_env_var("STUDENT_METADATA_FILE_NAME")
STUDENT_METADATA_FOLDER_PATH = validate_env_var("STUDENT_METADATA_FOLDER_PATH")
STUDENT_VECTORSTORE_FOLDER_PATH = validate_env_var("STUDENT_VECTORSTORE_FOLDER_PATH")