import json
import boto3
import os

from datetime import datetime, timezone
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from typing import List, Dict, Tuple

# Environment variables
CHAT_SESSIONS_TABLE_NAME = os.environ['CHAT_SESSIONS_TABLE_NAME']

def get_active_chat_sessions(user_email: str, login_session_id: str) -> Tuple[bool, str, bool, List[Dict]]:
    success = False
    message = ""
    result = False
    data = []
    
    try:
        dynamodb = boto3.resource('dynamodb')
        chat_sessions_table = dynamodb.Table(CHAT_SESSIONS_TABLE_NAME)
        
        response = chat_sessions_table.query(
            IndexName='UserSessionsIndex',
            KeyConditionExpression=Key('user_email').eq(user_email),
            FilterExpression=Attr('login_session_id').eq(login_session_id) & Attr('session_status').eq('active')
        )
        
        if 'Items' in response and len(response['Items']) > 0:
            sessions = response['Items']
            data = [
                {
                    "student_name": session.get('student_name'),
                    "chat_session_id": session.get('chat_session_id'),
                    "global_session_id": session.get('global_session_id'),
                    "started_at": session.get('started_at'),
                    "last_updated_at": session.get('last_updated_at')
                }
                for session in sessions
            ]
            
            result = True
            success = True
            message = f"Retrieved {len(data)} active chat sessions for user: {user_email}"
            print(f"get_active_chat_sessions | {message}")
        else:
            success = True
            message = f"No active chat sessions found for user: {user_email}"
            print(f"get_active_chat_sessions | {message}")
    except ClientError as e:
        message = f"Error getting active chat sessions for user: {user_email}: {e}"
        print(f"get_active_chat_sessions | {message}")
    
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
        user_email = body.get('user_email')
        login_session_id = body.get('login_session_id')
        
        print(f"user_email: {user_email}, login_session_id: {login_session_id}")
        
        # Validate required fields
        if not user_email or not user_email.strip():
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

        # Call the function
        get_active_sessions_success, get_active_sessions_message, get_active_sessions_result, sessions = get_active_chat_sessions(
            user_email=user_email.strip(),
            login_session_id=login_session_id.strip()
        )
        
        # Check for database errors
        if not get_active_sessions_success:
            print(f"Database error in getting active sessions: {get_active_sessions_message} | user_email={user_email} | login_session_id={login_session_id}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': f'Failed to retrieve active sessions for user {user_email} from the database.'
                })
            }
        
        # Create session infos (matching your FastAPI response structure)
        session_infos = [
            {
                "student_name": session["student_name"],
                "chat_session_id": session["chat_session_id"],
                "global_session_id": session["global_session_id"],
                "started_at": session["started_at"],
                "last_updated_at": session["last_updated_at"]
            } for session in sessions
        ]
        
        print(f"Retrieved {len(session_infos)} active chat sessions for user {user_email}")
        
        # Return response matching GetActiveSessionsResponse format
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': get_active_sessions_success,
                'message': get_active_sessions_message,
                'result': get_active_sessions_result,
                'data': session_infos,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        print(f"Get active sessions endpoint error: {str(e)} | user_email={user_email if 'user_email' in locals() else 'unknown'} | login_session_id={login_session_id if 'login_session_id' in locals() else 'unknown'}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'detail': f'Failed to retrieve active sessions. Please try again.'
            })
        }