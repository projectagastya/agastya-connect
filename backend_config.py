import os

from dotenv import load_dotenv

load_dotenv(dotenv_path="secrets.env")

MAIN_S3_BUCKET_NAME = os.getenv("MAIN_S3_BUCKET_NAME")
if not MAIN_S3_BUCKET_NAME or MAIN_S3_BUCKET_NAME.strip() == "" or not isinstance(MAIN_S3_BUCKET_NAME, str):
    MAIN_S3_BUCKET_NAME = "agastya-student-narratives"

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
if not AWS_DEFAULT_REGION or AWS_DEFAULT_REGION.strip() == "" or not isinstance(AWS_DEFAULT_REGION, str):
    AWS_DEFAULT_REGION = "us-east-1"

BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")

BACKEND_ORIGINS_STR = os.getenv("BACKEND_ORIGINS")
if not BACKEND_ORIGINS_STR or BACKEND_ORIGINS_STR.strip() == "" or not isinstance(BACKEND_ORIGINS_STR, str):
    BACKEND_ORIGINS = ["*"]
else:
    BACKEND_ORIGINS = BACKEND_ORIGINS_STR.split(",")

DYNAMODB_STUDENT_TABLE_BILLING_MODE = os.getenv("DYNAMODB_STUDENT_TABLE_BILLING_MODE")
if not DYNAMODB_STUDENT_TABLE_BILLING_MODE or not isinstance(DYNAMODB_STUDENT_TABLE_BILLING_MODE, str) or DYNAMODB_STUDENT_TABLE_BILLING_MODE.strip() == "" or  DYNAMODB_STUDENT_TABLE_BILLING_MODE not in ["PAY_PER_REQUEST", "PROVISIONED"]:
    DYNAMODB_STUDENT_TABLE_BILLING_MODE = "PAY_PER_REQUEST"

DYNAMODB_STUDENT_TABLE_NAME = os.getenv("DYNAMODB_STUDENT_TABLE_NAME")
if not DYNAMODB_STUDENT_TABLE_NAME or DYNAMODB_STUDENT_TABLE_NAME.strip() == "" or not isinstance(DYNAMODB_STUDENT_TABLE_NAME, str):
    DYNAMODB_STUDENT_TABLE_NAME = "student"

DYNAMODB_STUDENT_TABLE_READ_CAPACITY_STR = os.getenv("DYNAMODB_STUDENT_TABLE_READ_CAPACITY")
if not DYNAMODB_STUDENT_TABLE_READ_CAPACITY_STR or DYNAMODB_STUDENT_TABLE_READ_CAPACITY_STR.strip() == "":
    DYNAMODB_STUDENT_TABLE_READ_CAPACITY = "1"
DYNAMODB_STUDENT_TABLE_READ_CAPACITY = max(1, int(DYNAMODB_STUDENT_TABLE_READ_CAPACITY)) if DYNAMODB_STUDENT_TABLE_READ_CAPACITY.isdigit() else 1

DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY_STR = os.getenv("DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY")
if not DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY_STR or DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY_STR.strip() == "":
    DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY = "1"
DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY = max(1, int(DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY)) if DYNAMODB_STUDENT_TABLE_WRITE_CAPACITY.isdigit() else 1

DYNAMODB_STUDENT_TABLE_KEY_SCHEMA = [
    {
        'AttributeName': 'name',
        'KeyType': 'HASH'
    }
]
DYNAMODB_STUDENT_TABLE_ATTRIBUTE_DEFINITIONS = [
    {
        'AttributeName': 'name',
        'AttributeType': 'S'
    }
]
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

DYNAMODB_CHAT_SESSIONS_TABLE_NAME = os.getenv("DYNAMODB_CHAT_SESSIONS_TABLE_NAME", "chat-sessions")
DYNAMODB_CHAT_SESSIONS_TABLE_CONFIG = {
    'TableName': DYNAMODB_CHAT_SESSIONS_TABLE_NAME,
    'KeySchema': [
        {'AttributeName': 'session_id', 'KeyType': 'HASH'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'session_id', 'AttributeType': 'S'},
        {'AttributeName': 'instructor_email', 'AttributeType': 'S'},
        {'AttributeName': 'student_name', 'AttributeType': 'S'},
        {'AttributeName': 'last_updated_at', 'AttributeType': 'S'},
        {'AttributeName': 'created_at', 'AttributeType': 'S'},
        {'AttributeName': 'login_session_id', 'AttributeType': 'S'}
    ],
    'GlobalSecondaryIndexes': [
        {
            'IndexName': 'InstructorSessionsIndex',
            'KeySchema': [
                {'AttributeName': 'instructor_email', 'KeyType': 'HASH'},
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
                {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }
    ],
    'BillingMode': 'PAY_PER_REQUEST'
}

DYNAMODB_CHAT_MESSAGES_TABLE_NAME = os.getenv("DYNAMODB_CHAT_MESSAGES_TABLE_NAME", "chat-messages")
DYNAMODB_CHAT_MESSAGES_TABLE_CONFIG = {
    'TableName': DYNAMODB_CHAT_MESSAGES_TABLE_NAME,
    'KeySchema': [
        {'AttributeName': 'session_id', 'KeyType': 'HASH'},
        {'AttributeName': 'message_timestamp', 'KeyType': 'RANGE'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'session_id', 'AttributeType': 'S'},
        {'AttributeName': 'message_timestamp', 'AttributeType': 'S'}
    ],
    'BillingMode': 'PAY_PER_REQUEST'
}

LOGS_FOLDER_PATH = os.getenv("LOGS_FOLDER_PATH")
if not LOGS_FOLDER_PATH or LOGS_FOLDER_PATH.strip() == "" or not isinstance(LOGS_FOLDER_PATH, str):
    LOGS_FOLDER_PATH = "logs"

MAX_DOCS_TO_RETRIEVE = int(os.getenv("RAG_MAX_DOC_RETRIEVE", "4"))

TEMPORARY_VECTORSTORES_DIRECTORY = os.getenv("TEMPORARY_VECTORSTORES_DIRECTORY", "temporary-student-vectorstores")

DOCUMENT_EMBEDDING_MODEL_ID = os.getenv("DOCUMENT_EMBEDDING_MODEL_ID", "models/text-embedding-004")

RESPONSE_GENERATION_MODEL_ID = os.getenv("RESPONSE_GENERATION_MODEL_ID", "gemini-2.0-flash")
RESPONSE_GENERATION_MODEL_TEMPERATURE = float(os.getenv("RESPONSE_GENERATION_MODEL_TEMPERATURE", "0.0"))
RESPONSE_GENERATION_MODEL_MAX_TOKENS = int(os.getenv("RESPONSE_GENERATION_MODEL_MAX_TOKENS", "100"))

STUDENT_METADATA_FILE_NAME = os.getenv("STUDENT_METADATA_FILE_NAME")
STUDENT_METADATA_FOLDER_PATH = os.getenv("STUDENT_METADATA_FOLDER_PATH")

STUDENT_VECTORSTORE_FOLDER_PATH = os.getenv("STUDENT_VECTORSTORE_FOLDER_PATH", "vectorstores")