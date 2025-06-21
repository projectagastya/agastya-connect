import boto3
import json
import os

from botocore.exceptions import ClientError
from datetime import datetime, timezone, timedelta
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from typing import Tuple, Optional

# Environment variables
CHAT_SESSIONS_TABLE_NAME = os.environ['CHAT_SESSIONS_TABLE_NAME']
CHAT_MESSAGES_TABLE_NAME = os.environ['CHAT_MESSAGES_TABLE_NAME']

# Google Cloud Translation credentials from environment variables
GCP_CREDENTIALS = {
    "type": os.environ.get('GCP_TYPE', 'service_account'),
    "project_id": os.environ.get('GCP_PROJECT_ID'),
    "private_key_id": os.environ.get('GCP_PRIVATE_KEY_ID'),
    "private_key": os.environ.get('GCP_PRIVATE_KEY', '').replace('\\n', '\n'),  # Handle newlines in private key
    "client_email": os.environ.get('GCP_CLIENT_EMAIL'),
    "client_id": os.environ.get('GCP_CLIENT_ID'),
    "auth_uri": os.environ.get('GCP_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
    "token_uri": os.environ.get('GCP_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
    "auth_provider_x509_cert_url": os.environ.get('GCP_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
    "client_x509_cert_url": os.environ.get('GCP_CLIENT_X509_CERT_URL'),
    "universe_domain": os.environ.get('GCP_UNIVERSE_DOMAIN', 'googleapis.com')
}

def get_translate_client() -> Optional[translate.Client]:
    """Initialize Google Cloud Translation client."""
    try:
        # Skip translation if credentials are not configured
        if not GCP_CREDENTIALS.get('project_id') or not GCP_CREDENTIALS.get('private_key'):
            print("Google Cloud Translation credentials not configured. Skipping translation.")
            return None
            
        credentials = service_account.Credentials.from_service_account_info(GCP_CREDENTIALS)
        return translate.Client(credentials=credentials)
    except Exception as e:
        print(f"Failed to initialize translation client: {str(e)}")
        return None

def translate_text(text: str, source_language: str, target_language: str) -> str:
    """Translate text from source language to target language."""
    if not text:
        return ""
    
    translate_client = get_translate_client()
    if not translate_client:
        print("Translation client not available. Returning empty string.")
        return ""
    
    try:
        if isinstance(text, bytes):
            text = text.decode("utf-8")
            
        result = translate_client.translate(text, source_language=source_language, target_language=target_language)
        return result["translatedText"]
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return ""

def formatted(text: str) -> str:
    """Format text by replacing hyphens with spaces and title casing."""
    return text.replace('-', ' ').title()

def initialize_chat_session(user_email: str, login_session_id: str, chat_session_id: str, 
                          user_first_name: str, user_last_name: str, student_name: str) -> Tuple[bool, str]:
    """Initialize a new chat session in DynamoDB."""
    success = False
    message = ""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(CHAT_SESSIONS_TABLE_NAME)
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        now = datetime.now(timezone.utc).isoformat()
        
        table.put_item(
            Item={
                'global_session_id': global_session_id,
                'login_session_id': login_session_id,
                'chat_session_id': chat_session_id,
                'user_email': user_email,
                'user_full_name': f"{user_first_name} {user_last_name}",
                'student_name': student_name,
                'session_status': 'active',
                'started_at': now,
                'last_updated_at': now,
                'message_count': 0
            }
        )
        
        success = True
        message = f"Chat session initialized successfully for email={user_email}"
        print(f"initialize_chat_session | {message}")
    except Exception as e:
        message = f"Error initializing chat session: {e}"
        print(f"initialize_chat_session | {message}")
    
    return success, message

def insert_chat_message(login_session_id: str, chat_session_id: str, user_input: str, 
                       user_input_kannada: str | None, input_type: str, assistant_output: str) -> Tuple[bool, str]:
    success = False
    message = ""

    valid_input_types = ['manual-english', 'manual-kannada', 'button', 'default', 'system']
    if input_type not in valid_input_types:
        message = f"Invalid input_type: '{input_type}'. Must be one of: {', '.join(valid_input_types)}"
        print(f"insert_chat_message | {message}")
        return success, message

    try:
        dynamodb = boto3.resource('dynamodb')
        chat_messages_table = dynamodb.Table(CHAT_MESSAGES_TABLE_NAME)
        chat_sessions_table = dynamodb.Table(CHAT_SESSIONS_TABLE_NAME)
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        now = datetime.now(timezone.utc)
        
        # Insert user message
        user_timestamp = now.isoformat()
        user_message_timestamp = f"{user_timestamp}#user"
        
        # Translate user message to Kannada if not already provided
        user_message_kannada = user_input_kannada if user_input_kannada else translate_text(
            text=user_input, 
            source_language="en", 
            target_language="kn"
        )
        
        chat_messages_table.put_item(
            Item={
                'global_session_id': global_session_id,
                'message_timestamp': user_message_timestamp,
                'role': 'user',
                'message': user_input,
                'message_kannada': user_message_kannada,
                'input_type': input_type,
                'created_at': user_timestamp
            }
        )
        
        # Insert assistant message
        assistant_timestamp = (now + timedelta(milliseconds=100)).isoformat()
        assistant_message_timestamp = f"{assistant_timestamp}#assistant"
        
        # Translate assistant message to Kannada
        assistant_message_kannada = translate_text(
            text=assistant_output, 
            source_language="en", 
            target_language="kn"
        )
        
        chat_messages_table.put_item(
            Item={
                'global_session_id': global_session_id,
                'message_timestamp': assistant_message_timestamp,
                'role': 'assistant',
                'message': assistant_output,
                'message_kannada': assistant_message_kannada,
                'input_type': 'default',
                'created_at': assistant_timestamp
            }
        )
        
        # Update session message count
        chat_sessions_table.update_item(
            Key={'global_session_id': global_session_id},
            UpdateExpression="SET message_count = message_count + :inc, last_updated_at = :time",
            ExpressionAttributeValues={
                ':inc': 2,
                ':time': assistant_timestamp
            }
        )
        
        success = True
        message = "Chat history inserted successfully"
        print(f"insert_chat_message | {message}")
    except Exception as e:
        message = f"Error inserting chat history: {e}"
        print(f"insert_chat_message | {message}")

    return success, message

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    try:
        # Parse request body
        if 'body' in event and event['body'] is not None:
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                return {
                    'statusCode': 422,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'detail': 'Invalid JSON in request body'
                    })
                }
        else:
            return {
                'statusCode': 422,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'Request body is required'
                })
            }

        # Get parameters from request
        user_first_name = body.get('user_first_name', '').strip()
        user_last_name = body.get('user_last_name', '').strip()
        user_email = body.get('user_email', '').strip()
        login_session_id = body.get('login_session_id', '').strip()
        chat_session_id = body.get('chat_session_id', '').strip()
        student_name = body.get('student_name', '').strip()
        
        # Validate required fields
        if not user_first_name:
            return {
                'statusCode': 422,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'user_first_name is required and cannot be empty'
                })
            }
            
        if not user_last_name:
            return {
                'statusCode': 422,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'user_last_name is required and cannot be empty'
                })
            }
            
        if not user_email:
            return {
                'statusCode': 422,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'user_email is required and cannot be empty'
                })
            }
            
        if not login_session_id:
            return {
                'statusCode': 422,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'login_session_id is required and cannot be empty'
                })
            }
            
        if not chat_session_id:
            return {
                'statusCode': 422,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'chat_session_id is required and cannot be empty'
                })
            }
            
        if not student_name:
            return {
                'statusCode': 422,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'student_name is required and cannot be empty'
                })
            }

        user_full_name = f"{user_first_name} {user_last_name}"
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        # Initialize chat session
        init_chat_success, init_chat_message = initialize_chat_session(
            user_email=user_email,
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            student_name=student_name
        )
        
        if not init_chat_success:
            print(f"Error initializing chat session in DynamoDB: {init_chat_message} | global_session_id={global_session_id}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'Failed to initialize chat session. Please try again.'
                })
            }

        # Create first messages
        first_user_message = f"Hi {formatted(student_name).split()[0]}, I'm {user_full_name}, your instructor. I would like to chat with you."
        first_assistant_message = f"Hi, I'm {formatted(student_name).split()[0]} from Agastya International Foundation. What would you like to know about me?"
    
        # Insert first messages
        insert_chat_message_success, insert_chat_message_message = insert_chat_message(
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_input=first_user_message,
            user_input_kannada=None,
            input_type="system",
            assistant_output=first_assistant_message
        )
        
        if not insert_chat_message_success:
            print(f"Error inserting chat history: {insert_chat_message_message} | global_session_id={global_session_id}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'Failed to initialize chat messages. Please try again.'
                })
            }
            
        print(f"First message inserted for global_session_id={global_session_id}")

        # Return response matching StartChatResponse format
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': f"Chat session initialized successfully for email={user_email}",
                'result': True,
                'data': first_assistant_message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        print(f"Start chat session endpoint error: {str(e)} | global_session_id={global_session_id if 'global_session_id' in locals() else 'unknown'}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'detail': 'Failed to start chat session. Please try again.'
            })
        }