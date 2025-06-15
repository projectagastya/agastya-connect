import json
import boto3
import random
import os
from datetime import datetime
from botocore.exceptions import ClientError
from typing import List, Dict, Tuple, Optional
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('STUDENT_TABLE_NAME', 'students')
table = dynamodb.Table(table_name)

def convert_decimal(obj):
    if isinstance(obj, Decimal):
        # Convert to int if it's a whole number, otherwise float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    return obj

def get_student_profiles(count: int = 8) -> Tuple[bool, str, Optional[bool], List[Dict]]:
    success = False
    message = ""
    result = False
    data = []
    
    try:
        print(f"Scanning DynamoDB table: {table_name}")
        response = table.scan()
        
        if 'Items' in response:
            students = response['Items']
            data = [
                {
                    "student_name": student.get('student_name'),
                    "student_sex": student.get('student_sex'),
                    "student_age": convert_decimal(student.get('student_age')),
                    "student_state": student.get('student_state'),
                    "student_image": student.get('student_image')
                }
                for student in students
            ]
            
            print(f"Found {len(data)} students in database")
            random.shuffle(data)
            
            data = data[:min(count, len(data))]
            
            result = len(data) > 0
            success = True
            message = f"Retrieved {len(data)} student profiles successfully" if result else f"No student profiles found for a request to get {count} student profiles"
            print(f"get_students | {message}")
            
    except ClientError as e:
        message = f"Error getting {count} student profiles: {e}"
        print(f"get_students | {message}")
    
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
            body = {}

        # Get count from request (default to 8 like your util function)
        count = body.get('count', 8)
        print(f"Requested count: {count}")
        
        # Validate count (return 422 for invalid count)
        if not isinstance(count, int) or count <= 0:
            return {
                'statusCode': 422,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': f'Count must be a positive integer, got: {count}'
                })
            }

        # Call the util function (exactly like your FastAPI endpoint does)
        get_student_profiles_success, get_student_profiles_message, get_student_profiles_result, students = get_student_profiles(count=count)
        
        # Check for database errors (exactly like your FastAPI endpoint does)
        if not get_student_profiles_success:
            print(f"Database error in getting {count} student profiles: {get_student_profiles_message}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'detail': f'Failed to retrieve {count} student profiles from the database.'
                })
            }
        
        # Limit students again (redundant but matching your FastAPI logic exactly)
        students = students[:min(count, len(students))]
        
        # Create student profiles (your FastAPI creates StudentProfileSchema objects, but we'll use dicts)
        student_profiles = [
            {
                "student_name": student["student_name"],
                "student_sex": student["student_sex"], 
                "student_age": convert_decimal(student["student_age"]),
                "student_state": student["student_state"],
                "student_image": student["student_image"]
            } for student in students
        ]
        
        print(f"Retrieved {len(student_profiles)} student profiles successfully for a request to get {count} student profiles")
        
        # Return response exactly like your FastAPI GetStudentProfilesResponse
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': get_student_profiles_success,
                'message': get_student_profiles_message,
                'result': get_student_profiles_result,
                'data': student_profiles,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Get student profiles endpoint error for {count if 'count' in locals() else 'unknown'} student profiles: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'detail': f'Failed to retrieve {count if "count" in locals() else "student"} student profiles. Please try again.'
            })
        }