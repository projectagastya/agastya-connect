import boto3
import io
import json
import os
import pandas as pd
import random
import shutil
import time

from backend.core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    CHAT_TRANSCRIPTS_FOLDER_PATH,
    DOCUMENT_EMBEDDING_MODEL_ID,
    DYNAMODB_CHAT_SESSIONS_TABLE_NAME,
    DYNAMODB_CHAT_MESSAGES_TABLE_NAME,
    DYNAMODB_CHAT_SESSIONS_TABLE_CONFIG,
    DYNAMODB_CHAT_MESSAGES_TABLE_CONFIG,
    DYNAMODB_STUDENT_TABLE_CONFIG,
    DYNAMODB_STUDENT_TABLE_NAME,
    MAIN_S3_BUCKET_NAME,
    RESPONSE_GENERATION_MODEL_ID,
    RESPONSE_GENERATION_MODEL_MAX_TOKENS,
    RESPONSE_GENERATION_MODEL_TEMPERATURE,
    STUDENT_METADATA_FILE_NAME,
    STUDENT_METADATA_FOLDER_PATH,
    STUDENT_VECTORSTORE_FOLDER_PATH,
    LOCAL_VECTORSTORES_DIRECTORY
)
from backend.prompts import SYSTEM_PROMPT_CONTEXTUALIZED_QUESTION, SYSTEM_PROMPT_MAIN
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.base import Chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    UnstructuredHTMLLoader,
)
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from shared.logger import backend_logger
from shared.translate import translate_english_to_kannada
from shared.utils import formatted
from typing import Dict, List, Optional, Tuple

# Function to fetch a student's vectorstore from S3, using a local cache if available.
def fetch_vectorstore_from_s3(user_email: str, login_session_id: str, chat_session_id: str, student_name: str) -> Tuple[bool, str, bool, Optional[str]]:
    success = False
    message = ""
    result = False
    data = None

    local_dir = os.path.join(LOCAL_VECTORSTORES_DIRECTORY, student_name)
    
    if os.path.exists(local_dir) and os.listdir(local_dir):
        backend_logger.info(f"fetch_vectorstore_from_s3 | Using cached vectorstore from {local_dir}")
        success = True
        result = True
        message = "Using cached vectorstore"
        data = local_dir
        return success, message, result, data
    
    created_dir = False
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            os.makedirs(local_dir, exist_ok=True)
            created_dir = True
            backend_logger.info(f"fetch_vectorstore_from_s3 | Created shared directory {local_dir}")
            
            s3_client = boto3.client(
                "s3",
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY
            )
            bucket_name = MAIN_S3_BUCKET_NAME
            s3_prefix = f"{STUDENT_VECTORSTORE_FOLDER_PATH}/{student_name}/"
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_prefix)

            if 'Contents' not in response:
                backend_logger.error(f"fetch_vectorstore_from_s3 | No objects found in S3 under prefix: {s3_prefix}")
                if created_dir and os.path.exists(local_dir):
                    shutil.rmtree(local_dir)
                success = True
                message = "No objects found in S3 under prefix"
                backend_logger.info(f"fetch_vectorstore_from_s3 | {message}")
                return success, message, result, data
        
            for obj in response['Contents']:
                key = obj['Key']
                relative_path = key[len(s3_prefix):]
                if '..' in relative_path:
                    backend_logger.warning(f"fetch_vectorstore_from_s3 | Suspicious path detected: {relative_path}")
                    continue

                if key.endswith('/') or relative_path.endswith('/'):
                    dir_path = os.path.join(local_dir, relative_path)
                    os.makedirs(dir_path, exist_ok=True)
                    backend_logger.info(f"fetch_vectorstore_from_s3 | Created directory marker {dir_path}")
                    continue

                local_file_path = os.path.join(local_dir, relative_path)
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)        
                s3_client.download_file(bucket_name, key, local_file_path)
                backend_logger.info(f"fetch_vectorstore_from_s3 | Downloaded file {key} to {local_file_path}")
            
            success = True
            result = True
            message = "Vectorstore fetched from S3 successfully"
            data = local_dir
            backend_logger.info(f"fetch_vectorstore_from_s3 | {message}")
            return success, message, result, data
            
        except Exception as e:
            retry_count += 1
            backend_logger.error(f"fetch_vectorstore_from_s3 | Error fetching vectorstore from S3 (Attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                backend_logger.info(f"fetch_vectorstore_from_s3 | Retrying download...")
                time.sleep(2 ** retry_count)
                
                if created_dir and os.path.exists(local_dir):
                    try:
                        shutil.rmtree(local_dir)
                    except Exception:
                        pass
            else:
                if created_dir and os.path.exists(local_dir):
                    try:
                        shutil.rmtree(local_dir)
                        backend_logger.info(f"fetch_vectorstore_from_s3 | Cleaned up directory {local_dir} after error")
                    except Exception as ce:
                        backend_logger.error(f"fetch_vectorstore_from_s3 | Failed to clean up directory {local_dir}: {ce}")
                
                message = f"Error fetching vectorstore from S3 after {max_retries} attempts: {e}"
    
    return success, message, result, data

# Function to load a Chroma vectorstore from a specified local directory path.
def load_vectorstore_from_path(local_dir: str) -> Tuple[bool, str, Optional[Chroma]]:
    success = False
    message = ""
    data = None
    try:
        embedding_function = GoogleGenerativeAIEmbeddings(model=DOCUMENT_EMBEDDING_MODEL_ID)
        vectorstore = Chroma(persist_directory=local_dir, embedding_function=embedding_function)
        success = True
        message = "Vectorstore loaded successfully"
        data = vectorstore
        backend_logger.info(f"load_vectorstore_from_path | {message}")
        return success, message, data
    except Exception as e:
        message = f"Error in loading vectorstore: {e}"
        backend_logger.error(f"load_vectorstore_from_path | {message}")
        return success, message, data

# Function to load and split documents from various file types (PDF, DOCX, HTML).
def load_and_split_document(file_path: str) -> Tuple[bool, str, List[Document]]:
    success = False
    message = ""
    data = None
    try:
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        elif file_path.endswith('.html'):
            loader = UnstructuredHTMLLoader(file_path)
        else:
            message = f"Unsupported file type: {file_path}"
            backend_logger.error(f"load_and_split_document | {message}")
            return success, message, data
        documents = loader.load()
        success = True
        message = "Documents loaded successfully"
        data = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len).split_documents(documents)
        backend_logger.info(f"load_and_split_document | {message}")
        return success, message, data
    except Exception as e:
        message = f"Error in loading and splitting document: {e}"
        backend_logger.error(f"load_and_split_document | {message}")
        return success, message, data

# Function to create a Retrieval-Augmented Generation (RAG) chain using a vectorstore retriever.
def get_rag_chain(retriever: Chroma) -> Tuple[bool, str, Optional[Chain]]:
    success = False
    message = ""
    data = None
    try:
        llm = ChatGoogleGenerativeAI(
            model=RESPONSE_GENERATION_MODEL_ID,
            temperature=RESPONSE_GENERATION_MODEL_TEMPERATURE,
            max_tokens=RESPONSE_GENERATION_MODEL_MAX_TOKENS
        )
        contextualize_question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT_CONTEXTUALIZED_QUESTION),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ]
        )
        final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT_MAIN),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ]
        )
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_question_prompt)
        question_answer_chain = create_stuff_documents_chain(llm=llm, prompt=final_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        success = True
        message = "RAG chain created successfully"
        data = rag_chain
    except Exception as e:
        backend_logger.error(f"Error in getting RAG chain: {e}")
        message = f"Error in getting RAG chain: {e}"
    return success, message, data

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
def insert_student(student_name: str, student_sex: str, student_age: int, student_state: str, student_image: str) -> Tuple[bool, str, Optional[bool], Optional[str]]:
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
                'student_state': student_state,
                'student_image': student_image
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
                "student_state": student.get('student_state'),
                "student_image": student.get('student_image')
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

# Function to retrieve a specified number of random student profiles from DynamoDB.
def get_student_profiles(count: int = 8) -> Tuple[bool, str, Optional[bool], List[Dict]]:
    success = False
    message = ""
    result = False
    data = []
    
    try:
        table = get_student_table()
        response = table.scan()
        
        if 'Items' in response:
            students = response['Items']
            data = [
                {
                    "student_name": student.get('student_name'),
                    "student_sex": student.get('student_sex'),
                    "student_age": student.get('student_age'),
                    "student_state": student.get('student_state'),
                    "student_image": student.get('student_image')
                }
                for student in students
            ]
            
            random.shuffle(data)
            
            data = data[:min(count, len(data))]
            
            result = len(data) > 0
            success = True
            message = result and f"Retrieved {len(data)} student profiles successfully" or f"No student profiles found for a request to get {count} student profiles"
            backend_logger.info(f"get_students | {message}")
    except ClientError as e:
        message = f"Error getting {count} student profiles: {e}"
        backend_logger.error(f"get_students | {message}")
    
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
        student_image = student.get('student_image', None)
        
        insert_success, insert_message, insert_result, _ = insert_student(
            student_name, student_sex, student_age, student_state, student_image
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

# Function to initialize a new chat session in DynamoDB.
def initialize_chat_session(user_email: str, login_session_id: str, chat_session_id: str, user_first_name: str, user_last_name: str, student_name: str) -> Tuple[bool, str]:
    success = False
    message = ""
    
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(DYNAMODB_CHAT_SESSIONS_TABLE_NAME)
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        now = datetime.now().isoformat()
        
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
        backend_logger.info(f"initialize_chat_session | {message}")
    except Exception as e:
        message = f"Error initializing chat session: {e}"
        backend_logger.error(f"initialize_chat_session | {message}")
    
    return success, message

# Function to insert a chat message (user input and assistant output) into DynamoDB.
def insert_chat_message(login_session_id: str, chat_session_id: str, user_input: str, user_input_kannada: str | None, input_type: str, assistant_output: str) -> Tuple[bool, str]:
    success = False
    message = ""

    valid_input_types = ['manual-english', 'manual-kannada', 'button', 'default', 'system']
    if input_type not in valid_input_types:
        message = f"Invalid input_type: '{input_type}'. Must be one of: {', '.join(valid_input_types)}"
        backend_logger.error(f"insert_chat_message | {message}")
        return success, message

    try:
        dynamodb = get_dynamodb_resource()
        chat_messages_table = dynamodb.Table(DYNAMODB_CHAT_MESSAGES_TABLE_NAME)
        chat_sessions_table = dynamodb.Table(DYNAMODB_CHAT_SESSIONS_TABLE_NAME)
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        now = datetime.now()
        
        user_timestamp = now.isoformat()
        user_message_timestamp = f"{user_timestamp}#user"
        
        chat_messages_table.put_item(
            Item={
                'global_session_id': global_session_id,
                'message_timestamp': user_message_timestamp,
                'role': 'user',
                'message': user_input,
                'message_kannada': user_input_kannada if user_input_kannada else translate_english_to_kannada(user_input),
                'input_type': input_type,
                'created_at': user_timestamp
            }
        )
        
        assistant_timestamp = (now + timedelta(milliseconds=100)).isoformat()
        assistant_message_timestamp = f"{assistant_timestamp}#assistant"
        
        chat_messages_table.put_item(
            Item={
                'global_session_id': global_session_id,
                'message_timestamp': assistant_message_timestamp,
                'role': 'assistant',
                'message': assistant_output,
                'message_kannada': translate_english_to_kannada(assistant_output),
                'input_type': 'default',
                'created_at': assistant_timestamp
            }
        )
        
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
        backend_logger.info(f"insert_chat_message | {message}")
    except Exception as e:
        message = f"Error inserting chat history: {e}"
        backend_logger.error(f"insert_chat_message | {message}")

    return success, message
    
# Function to retrieve the chat history for a specific session from DynamoDB.
def get_chat_history(login_session_id: str, chat_session_id: str) -> Tuple[bool, str, Optional[bool], list]:
    success = False
    message = ""
    result = False
    data = []

    if not login_session_id or not chat_session_id:
        message = "Login session id and chat session id are required"
        backend_logger.error(f"get_chat_history | {message}")
        return success, message, result, data
    
    try:
        dynamodb = get_dynamodb_resource()
        chat_messages_table = dynamodb.Table(DYNAMODB_CHAT_MESSAGES_TABLE_NAME)
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            response = chat_messages_table.query(
                KeyConditionExpression=Key('global_session_id').eq(global_session_id),
                ScanIndexForward=True
            )
            
            messages = []
            for item in response.get('Items', []):
                role = item.get('role')
                msg = item.get('message')
                
                if msg and msg.strip():
                    if role == 'user':
                        messages.append(HumanMessage(content=msg))
                    elif role == 'assistant':
                        messages.append(AIMessage(content=msg))
                else:
                    backend_logger.warning(f"get_chat_history | Skipping invalid message with empty content from role: {role} for global_session_id: {global_session_id}")
            
            if len(messages) > 0:
                success = True
                message = "Chat history found for the given global session id"
                result = True
                data = messages
                backend_logger.info(f"get_chat_history | {message}")
                break
            elif attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                success = True
                message = "Chat history not found for the given global session id"
                backend_logger.info(f"get_chat_history | {message}")
    except Exception as e:
        message = f"Error getting chat history: {str(e)}"
        backend_logger.error(f"get_chat_history | {message}")
    
    return success, message, result, data

# Function to retrieve active chat sessions for a user based on email and login session ID.
def get_active_chat_sessions(user_email: str, login_session_id: str) -> Tuple[bool, str, bool, List[Dict]]:
    success = False
    message = ""
    result = False
    data = []
    
    try:
        dynamodb = get_dynamodb_resource()
        chat_sessions_table = dynamodb.Table(DYNAMODB_CHAT_SESSIONS_TABLE_NAME)
        
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
            backend_logger.info(f"get_active_chat_sessions | {message}")
        else:
            success = True
            message = f"No active chat sessions found for user: {user_email}"
            backend_logger.info(f"get_active_chat_sessions | {message}")
    except ClientError as e:
        message = f"Error getting active chat sessions for user: {user_email}: {e}"
        backend_logger.error(f"get_active_chat_sessions | {message}")
    
    return success, message, result, data

# Function to retrieve chat history formatted specifically for the UI display.
def get_chat_history_for_ui(login_session_id: str, chat_session_id: str) -> Tuple[bool, str, bool, List[Dict]]:
    success = False
    message = ""
    result = False
    data = []

    if not login_session_id or not chat_session_id:
        message = "Login session id and chat session id are required"
        backend_logger.error(f"get_chat_history_for_ui | {message}")
        return success, message, result, data
    
    try:
        dynamodb = get_dynamodb_resource()
        chat_messages_table = dynamodb.Table(DYNAMODB_CHAT_MESSAGES_TABLE_NAME)
        
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
            backend_logger.info(f"get_chat_history_for_ui | {message}")
        else:
            success = True
            message = f"No chat history found for session {global_session_id}"
            backend_logger.info(f"get_chat_history_for_ui | {message}")
    except Exception as e:
        message = f"Error getting chat history: {str(e)}"
        backend_logger.error(f"get_chat_history_for_ui | {message}")
    
    return success, message, result, data

# Function to mark all active chat sessions for a user (based on login session) as inactive.
def end_all_chat_sessions(user_email: str, login_session_id: str) -> Tuple[bool, str]:
    success = False
    message = ""
    
    try:
        dynamodb = get_dynamodb_resource()
        chat_sessions_table = dynamodb.Table(DYNAMODB_CHAT_SESSIONS_TABLE_NAME)
        
        response = chat_sessions_table.query(
            IndexName='UserSessionsIndex',
            KeyConditionExpression=Key('user_email').eq(user_email),
            FilterExpression=Attr('login_session_id').eq(login_session_id) & Attr('session_status').eq('active')
        )
        
        if 'Items' not in response or len(response['Items']) == 0:
            success = True
            message = f"No active chat sessions found for user: {user_email}"
            backend_logger.info(f"end_all_chat_sessions | {message}")
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
            backend_logger.info(f"end_all_chat_sessions | Ended chat session with global_session_id={global_session_id}")
        
        success = True
        message = f"Ended all {len(response['Items'])} active chat sessions for user: {user_email}"
        backend_logger.info(f"end_all_chat_sessions | {message}")
    except Exception as e:
        message = f"Error ending all chat sessions for user: {user_email}: {e}"
        backend_logger.error(f"end_all_chat_sessions | {message}")
    
    return success, message

if __name__ == "__main__":
    pass