import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from typing import List, Dict, Tuple

# Environment variables
CHAT_MESSAGES_TABLE_NAME = os.environ['CHAT_MESSAGES_TABLE_NAME']

def get_chat_history_for_ui(login_session_id: str, chat_session_id: str) -> Tuple[bool, str, bool, List[Dict]]:
    success = False
    message = ""
    result = False
    data = []

    if not login_session_id or not chat_session_id:
        message = "Login session id and chat session id are required"
        print(f"get_chat_history_for_ui | {message}")
        return success, message, result, data
    
    try:
        dynamodb = boto3.resource('dynamodb')
        chat_messages_table = dynamodb.Table(CHAT_MESSAGES_TABLE_NAME)
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        response = chat_messages_table.query(
            KeyConditionExpression=Key('global_session_id').eq(global_session_id),
            ScanIndexForward=True
        )
        
        if 'Items' in response and len(response['Items']) > 0:
            for item in response.get('Items', []):
                role = item.get('role')
                msg = item.get('message')
                created_at = item.get('created_at')
                input_type = item.get('input_type')

                # Skip system messages (like the initial greeting)
                if input_type == "system":
                    continue

                if msg and msg.strip():
                    data.append({
                        "role": role,
                        "content": msg,
                        "created_at": created_at
                    })
            
            success = True
            result = True
            message = f"Retrieved {len(data)} messages for session {global_session_id}"
            print(f"get_chat_history_for_ui | {message}")
        else:
            success = True
            message = f"No chat history found for session {global_session_id}"
            print(f"get_chat_history_for_ui | {message}")
    except Exception as e:
        message = f"Error getting chat history: {str(e)}"
        print(f"get_chat_history_for_ui | {message}")
    
    return success, message, result, data

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
        login_session_id = body.get('login_session_id')
        chat_session_id = body.get('chat_session_id')
        
        print(f"login_session_id: {login_session_id}, chat_session_id: {chat_session_id}")
        
        # Validate required fields
        if not login_session_id or not login_session_id.strip():
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
            
        if not chat_session_id or not chat_session_id.strip():
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

        global_session_id = f"{login_session_id.strip()}#{chat_session_id.strip()}"

        # Call the function
        get_chat_history_success, get_chat_history_message, get_chat_history_result, messages = get_chat_history_for_ui(
            login_session_id=login_session_id.strip(),
            chat_session_id=chat_session_id.strip()
        )
        
        # Check for database errors
        if not get_chat_history_success:
            print(f"Database error in getting chat history for session {global_session_id}: {get_chat_history_message}")
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
        
        # Handle case where no chat history is found
        if not get_chat_history_result:
            print(f"No chat history found for session {global_session_id}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'message': "No chat history found",
                    'result': False,
                    'data': [],
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        # Create message infos (matching your FastAPI response structure)
        message_infos = [
            {
                "role": message["role"],
                "content": message["content"],
                "created_at": message["created_at"]
            } for message in messages
        ]
        
        print(f"Retrieved {len(message_infos)} messages for session {global_session_id}")
        
        # Return response matching GetChatHistoryResponse format
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': f"Retrieved {len(message_infos)} messages",
                'result': True,
                'data': message_infos,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Get chat history endpoint error: {str(e)} | global_session_id={global_session_id if 'global_session_id' in locals() else 'unknown'}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'detail': 'Failed to retrieve chat history. Please try again.'
            })
        }