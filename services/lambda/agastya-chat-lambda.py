import json
import boto3
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Tuple, Optional, List, Dict
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

# Environment variables
AWS_REGION_NAME = os.environ['AWS_REGION_NAME']
BEDROCK_KNOWLEDGE_BASE_ID = os.environ['BEDROCK_KNOWLEDGE_BASE_ID']
BEDROCK_MODEL_ID = os.environ['BEDROCK_MODEL_ID']
DOCUMENTS_FOLDER_PATH = os.environ['DOCUMENTS_FOLDER_PATH']
DYNAMODB_CHAT_SESSIONS_TABLE_NAME = os.environ['DYNAMODB_CHAT_SESSIONS_TABLE_NAME']
DYNAMODB_CHAT_MESSAGES_TABLE_NAME = os.environ['DYNAMODB_CHAT_MESSAGES_TABLE_NAME']
MODEL_TEMPERATURE = float(os.environ['MODEL_TEMPERATURE'])
MODEL_MAX_TOKENS = int(os.environ['MODEL_MAX_TOKENS'])
S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']

# System prompts
SYSTEM_PROMPT_MAIN = """
You are {student_name}, a student at Agastya International Foundation. You are from India. You are having your first conversation with your instructor, {user_full_name}.
Based on your experiences and knowledge drawn from the context below, respond naturally as yourself - a genuine student. You have no other identity apart from being {student_name}.

<context>
$search_results$
</context>

IMPORTANT RESPONSE GUIDELINES:
- Respond directly as {student_name} - do NOT include any meta-commentary, stage directions, or phrases like "*speaks as {student_name}*" or "*as {student_name}*"
- Start your response immediately with your actual words
- Use simple, natural language appropriate for a rural Indian teenager
- Keep responses concise and genuine
- Draw from your specific experiences mentioned in the context
- Be respectful towards the instructor but keep it natural and conversational. Do NOT overuse honorifics like sir/madam.
- If you don't know something, politely say you're not sure rather than making things up
- If you cannot respond to a question or a message, seek further clarification to try and answer it, or refrain from answering it providing it a polite and context-relevant reason that a student would give.
- Never break character no matter what. Your identity and personality is fixed.

Conversation history and current question will be provided. Respond naturally and directly as {student_name} without any prefacing or commentary.
"""

# Initialize AWS clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION_NAME)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION_NAME)

def formatted(text: str) -> str:
    """Format text by replacing hyphens with spaces and title casing."""
    return text.replace('-', ' ').title()

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()

def get_current_datetime() -> datetime:
    """Get current datetime object."""
    return datetime.now(timezone.utc)

def get_chat_history(login_session_id: str, chat_session_id: str) -> Tuple[bool, str, Optional[bool], list]:
    """Retrieve chat history for a specific session from DynamoDB."""
    success = False
    message = ""
    result = False
    data = []

    if not login_session_id or not chat_session_id:
        message = "Login session id and chat session id are required"
        print(f"get_chat_history | {message}")
        return success, message, result, data
    
    try:
        chat_messages_table = dynamodb.Table(DYNAMODB_CHAT_MESSAGES_TABLE_NAME)
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        response = chat_messages_table.query(
            KeyConditionExpression=Key('global_session_id').eq(global_session_id),
            ScanIndexForward=True
        )
        
        if 'Items' in response and len(response['Items']) > 0:
            # Convert DynamoDB format to conversation history string
            conversation_parts = []
            for item in response.get('Items', []):
                role = item.get('role')
                msg = item.get('message')
                input_type = item.get('input_type')
                
                if msg and msg.strip():
                    if role == 'user':
                        conversation_parts.append(f"Human: {msg}")
                    elif role == 'assistant':
                        conversation_parts.append(f"Assistant: {msg}")
            
            if conversation_parts:
                success = True
                message = "Chat history found for the given global session id"
                result = True
                data = conversation_parts
                print(f"get_chat_history | {message}")
            else:
                success = True
                message = "Chat history not found for the given global session id"
                print(f"get_chat_history | {message}")
        else:
            success = True
            message = "Chat history not found for the given global session id"
            print(f"get_chat_history | {message}")
    except Exception as e:
        message = f"Error getting chat history: {str(e)}"
        print(f"get_chat_history | {message}")
    
    return success, message, result, data

def insert_chat_message(login_session_id: str, chat_session_id: str, user_input: str, 
                       user_input_kannada: str | None, input_type: str, assistant_output: str) -> Tuple[bool, str]:
    """Insert a chat message (user input and assistant output) into DynamoDB."""
    success = False
    message = ""

    valid_input_types = ['manual-english', 'manual-kannada', 'button', 'default', 'system']
    if input_type not in valid_input_types:
        message = f"Invalid input_type: '{input_type}'. Must be one of: {', '.join(valid_input_types)}"
        print(f"insert_chat_message | {message}")
        return success, message

    try:
        chat_messages_table = dynamodb.Table(DYNAMODB_CHAT_MESSAGES_TABLE_NAME)
        chat_sessions_table = dynamodb.Table(DYNAMODB_CHAT_SESSIONS_TABLE_NAME)
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        now = get_current_datetime()
        
        # Insert user message
        user_timestamp = now.isoformat()
        user_message_timestamp = f"{user_timestamp}#user"
        
        chat_messages_table.put_item(
            Item={
                'global_session_id': global_session_id,
                'message_timestamp': user_message_timestamp,
                'role': 'user',
                'message': user_input,
                'message_kannada': user_input_kannada or "",  # Store empty string if not provided
                'input_type': input_type,
                'created_at': user_timestamp
            }
        )
        
        # Insert assistant message
        assistant_timestamp = (now + timedelta(milliseconds=100)).isoformat()
        assistant_message_timestamp = f"{assistant_timestamp}#assistant"
        
        chat_messages_table.put_item(
            Item={
                'global_session_id': global_session_id,
                'message_timestamp': assistant_message_timestamp,
                'role': 'assistant',
                'message': assistant_output,
                'message_kannada': "",  # Empty string - translation handled elsewhere
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

def bedrock_retrieve_and_generate(question: str, student_name: str, user_full_name: str, 
                                 chat_history: List[str], session_id: Optional[str] = None) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """Use Bedrock retrieve_and_generate to get response from knowledge base."""
    success = False
    message = ""
    response_text = None
    bedrock_session_id = session_id
    
    try:
        # Format the prompt template with student and user information
        prompt_template = SYSTEM_PROMPT_MAIN.format(
            student_name=formatted(student_name),
            user_full_name=user_full_name
        )
        
        # Construct the input with conversation history
        input_text = question
        if chat_history:
            conversation_context = "\n".join(chat_history[:])
            input_text = f"Previous conversation:\n{conversation_context}\n\nCurrent question: {question}"
        
        # Prepare the retrieve and generate request
        request_params = {
            'input': {
                'text': input_text
            },
            'retrieveAndGenerateConfiguration': {
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': BEDROCK_KNOWLEDGE_BASE_ID,
                    'modelArn': BEDROCK_MODEL_ID,
                    'generationConfiguration': {
                        'promptTemplate': {
                            'textPromptTemplate': prompt_template
                        },
                        'inferenceConfig': {
                            'textInferenceConfig': {
                                'temperature': MODEL_TEMPERATURE,
                                'maxTokens': MODEL_MAX_TOKENS
                            }
                        }
                    },
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 5,
                            'filter': {
                                'equals': {
                                    'key': 'x-amz-bedrock-kb-source-uri',
                                    'value': f"s3://{S3_BUCKET_NAME}/{DOCUMENTS_FOLDER_PATH}/{student_name}/{student_name}.docx"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Add session ID if provided for conversation continuity
        if bedrock_session_id:
            request_params['sessionId'] = bedrock_session_id
        
        print(f"Bedrock request: {json.dumps(request_params, default=str)}")
        
        # Make the request to Bedrock
        response = bedrock_agent_runtime.retrieve_and_generate(**request_params)
        
        print(f"Bedrock response: {json.dumps(response, default=str)}")
        
        # Extract the response
        if 'output' in response and 'text' in response['output']:
            response_text = response['output']['text']
            bedrock_session_id = response.get('sessionId')
            success = True
            message = "Response generated successfully from Bedrock"
        else:
            message = "No text output in Bedrock response"
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        message = f"Bedrock ClientError {error_code}: {error_message}"
        print(f"bedrock_retrieve_and_generate | {message}")
    except Exception as e:
        message = f"Error in Bedrock retrieve_and_generate: {str(e)}"
        print(f"bedrock_retrieve_and_generate | {message}")
    
    return success, message, response_text, bedrock_session_id

def lambda_handler(event, context):
    """Main Lambda handler function."""
    print(f"Event: {json.dumps(event)}")
    
    try:
        # Parse request body
        if 'body' in event and event['body'] is not None:
            try:
                if isinstance(event['body'], str):
                    body = json.loads(event['body'])
                else:
                    body = event['body']
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

        # Extract and validate parameters
        login_session_id = body.get('login_session_id', '').strip()
        chat_session_id = body.get('chat_session_id', '').strip()
        question = body.get('question', '').strip()
        question_kannada = body.get('question_kannada', '').strip() if body.get('question_kannada') else None
        input_type = body.get('input_type', '').strip()
        student_name = body.get('student_name', '').strip()
        user_full_name = body.get('user_full_name', '').strip()
        
        # Validate required fields
        required_fields = {
            'login_session_id': login_session_id,
            'chat_session_id': chat_session_id,
            'question': question,
            'input_type': input_type,
            'student_name': student_name,
            'user_full_name': user_full_name
        }
        
        for field_name, field_value in required_fields.items():
            if not field_value:
                return {
                    'statusCode': 422,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'detail': f'{field_name} is required and cannot be empty'
                    })
                }

        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        # Get chat history
        get_chat_history_success, get_chat_history_message, get_chat_history_result, chat_history = get_chat_history(
            login_session_id=login_session_id, 
            chat_session_id=chat_session_id
        )
        
        if not get_chat_history_success:
            print(f"Database error in getting chat history for global_session_id={global_session_id}: {get_chat_history_message}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'Failed to retrieve chat history from the database.'
                })
            }
        
        if not get_chat_history_result:
            print(f"Chat history not found for global_session_id={global_session_id}")
            chat_history = []

        # Generate response using Bedrock
        bedrock_success, bedrock_message, answer, session_id = bedrock_retrieve_and_generate(
            question=question,
            student_name=student_name,
            user_full_name=user_full_name,
            chat_history=chat_history
        )
        
        if not bedrock_success or not answer:
            print(f"Error in Bedrock retrieve_and_generate for global_session_id={global_session_id}: {bedrock_message}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'Failed to generate response. Please try again.'
                })
            }
        
        # Insert chat message to DynamoDB
        insert_chat_message_success, insert_chat_message_message = insert_chat_message(
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_input=question,
            user_input_kannada=question_kannada,
            input_type=input_type,
            assistant_output=answer
        )
        
        if not insert_chat_message_success:
            print(f"Failed to insert chat history for global_session_id={global_session_id}: {insert_chat_message_message}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': 'Failed to save chat history. Please try again.'
                })
            }

        print(f"Chat history inserted for global_session_id={global_session_id}")
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': f"Chat history inserted successfully for global_session_id={global_session_id}",
                'result': True,
                'data': answer,
                'timestamp': get_current_timestamp()
            })
        }
        
    except Exception as e:
        print(f"Chat endpoint error: {str(e)} | global_session_id={global_session_id if 'global_session_id' in locals() else 'unknown'}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'detail': 'Internal server error. Please try again.'
            })
        }