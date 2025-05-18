from utils.shared.env import validate_env_var, validate_int_env_var

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

# Configuration dictionary for the DynamoDB student table.
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

# Configuration dictionary for the DynamoDB chat sessions table.
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

# Configuration dictionary for the DynamoDB chat messages table.
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