import boto3
import json

from config.backend.aws import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY
)
from config.backend.dynamodb import (
    DYNAMODB_CHAT_SESSIONS_TABLE_NAME,
    DYNAMODB_CHAT_MESSAGES_TABLE_NAME,
    DYNAMODB_CHAT_SESSIONS_TABLE_CONFIG,
    DYNAMODB_CHAT_MESSAGES_TABLE_CONFIG,
    DYNAMODB_STUDENT_TABLE_CONFIG,
    DYNAMODB_STUDENT_TABLE_NAME
)
from config.backend.s3 import (
    MAIN_S3_BUCKET_NAME,
    STUDENT_METADATA_FILE_NAME,
    STUDENT_METADATA_FOLDER_PATH,
    STUDENT_VECTORSTORE_FOLDER_PATH
)
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from utils.shared.logger import backend_logger
from typing import Dict, List, Optional, Tuple

# Function to get a boto3 DynamoDB resource object.
def get_dynamodb_resource():
    return boto3.resource(
        'dynamodb', 
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

# Function to create the DynamoDB table for storing student profiles if it doesn't exist.
def create_student_table() -> tuple[bool, bool, str]:
    success = False
    result = False
    message = ""
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.create_table(**DYNAMODB_STUDENT_TABLE_CONFIG)
        table.meta.client.get_waiter('table_exists').wait(TableName=DYNAMODB_STUDENT_TABLE_NAME)

        success = True
        result = True
        message = f"Table: '{DYNAMODB_STUDENT_TABLE_NAME}' created successfully"
        backend_logger.info(f"create_students_table | {message}")
        return success, result, message

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            success = True
            message = f"Table '{DYNAMODB_STUDENT_TABLE_NAME}' already exists"
            backend_logger.info(f"create_students_table | {message}")
            return success, result, message

        message = f"Error creating table: {str(e)}"
        backend_logger.error(f"create_students_table | {message}")
        return success, result, message

    except Exception as e:
        message = f"Unexpected error creating table: {str(e)}"
        backend_logger.error(f"create_students_table | {message}")
        return success, result, message

# Function to get the DynamoDB student table object.
def get_student_table():
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(DYNAMODB_STUDENT_TABLE_NAME)

# Function to load student metadata from an Excel file stored in S3.
def load_student_metadata_from_s3() -> Tuple[bool, str, Optional[List[Dict]]]:
    success = False
    message = ""
    data = None
    
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        s3_key = f"{STUDENT_METADATA_FOLDER_PATH}/{STUDENT_METADATA_FILE_NAME}"
        
        response = s3_client.get_object(
            Bucket=MAIN_S3_BUCKET_NAME,
            Key=s3_key
        )
        
        file_content = response['Body'].read().decode('utf-8')
        data = json.loads(file_content)
        
        success = True
        message = f"Successfully loaded student profiles from S3 bucket {MAIN_S3_BUCKET_NAME}"
        backend_logger.info(f"load_students_from_s3 | Loaded {len(data)} profiles from {MAIN_S3_BUCKET_NAME}")
    except ClientError as e:
        message = f"Error loading student profiles from S3: {str(e)}"
        backend_logger.error(f"load_students_from_s3 | {message}")
    except Exception as e:
        message = f"Unexpected error loading student profiles from S3: {str(e)}"
        backend_logger.error(f"load_students_from_s3 | {message}")
    
    return success, message, data

# Function to validate student data fields.
def validate_student(student_name: str, student_sex: str, student_age: int, student_state: str) -> Tuple[bool, str]:
    success = False
    message = ""

    valid_sexes = ['male', 'female']
    if student_sex.lower() not in valid_sexes:
        message = f"Invalid sex: '{student_sex}' for student: '{student_name}'. Must be one of: {', '.join(valid_sexes)}"
        return success, message
    
    if student_age < 0:
        message = f"Invalid age: '{student_age}' for student: '{student_name}'. Must be greater than 0"
        return success, message
    
    valid_states = [
        "andhra-pradesh", "arunachal-pradesh", "assam", "bihar", "chhattisgarh",
        "goa", "gujarat", "haryana", "himachal-pradesh", "jammu-kashmir",
        "jharkhand", "karnataka", "kerala", "madhya-pradesh", "maharashtra",
        "manipur", "meghalaya", "mizoram", "nagaland", "odisha", "punjab",
        "rajasthan", "sikkim", "tamil-nadu", "telangana", "tripura",
        "uttar-pradesh", "uttarakhand", "west-bengal"
    ]

    if student_state.lower().replace(' ', '-') not in valid_states:
        message = f"Invalid state: '{student_state}' for student: '{student_name}'. Must be one of: {', '.join(valid_states)}"
        return success, message
    
    success = True
    message = "Student profile data is valid"
    return success, message

# Function to insert or update a student's profile in the DynamoDB table.
def insert_student(student_name: str, student_sex: str, student_age: int, student_state: str) -> Tuple[bool, str, Optional[bool], Optional[str]]:
    success = False
    message = ""
    result = False
    data = None
    
    validation_success, validation_message = validate_student(student_name, student_sex, student_age, student_state)
    if not validation_success:
        backend_logger.error(f"insert_student | Validation error for {student_name}: {validation_message}")
        return success, validation_message, result, data
    
    get_profile_success, get_profile_message, get_profile_result, _ = get_single_student_profile(student_name)
    if not get_profile_success:
        message = f"Error getting student profile for name: {student_name}: {get_profile_message}"
        backend_logger.error(f"insert_student | {message}")
        return success, message, result, data
    
    if get_profile_result:
        success = True
        message = f"Student profile already exists for name: {student_name}"
        backend_logger.info(f"insert_student | {message}")
        return success, message, result, data
    
    try:
        table = get_student_table()
        
        _ = table.put_item(
            Item={
                'student_name': student_name,
                'student_sex': student_sex,
                'student_age': student_age,
                'student_state': student_state
            }
        )
        success = True
        message = f"Student profile for {student_name} inserted successfully"
        result = True
        data = student_name
        backend_logger.info(f"insert_student | {message}")
    except ClientError as e:
        message = f"Error inserting student profile for name: {student_name}: {e}"
        backend_logger.error(f"insert_student | {message}")
    
    return success, message, result, data

# Function to retrieve a single student's profile from DynamoDB by name.
def get_single_student_profile(student_name: str) -> Tuple[bool, str, Optional[bool], Dict]:
    success = False
    message = ""
    result = False
    data = {}
    
    try:
        table = get_student_table()
        
        response = table.get_item(Key={'student_name': student_name})
        
        if 'Item' in response:
            student = response['Item']
            success = True
            message = f"Student profile found for name: {student_name}"
            result = True
            data = {
                "student_name": student.get('student_name'),
                "student_sex": student.get('student_sex'),
                "student_age": student.get('student_age'),
                "student_state": student.get('student_state')
            }
            backend_logger.info(f"get_single_student | {message}")
        else:
            success = True
            message = f"Student profile not found for name: {student_name}"
            backend_logger.info(f"get_single_student | {message}")
    except ClientError as e:
        message = f"Error getting student profile for name: {student_name}: {e}"
        backend_logger.error(f"get_single_student | {message}")
    
    return success, message, result, data

# Function to populate the student DynamoDB table using metadata from S3.
def populate_student_table() -> Tuple[bool, str]:
    success = False
    message = ""
    
    s3_success, s3_message, students = load_student_metadata_from_s3()
    
    if not s3_success or not students:
        message = f"Failed to load student profiles from S3: {s3_message}"
        backend_logger.error(f"populate_student_table | {message}")
        return False, message
    
    success_count = 0
    error_count = 0
    already_exists_count = 0
    
    for student in students:
        student_name = student.get('student_name')
        student_sex = student.get('student_sex')
        student_age = student.get('student_age', None)
        student_state = student.get('student_state')
        
        insert_success, insert_message, insert_result, _ = insert_student(
            student_name, student_sex, student_age, student_state
        )
        
        if not insert_success:
            backend_logger.error(f"populate_student_table | Error inserting student profile for name: {student_name}: {insert_message}")
            error_count += 1
        elif not insert_result:
            if "already exists" in insert_message:
                already_exists_count += 1
            else:
                backend_logger.error(f"populate_student_table | Error inserting student profile for name: {student_name}: {insert_message}")
                error_count += 1
        else:
            success_count += 1
    
    success = True
    message = f"Student table populated successfully from S3 with {len(students)} student profiles"
    backend_logger.info(f"populate_student_table | Completed populating {len(students)} profiles: {success_count} new inserts, {already_exists_count} already existed, {error_count} errors")
    
    return success, message

# Function to create the DynamoDB table for storing chat messages if it doesn't exist.
def create_chat_message_table() -> Tuple[bool, str]:
    success = False
    message = ""
    
    try:
        dynamodb = get_dynamodb_resource()
        chat_messages_table = dynamodb.create_table(**DYNAMODB_CHAT_MESSAGES_TABLE_CONFIG)
        chat_messages_table.meta.client.get_waiter('table_exists').wait(TableName=DYNAMODB_CHAT_MESSAGES_TABLE_NAME)
        
        success = True
        message = "Chat message table created successfully"
        backend_logger.info(f"create_chat_message_table | {message}")
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            success = True
            message = "Chat message table already exists"
            backend_logger.info(f"create_chat_message_table | {message}")
        else:
            message = f"Error creating chat message table: {e}"
            backend_logger.error(f"create_chat_message_table | {message}")
    except Exception as e:
        message = f"Unexpected error creating chat message table: {e}"
        backend_logger.error(f"create_chat_message_table | {message}")
    
    return success, message

# Function to create the DynamoDB table for storing chat session metadata if it doesn't exist.
def create_chat_session_table() -> Tuple[bool, str]:
    success = False
    message = ""
    
    try:
        dynamodb = get_dynamodb_resource()
        
        chat_sessions_table = dynamodb.create_table(**DYNAMODB_CHAT_SESSIONS_TABLE_CONFIG)
        chat_sessions_table.meta.client.get_waiter('table_exists').wait(TableName=DYNAMODB_CHAT_SESSIONS_TABLE_NAME)

        success = True
        message = "Chat session table created successfully"
        backend_logger.info(f"create_chat_session_table | {message}")
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            success = True
            message = "Chat session table already exists"
            backend_logger.info(f"create_chat_session_table | {message}")
        else:
            message = f"Error creating chat session table: {e}"
            backend_logger.error(f"create_chat_session_table | {message}")
    except Exception as e:
        message = f"Unexpected error creating chat session table: {e}"
        backend_logger.error(f"create_chat_session_table | {message}")
    
    return success, message

if __name__ == "__main__":
    pass