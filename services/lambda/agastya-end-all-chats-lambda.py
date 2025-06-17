import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from typing import Tuple

# Environment variables
CHAT_SESSIONS_TABLE_NAME = os.environ['CHAT_SESSIONS_TABLE_NAME']

def end_all_chat_sessions(user_email: str, login_session_id: str) -> Tuple[bool, str]:
    success = False
    message = ""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        chat_sessions_table = dynamodb.Table(CHAT_SESSIONS_TABLE_NAME)
        
        response = chat_sessions_table.query(
            IndexName='UserSessionsIndex',
            KeyConditionExpression=Key('user_email').eq(user_email),
            FilterExpression=Attr('login_session_id').eq(login_session_id) & Attr('session_status').eq('active')
        )
        
        if 'Items' not in response or len(response['Items']) == 0:
            success = True
            message = f"No active chat sessions found for user: {user_email}"
            print(f"end_all_chat_sessions | {message}")
            return success, message
        
        now = datetime.now().isoformat()
        
        for session in response['Items']:
            global_session_id = session['global_session_id']
            chat_sessions_table.update_item(
                Key={'global_session_id': global_session_id},
                UpdateExpression="SET session_status = :status, last_updated_at = :time",
                ExpressionAttributeValues={
                    ':status': 'ended',
                    ':time': now
                }
            )
            print(f"end_all_chat_sessions | Ended chat session with global_session_id={global_session_id}")
        
        success = True
        message = f"Ended all {len(response['Items'])} active chat sessions for user: {user_email}"
        print(f"end_all_chat_sessions | {message}")
    except Exception as e:
        message = f"Error ending all chat sessions for user: {user_email}: {e}"
        print(f"end_all_chat_sessions | {message}")
    
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

        # Get user_email and login_session_id from request
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

        # Call the end_all_chat_sessions function
        end_all_chat_success, end_all_chat_message = end_all_chat_sessions(
            user_email=user_email.strip(),
            login_session_id=login_session_id.strip()
        )
        
        # Check for errors
        if not end_all_chat_success:
            print(f"Error ending all chat sessions for user: {end_all_chat_message} | user_email={user_email} | login_session_id={login_session_id}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': f'Failed to end chat sessions for user {user_email}. Please try again.'
                })
            }
        
        print(f"Chat sessions ended successfully for user {user_email}")
        
        # Return success response matching EndChatResponse format
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': f"Chat sessions ended successfully for user {user_email}",
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        print(f"End all chats endpoint error for user: {str(e)} | user_email={user_email if 'user_email' in locals() else 'unknown'} | login_session_id={login_session_id if 'login_session_id' in locals() else 'unknown'}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'detail': f'Failed to end chat sessions. Please try again.'
            })
        }